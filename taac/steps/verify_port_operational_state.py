# pyre-unsafe
import typing as t

from taac.constants import TestCaseFailure
from taac.steps.step import Step
from taac.utils.oss_taac_lib_utils import (
    async_retryable,
    none_throws,
)
from taac.test_as_a_config import types as taac_types


class VerifyPortOperationalStateStep(Step[taac_types.BaseInput]):
    """
    Step to verify the operational state of network interfaces.
    This step checks whether the specified interfaces are in the desired operational state
    (UP or DOWN). It supports specifying a global operational state or a per-interface state
    override via an operational state map.
    """

    STEP_NAME = taac_types.StepName.VERIFY_PORT_OPERATIONAL_STATE

    async def run(
        self,
        input: taac_types.BaseInput,
        params: t.Dict[str, t.Any],
    ) -> None:
        """
        Verify the operational state of the given interfaces.
        """
        interfaces: t.List[str] = params["interfaces"]
        operational_state: bool = params.get("operational_state")
        operational_state_map: t.Dict[str, bool] = params.get(
            "operational_state_map", {}
        )
        retries = params.get("retries", 5)
        sleep_time = params.get("sleep_time", 30)
        # pyre-fixme[12]: Expected an awaitable but got `AsyncF`.
        # pyre-fixme[19]: Expected 1 positional argument.
        await async_retryable(
            # pyre-fixme[6]: For 1st argument expected `Optional[int]` but got
            #  `(self: VerifyPortOperationalStateStep, interfaces: List[str],
            #  operational_state: Optional[bool], operational_state_map:
            #  Optional[Dict[str, bool]]) -> Coroutine[Any, Any, None]`.
            self.async_check_interfaces_operational_state,
            retries=retries,
            sleep_time=sleep_time,
            exceptions=(Exception,),
        )(interfaces, operational_state, operational_state_map)
        self.logger.info("All interfaces are in the desired operational state")

    async def async_check_interfaces_operational_state(
        self,
        interfaces: t.List[str],
        operational_state: t.Optional[bool],
        operational_state_map: t.Optional[t.Dict[str, bool]],
    ) -> None:
        operational_state_map = operational_state_map or {}
        actual_interface_state_map = await self.driver.async_get_interfaces_status(
            interfaces
        )
        missing_interfaces = [
            interface
            for interface in interfaces
            if interface not in actual_interface_state_map
        ]
        if missing_interfaces:
            raise TestCaseFailure(
                f"Failed to fetch operational state for interfaces not found: {missing_interfaces}"
            )
        mismatched_interface_state_map = {
            interface: actual_state
            for interface, actual_state in actual_interface_state_map.items()
            if actual_state
            != (operational_state_map.get(interface) or none_throws(operational_state))
        }
        if mismatched_interface_state_map:
            err_msg = f"Operational state mismatch for interfaces: {mismatched_interface_state_map}"
            self.logger.debug(err_msg)
            raise TestCaseFailure(err_msg)
