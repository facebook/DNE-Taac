# (c) Meta Platforms, Inc. and affiliates. Confidential and proprietary.

# pyre-unsafe

import time
import typing as t

from taac.steps.step import Step
from taac.utils.common import run_in_thread
from taac.utils.system_stress_utils import (
    async_get_memory_current_pct,
)
from taac.test_as_a_config import types as taac_types


class AllocateCgroupSliceMemory(Step[taac_types.BaseInput]):
    STEP_NAME = taac_types.StepName.ALLOCATE_CGROUP_SLICE_MEMORY_STEP

    async def run(
        self,
        input: taac_types.BaseInput,
        params: t.Dict[str, t.Any],
    ) -> None:
        executable_path = params.get("executable_path", "/opt/memory_pressure")
        slice_name = params["slice_name"]
        keep_alive = params.get("keep_alive", False)
        initial_memory_allocation = params.get("initial_memory_allocation")
        ods_query_duration = params.get("ods_query_duration", 300)
        duration = params.get("duration", 300)
        minimum_memory_allocation = params.get("minimum_memory_allocation", 0)
        oom_score_adj = params.get("oom_score_adj", 0)

        # pyre-ignore
        if not await self.driver.async_check_if_file_exists(executable_path):
            raise Exception(
                f"Memory pressure script does not exist at {executable_path} on {self.hostname}"
            )

        end_time = int(time.time())
        start_time = end_time - ods_query_duration
        p90_memory_current = await async_get_memory_current_pct(
            self.hostname,
            slice_name,
            start_time,
            end_time,
        )  # In B

        # Calculate memory_to_allocate based on available parameters
        if params.get("total_memory_pct_decimal") is not None:
            # Old logic: use total memory percentage
            total_memory_pct = float(params["total_memory_pct_decimal"])
            memory_total = await self.driver.async_get_memory_total()  # pyre-ignore
            target_memory = total_memory_pct * memory_total  # In B
            self.driver.logger.info(
                f"Using total memory logic: total_memory_pct={total_memory_pct}, "
                f"memory_total={memory_total / (1024**3):.2f}GB, target_memory={target_memory / (1024**3):.2f}GB, "
                f"p90_memory_current={p90_memory_current / (1024**3):.2f}GB"
            )
            memory_to_allocate = max(
                int((target_memory - p90_memory_current) / 1024**2),
                minimum_memory_allocation,
            )
            self.driver.logger.info(
                f"Total memory logic result: memory_to_allocate={memory_to_allocate / (1024):.2f}GB"
            )
        elif params.get("workload_slice_based_total_memory_decimal") is not None:
            # New logic: use workload slice percentage
            workload_slice_based_total_memory_decimal = float(
                params["workload_slice_based_total_memory_decimal"]
            )
            workload_max_mem = (
                await self.driver.async_get_workload_slice_max_allocated_memory()
            )
            target_memory = (
                workload_max_mem / 0.75
            ) * workload_slice_based_total_memory_decimal
            self.driver.logger.info(
                f"Using workload slice logic: workload_slice_based_total_memory_decimal={workload_slice_based_total_memory_decimal}, "
                f"workload_max_mem={workload_max_mem / (1024**3):.2f}GB, target_memory={target_memory / (1024**3):.2f}GB, "
                f"p90_memory_current={p90_memory_current / (1024**3):.2f}GB"
            )
            memory_to_allocate = max(
                # Bytes to MB
                int((target_memory - p90_memory_current) / 1024**2),
                minimum_memory_allocation,
            )
            self.driver.logger.info(
                f"Workload slice logic result: memory_to_allocate={memory_to_allocate / (1024):.2f}GB"
            )
        else:
            raise ValueError(
                "Either 'total_memory_pct_decimal' or 'workload_slice_based_total_memory_decimal' must be provided"
            )
        if memory_to_allocate <= 0:
            self.driver.logger.info(
                f"No memory allocation needed, calculated value: {memory_to_allocate}"
            )
            return
        allocate_memory_cmds = [
            f"{executable_path}",
            "-c",
            f"{slice_name}.slice",
            "-m",
            memory_to_allocate,
            "-t",
            duration,
        ]
        if keep_alive:
            allocate_memory_cmds.append("-k")
        if initial_memory_allocation:
            allocate_memory_cmds.extend(["-i", initial_memory_allocation])
        if oom_score_adj:
            allocate_memory_cmds.extend(["-s", oom_score_adj])
        allocate_memory_cmds = [str(cmd) for cmd in allocate_memory_cmds]
        run_in_thread(
            self.driver.async_run_cmd_on_shell, cmd=" ".join(allocate_memory_cmds)
        )
