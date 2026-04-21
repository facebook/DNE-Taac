# pyre-unsafe
import asyncio
import time
import typing as t

from taac.steps.step import Step
from taac.test_as_a_config import types as taac_types


class LongevityStep(Step[taac_types.BaseInput]):
    STEP_NAME = taac_types.StepName.LONGEVITY_STEP

    async def run(
        self,
        input: taac_types.BaseInput,
        params: t.Dict[str, t.Any],
    ):
        duration = params["duration"]
        self.logger.info(f"Sleeping for {duration} seconds...")
        start_time = time.time()
        seconds_passed = 0
        while seconds_passed < duration:
            sleep_time = min(60, duration - seconds_passed)
            await asyncio.sleep(sleep_time)
            seconds_passed = int(time.time() - start_time)
            seconds_remaining = max(0, duration - seconds_passed)
            self.logger.info(
                f"{seconds_passed} seconds have passed, {seconds_remaining} seconds remaining"
            )
        end_time = time.time()
        self.logger.info(f"Slept for {end_time - start_time:.2f} seconds.")
