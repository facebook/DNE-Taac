# pyre-unsafe
import asyncio
import typing as t

from taac.internal.driver.arista_switch import AristaSwitch
from taac.internal.driver.cisco_switch import CiscoSwitch
from taac.steps.step import Step
from taac.test_as_a_config import types as taac_types


class ModulePowerToggleStep(Step[taac_types.BaseInput]):
    STEP_NAME = taac_types.StepName.MODULE_POWER_TOGGLE_STEP

    async def run(
        self,
        input: taac_types.BaseInput,
        params: t.Dict[str, t.Any],
    ) -> None:
        """
        Enable or disable specified modules (fabric, linecard).
        params:
            modules: List[str]
            enable: bool - True to enable, False to disable
            sequential: bool - Whether to operate sequentially (default: False)
        """
        modules = params["modules"]
        enable = params["enable"]
        sequential = params.get("sequential", False)
        delay = params.get("delay", 5)
        try:
            await self.async_toggle_modules(modules, enable, sequential)
        except Exception as e:
            self.logger.error(f"Failed to toggle modules: {e}")
            raise e
        if delay:
            self.logger.info(f"Sleeping for {delay} seconds...")
            await asyncio.sleep(delay)

    async def async_toggle_modules(
        self,
        modules: t.List[str],
        enable: bool,
        sequential: bool,
    ) -> None:
        if isinstance(self.driver, AristaSwitch):
            driver = self.driver
        elif isinstance(self.driver, CiscoSwitch):
            driver = self.driver
        else:
            raise NotImplementedError(
                "Module power toggle only supported for Arista and Cisco switches"
            )

        coroutines = []
        for module in modules:
            if enable:
                coroutines.append(driver.enable_location(module))
            else:
                coroutines.append(driver.disable_location(module))

        if sequential:
            for coro in coroutines:
                await coro
        else:
            await asyncio.gather(*coroutines)

        action = "enabled" if enable else "disabled"
        self.logger.info(f"Successfully {action} modules: {modules}")
