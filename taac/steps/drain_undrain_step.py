# pyre-unsafe
import json
import typing as t

from taac.internal.drainer_utils import async_nds_drain
from taac.steps.step import Step
from taac.utils.json_thrift_utils import (
    try_json_loads,
    try_json_to_thrift,
)
from taac.test_as_a_config import types as taac_types


class DrainUndrainStep(Step[taac_types.DrainUndrainInput]):
    STEP_NAME = taac_types.StepName.DRAIN_UNDRAIN_STEP

    async def run(
        self,
        input: taac_types.DrainUndrainInput,
        params: t.Dict[str, t.Any],
    ) -> None:
        interfaces = params.get("interfaces", [])
        if interfaces:
            interfaces = [
                try_json_to_thrift(interface, taac_types.TestInterface)
                for interface in try_json_loads(interfaces)
            ]
            interfaces = [
                (
                    self.device.get_interface_by_name(interface)
                    if isinstance(interface, str)
                    else interface
                )
                for interface in interfaces
            ]
        interface_names = [interface.interface_name for interface in interfaces]
        if input.drain_handler == taac_types.DrainHandler.LOCAL_DRAINER:
            if input.drain:
                await self.driver.async_onbox_drain_device()
            else:
                await self.driver.async_onbox_undrain_device()
        elif input.drain_handler == taac_types.DrainHandler.NDS:
            await async_nds_drain(
                self.device.name,
                force_undrain=not input.drain,
                interfaces=interface_names,
            )
        else:
            raise
