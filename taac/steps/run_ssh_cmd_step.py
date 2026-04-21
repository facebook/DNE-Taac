# (c) Meta Platforms, Inc. and affiliates. Confidential and proprietary.

# pyre-unsafe

import typing as t

from taac.steps.step import Step
from taac.test_as_a_config import types as taac_types


class RunSSHCmdStep(Step[taac_types.BaseInput]):
    STEP_NAME = taac_types.StepName.RUN_SSH_COMMAND_STEP

    async def run(
        self,
        input: taac_types.BaseInput,
        params: t.Dict[str, t.Any],
    ) -> None:
        cmd = params["cmd"]
        log_output = params.get("log_output", False)
        output = await self.driver.async_run_cmd_on_shell(cmd)
        if log_output and output:
            self.logger.info(f"Command output:\n{output}")
