# (c) Meta Platforms, Inc. and affiliates. Confidential and proprietary.

# pyre-unsafe

import typing as t

from taac.internal.coop_utils import async_unregister_patcher
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
