# (c) Meta Platforms, Inc. and affiliates. Confidential and proprietary.

# pyre-unsafe

import os
import typing as t

TAAC_OSS = os.environ.get("TAAC_OSS", "").lower() in ("1", "true", "yes")

if not TAAC_OSS:
    from taac.internal.coop_utils import async_unregister_patcher
else:
    # OSS stub - COOP (Config Orchestrator) is Meta-internal
    async def async_unregister_patcher(
        hostname: str,
        config_name: str,
        patcher_name: str,
    ) -> None:
        raise NotImplementedError(
            "COOP patcher unregistration is Meta-internal and not available in OSS mode"
        )

from taac.steps.step import Step
from taac.test_as_a_config import types as taac_types


class RegisterPatcherStep(Step[taac_types.RegisterPatcherInput]):
    STEP_NAME = taac_types.StepName.REGISTER_PATCHER_STEP
    OPERATING_SYSTEMS = ["FBOSS"]

    def __init__(
        self,
        *args,
        **kwargs,
    ) -> None:
        super(RegisterPatcherStep, self).__init__(*args, **kwargs)
        self.registered_patcher_name: t.Optional[str] = None

    async def run(
        self,
        input: taac_types.RegisterPatcherInput,
        params: t.Dict[str, t.Any],
    ) -> None:
        if input.register_patcher:
            # pyre-fixme[16]
            await self.driver.async_register_python_patcher(
                input.config_name,
                patcher_name=input.name,
                py_func_name=input.py_func_name,
                patcher_args=dict(input.kwargs) if input.kwargs else {},
                patcher_desc=input.description,
            )
            self.registered_patcher_name = input.name
        else:
            # pyre-fixme[16]
            await self.driver.async_unregister_python_patcher(
                config_name=input.config_name,
                patcher_name=input.name,
            )

    async def cleanUp(
        self, input: taac_types.RegisterPatcherInput, params: t.Dict[str, t.Any]
    ) -> None:
        if self.registered_patcher_name:
            await async_unregister_patcher(
                self.hostname,
                input.config_name,
                self.registered_patcher_name,
            )
