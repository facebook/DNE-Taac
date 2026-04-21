# (c) Meta Platforms, Inc. and affiliates. Confidential and proprietary.

# pyre-unsafe
import traceback
import typing as t
from abc import ABC, abstractmethod

from neteng.test_infra.dne.taac.constants import TestDevice, TestTopology
from taac.health_checks.common_utils import (
    async_get_everpaste_fburl_if_needed,
)
from neteng.test_infra.dne.taac.ixia.taac_ixia import TaacIxia as Ixia
from taac.utils.common import is_overridden
from taac.utils.driver_factory import async_get_device_driver
from taac.utils.oss_taac_lib_utils import ConsoleFileLogger
from taac.utils.taac_log_formatter import log_health_check_info
from taac.health_check.health_check import types as hc_types


HealthCheckIn = t.TypeVar("HealthCheckIn", bound=t.Any)
Object = t.TypeVar("Object", bound=t.Any)


class AbstractPointInTimeHealthCheck(t.Generic[HealthCheckIn, Object], ABC):
    CHECK_NAME: hc_types.CheckName = hc_types.CheckName.UNDEFINED
    CHECK_SCOPE = hc_types.Scope.DEFAULT
    DEFAULT_PRIORITY = hc_types.DEFAULT_HC_PRIORITY

    def __init__(self, logger: ConsoleFileLogger, ixia: t.Optional[Ixia] = None):
        if self.__class__.CHECK_NAME is hc_types.CheckName.UNDEFINED:
            raise ValueError(
                f"{self.__class__.__name__} must have a valid CHECK_NAME defined"
            )
        self.logger = logger
        self.ixia = ixia

    async def run_wrapper(
        self,
        obj: Object,
        input: t.Optional[HealthCheckIn],
        default_input: HealthCheckIn,
        check_params: t.Dict[str, t.Any],
    ) -> hc_types.HealthCheckResult:
        # Override this method to add custom logic before running the health check
        return await self.run(obj, input, default_input, check_params)

    async def run(
        self,
        obj: Object,
        input: t.Optional[HealthCheckIn],
        default_input: HealthCheckIn,
        check_params: t.Dict[str, t.Any],
        custom_run_fn: t.Optional[t.Callable] = None,
    ) -> hc_types.HealthCheckResult:
        try:
            should_skip_check, reason = await self.should_skip_check(obj)
            if should_skip_check:
                self.logger.info(
                    f"Skipping health check {self.__class__.CHECK_NAME} for the reason {reason}"
                )
                return hc_types.HealthCheckResult(
                    status=hc_types.HealthCheckStatus.SKIP,
                    message=reason,
                )
            input = input or self._default_input(obj) or default_input
            self.logger.info(f"Running health check: {self.__class__.__name__}")
            self.logger.debug(f"Health check input: {input}")
            run_fn = custom_run_fn or self._run
            check_result = await run_fn(obj, input, check_params)
            check_result = check_result(
                message=await async_get_everpaste_fburl_if_needed(check_result.message)
            )
            log_health_check_info(
                self.__class__.__name__,
                check_result.status.name,
                logger=self.logger,
            )
            return check_result(
                name=self.__class__.CHECK_NAME,
            )
        except Exception as e:
            err_msg = f"Exception occurred while running {self.__class__.__name__}: {e}\n {traceback.format_tb(e.__traceback__)}"
            self.logger.error(err_msg)
            return hc_types.HealthCheckResult(
                name=self.__class__.CHECK_NAME,
                status=hc_types.HealthCheckStatus.ERROR,
                message=await async_get_everpaste_fburl_if_needed(err_msg),
            )

    @abstractmethod
    async def _run(
        self,
        obj: Object,
        input: HealthCheckIn,
        check_params: t.Dict[str, t.Any],
    ) -> hc_types.HealthCheckResult:
        raise NotImplementedError

    def default_input(self, obj: Object) -> t.Optional[HealthCheckIn]:
        try:
            return self.default_input(obj)
        except Exception as ex:
            self.logger.error(
                f"Failed to get default input for {self.__class__.__name__}: {ex}"
            )
            return None

    def _default_input(self, obj: Object) -> t.Optional[HealthCheckIn]:
        return None

    async def should_skip_check(self, obj: Object) -> t.Tuple[bool, str | None]:
        return False, None


class AbstractIxiaHealthCheck(AbstractPointInTimeHealthCheck[HealthCheckIn, Ixia], ABC):
    pass


OPERATING_SYSTEM_TO_FN_NAME = {
    "FBOSS": "_run_fboss",
    "EOS": "_run_arista",
    "IOSXR": "_run_cisco",
}


class AbstractDeviceHealthCheck(
    AbstractPointInTimeHealthCheck[HealthCheckIn, TestDevice], ABC
):
    OPERATING_SYSTEMS = ["FBOSS", "EOS"]
    LOG_TO_SCUBA: bool = False
    CHECK_SCOPE = hc_types.Scope.TOPOLOGY

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.driver = ...
        self.data_to_log = {}

    async def run_wrapper(
        self,
        obj: Object,
        input: t.Optional[HealthCheckIn],
        default_input: HealthCheckIn,
        check_params: t.Dict[str, t.Any],
    ) -> hc_types.HealthCheckResult:
        os = obj.attributes.operating_system
        if os in self.__class__.OPERATING_SYSTEMS:
            self.driver = await async_get_device_driver(obj.name)
            fn_name = OPERATING_SYSTEM_TO_FN_NAME[os]
            is_fn_overridden = is_overridden(
                self.__class__, AbstractDeviceHealthCheck, fn_name
            )
            custom_run_fn = getattr(self, fn_name, None) if is_fn_overridden else None
            return await self.run(
                obj, input, default_input, check_params, custom_run_fn
            )

        return hc_types.HealthCheckResult(
            name=self.__class__.CHECK_NAME,
            status=hc_types.HealthCheckStatus.SKIP,
        )

    def add_data_to_log(self, json_serializable_dict: t.Dict) -> None:
        self.data_to_log.update(json_serializable_dict)

    async def _run_arista(
        self,
        obj: Object,
        input: HealthCheckIn,
        check_params: t.Dict[str, t.Any],
    ) -> hc_types.HealthCheckResult:
        raise NotImplementedError

    async def _run_fboss(
        self,
        obj: Object,
        input: HealthCheckIn,
        check_params: t.Dict[str, t.Any],
    ) -> hc_types.HealthCheckResult:
        raise NotImplementedError

    async def _run_cisco(
        self,
        obj: Object,
        input: HealthCheckIn,
        check_params: t.Dict[str, t.Any],
    ) -> hc_types.HealthCheckResult:
        raise NotImplementedError


class AbstractTopologyHealthCheck(
    AbstractPointInTimeHealthCheck[HealthCheckIn, TestTopology], ABC
):
    pass
