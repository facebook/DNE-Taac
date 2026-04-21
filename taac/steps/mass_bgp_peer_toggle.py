# (c) Meta Platforms, Inc. and affiliates. Confidential and proprietary.

# pyre-unsafe

import asyncio
import time
import typing as t

from taac.steps.step import Step
from taac.utils.oss_taac_lib_utils import none_throws
from taac.test_as_a_config import types as taac_types

SLEEP_TIME_AFTER_STABLIZING_S = 120


class MassBgpPeerToggle(Step[taac_types.BaseInput]):
    STEP_NAME = taac_types.StepName.MASS_BGP_PEER_TOGGLE

    async def run(
        self,
        input: taac_types.BaseInput,
        params: t.Dict[str, t.Any],
    ) -> None:
        ixia = none_throws(self.ixia)
        # Step 1: Stop the Flapping
        device_group_name_regex = params["device_group_name_regex"]
        toggle_time_interval_s = int(params["toggle_time_interval_s"])
        total_step_time_hours = int(params["total_step_time_hours"])
        is_enable = False  # initializing state
        start_time = time.time()
        while True:
            ixia.toggle_device_groups(
                enable=is_enable, device_group_name_regex=device_group_name_regex
            )
            mode_str = "enable" if is_enable else "disable"
            ixia.logger.info(
                f"Waiting {toggle_time_interval_s}s before flipping rogue device groups to {mode_str}"
            )
            await asyncio.sleep(toggle_time_interval_s)
            is_enable = not is_enable
            # Check if total step time has exceeded
            elapsed_time = time.time() - start_time
            if elapsed_time >= total_step_time_hours * 3600:
                break
        # Set device_groups to enable
        ixia.toggle_device_groups(
            enable=True, device_group_name_regex=device_group_name_regex
        )
        ixia.logger.info(
            f"Waiting for the {SLEEP_TIME_AFTER_STABLIZING_S}s after enabling device groups"
        )
        await asyncio.sleep(SLEEP_TIME_AFTER_STABLIZING_S)
