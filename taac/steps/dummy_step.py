# (c) Meta Platforms, Inc. and affiliates. Confidential and proprietary.

# pyre-unsafe

import typing as t

from taac.steps.step import Step
from taac.test_as_a_config import types as taac_types


class DummyStep(Step[taac_types.BaseInput]):
    STEP_NAME = taac_types.StepName.DUMMY_STEP

    async def run(
        self,
        input: taac_types.BaseInput,
        params: t.Dict[str, t.Any],
    ) -> None:
        self.logger.info("Executing dummy step")
