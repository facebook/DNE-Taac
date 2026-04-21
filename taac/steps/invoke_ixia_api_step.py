# (c) Meta Platforms, Inc. and affiliates. Confidential and proprietary.

# pyre-unsafe

import json
import typing as t

from taac.steps.step import Step
from taac.utils.oss_taac_lib_utils import none_throws
from taac.test_as_a_config import types as taac_types


class InvokeIxiaApiStep(Step[taac_types.BaseInput]):
    STEP_NAME = taac_types.StepName.INVOKE_IXIA_API_STEP

    async def run(
        self,
        input: taac_types.BaseInput,
        params: t.Dict[str, t.Any],
    ) -> None:
        ixia = none_throws(self.ixia)
        api_name = params["api_name"]
        api_func = getattr(ixia, api_name)
        if not api_func:
            raise ValueError(f"Invalid ixia API name: {api_name}")
        args = json.loads(params.get("args_json", "{}"))
        assert isinstance(args, dict), (
            f"Invalid args_json: {args}: {type(args)}. Args must be a dict"
        )
        api_func(**args)
