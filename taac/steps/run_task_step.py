# (c) Meta Platforms, Inc. and affiliates. Confidential and proprietary.

# pyre-unsafe

import typing as t

from taac.steps.step import Step
from taac.tasks.utils import run_task
from taac.utils.common import run_in_thread
from taac.test_as_a_config import types as taac_types


class RunTaskStep(Step[taac_types.RunTaskInput]):
    STEP_NAME = taac_types.StepName.RUN_TASK_STEP

    async def run(
        self,
        input: taac_types.RunTaskInput,
        params: t.Dict[str, t.Any],
    ) -> None:
        task = input.task
        dict_params = self.parameter_evaluator.evaluate(task.params)
        if input.blocking:
            await run_task(task, dict_params, self.ixia, self.logger)
        else:
            run_in_thread(run_task, task, dict_params, self.ixia, self.logger)
