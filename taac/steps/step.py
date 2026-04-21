# pyre-unsafe
import time
import typing as t
from abc import ABC, abstractmethod


# TestbedError defined locally for OSS compatibility
class TestbedError(Exception):
    pass


from taac.constants import (
    TestCaseFailure,
    TestDevice,
    TestResult,
    TestTopology,
)
from taac.driver.abstract_switch import AbstractSwitch
from taac.ixia.taac_ixia import TaacIxia
from taac.libs.parameter_evaluator import ParameterEvaluator
from taac.utils.common import (
    async_everpaste_if_needed,
    async_everpaste_str,
    async_get_fburl,
    async_write_test_result,
)
from taac.utils.driver_factory import async_get_device_driver
from taac.utils.json_thrift_utils import thrift_to_json
from taac.utils.oss_taac_lib_utils import (
    ConsoleFileLogger,
    get_root_logger,
)
from taac.utils.taac_log_formatter import (
    format_duration,
    log_step_info,
)
from taac.health_check.health_check import types as hc_types
from taac.test_as_a_config import types as taac_types


StepInput = t.TypeVar("StepInput", bound=t.Any)


class Step(t.Generic[StepInput], ABC):
    STEP_NAME: taac_types.StepName = taac_types.StepName.UNDEFINED
    IXIA_REQUIRED: bool = False

    def __init_subclass__(cls, **kwargs):
        if cls.STEP_NAME == taac_types.StepName.UNDEFINED:
            raise ValueError(f"Step {cls.__name__} does not have a valid step name")

    def __init__(
        self,
        name: str,
        device: TestDevice,
        topology: TestTopology,
        test_case_results: t.List[TestResult],
        test_config: taac_types.TestConfig,
        test_case_name: str,
        test_case_start_time: float,
        parameter_evaluator: ParameterEvaluator,
        step: taac_types.Step,
        ixia: t.Optional[TaacIxia] = None,
        logger: t.Optional[ConsoleFileLogger] = None,
    ) -> None:
        self.name = name
        self.device = device
        self.ixia = ixia
        self.test_case_results = test_case_results
        self.test_case_name = test_case_name
        self.test_case_start_time = test_case_start_time
        self.test_config = test_config
        self.step = step

        self.topology: TestTopology = topology
        self.hostname: str = self.device.name
        self.logger = logger or get_root_logger()
        self.parameter_evaluator = parameter_evaluator
        self.driver: AbstractSwitch = ...
        self.failures = []

        # to be initialized in TaacRunner
        self._input: StepInput = ...
        self._step_params: t.Dict[str, t.Any] = ...
        self._initialize_and_run_step_callable: t.Callable = ...

    async def _run(self, input: StepInput, params: t.Dict[str, t.Any]) -> None:
        step_start_time = time.time()
        try:
            if self.ixia:
                self.ixia.start_traffic()
            log_step_info(
                self.__class__.STEP_NAME.name,
                self.device.name,
                action="setUp",
                logger=self.logger,
            )
            self.logger.debug(
                await async_everpaste_if_needed(
                    f"Step input: {input} | params: {params}", 100
                )
            )
            await self.setUp(input, params)
            log_step_info(
                self.__class__.STEP_NAME.name,
                self.device.name,
                action="Running",
                logger=self.logger,
            )
            await self.run(input, params)
        except TestbedError as e:
            self.logger.error(f"Testbed is not clean: {str(e)}")
            raise e
        except TestCaseFailure as e:
            raise e
        except Exception as e:
            failure_reason = (
                f"Step {self.__class__.__name__} failed on {self.device.name}: {str(e)}"
            )
            test_result = await async_write_test_result(
                self.test_case_name,
                devices=[self.device],
                test_status=hc_types.HealthCheckStatus.FAIL,
                start_time=self.test_case_start_time,
                message=(
                    await async_get_fburl(await async_everpaste_str(failure_reason))
                    if len(failure_reason) > 100
                    else failure_reason
                ),
            )
            self.test_case_results.append(test_result)
            self.logger.error(failure_reason)
            raise e
        finally:
            step_end_time = time.time()
            step_duration = step_end_time - step_start_time
            log_step_info(
                self.__class__.STEP_NAME.name,
                self.device.name,
                action=f"Done ({format_duration(step_duration)})",
                logger=self.logger,
            )

    @abstractmethod
    async def run(self, input: StepInput, params: t.Dict[str, t.Any]) -> None:
        pass

    async def setUp(self, input: StepInput, params: t.Dict[str, t.Any]) -> None:
        self.driver = await async_get_device_driver(self.hostname)

    async def cleanUp(self, input: StepInput, params: t.Dict[str, t.Any]) -> None:
        # Executed at the end of the Stage
        pass

    @property
    def is_fboss(self) -> bool:
        return self.device.attributes.operating_system == "FBOSS"

    @property
    def is_eos(self) -> bool:
        return self.device.attributes.operating_system == "EOS"

    async def run_steps(
        self,
        steps: t.List[taac_types.Step],
        concurrent: bool = False,
        device: t.Optional[TestDevice] = None,
    ) -> None:
        # Note: concurrent parameter is reserved for future use or handled at stage level
        # _initialize_and_run_step_callable only accepts device, not concurrent
        await self._initialize_and_run_step_callable(
            steps,
            device or self.device,
            self.test_case_name,
            self.test_case_start_time,
            self.test_case_results,
        )

    async def run_step(
        self,
        step_name: taac_types.StepName,
        input_json: t.Optional[str] = None,
        params: t.Optional[taac_types.Params] = None,
        id: t.Optional[str] = None,
    ) -> None:
        step = taac_types.Step(
            name=step_name,
            input_json=input_json,
            step_params=params,
            id=id,
        )
        await self.run_steps([step])

    async def run_health_checks(
        self,
        health_checks: t.List[
            t.Union[hc_types.CheckName, taac_types.PointInTimeHealthCheck]
        ],
        stage: taac_types.ValidationStage = taac_types.ValidationStage.MID_TEST,
    ) -> None:
        point_in_time_health_checks = []
        for check in health_checks:
            if isinstance(check, hc_types.CheckName):
                point_in_time_health_checks.append(
                    taac_types.PointInTimeHealthCheck(
                        name=check,
                    )
                )
            else:
                point_in_time_health_checks.append(check)
        await self.run_steps(
            [
                taac_types.Step(
                    name=taac_types.StepName.VALIDATION_STEP,
                    input_json=thrift_to_json(
                        taac_types.ValidationInput(
                            point_in_time_checks=point_in_time_health_checks,
                            stage=stage,
                        )
                    ),
                )
            ],
            device=self.device,  # Explicitly pass device context to prevent it from being lost
        )

    def add_failure(self, failure: str) -> None:
        self.failures.append(failure)

    def raise_failure_if_exists(self) -> None:
        if self.failures:
            raise TestCaseFailure(
                f"Test case failed with the following failures: {'\n'.join(self.failures)}"
            )
