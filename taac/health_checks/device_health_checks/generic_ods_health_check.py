# (c) Meta Platforms, Inc. and affiliates. Confidential and proprietary.

# pyre-unsafe
import asyncio
import time
import typing as t

from taac.constants import TestDevice
from taac.health_checks.abstract_health_check import (
    AbstractDeviceHealthCheck,
)
from taac.health_checks.constants import (
    DAILY_TABLE_TRANSFORM_DESC,
)
from taac.internal.ods_utils import (
    async_generate_ods_url,
    async_query_ods,
)
from taac.utils.common import eval_jq
from pyre_extensions import JSON
from taac.health_check.health_check import types as hc_types


def dict(ods_data) -> JSON:
    dict_data = {}
    for hostname, time_series in ods_data.items():
        dict_data[hostname] = {}
        for timestamp, value in time_series.items():
            dict_data[hostname][str(timestamp)] = value
    return dict_data


class GenericOdsHealthCheck(AbstractDeviceHealthCheck[hc_types.BaseHealthCheckIn]):
    CHECK_NAME = hc_types.CheckName.GENERIC_ODS_CHECK
    LOG_TO_SCUBA = True

    async def _run(
        self,
        obj: TestDevice,
        input: hc_types.BaseHealthCheckIn,
        check_params: t.Dict[str, t.Any],
    ) -> hc_types.HealthCheckResult:
        key_desc = check_params["key_desc"]
        min_ods_query_duration = int(check_params.get("min_ods_query_duration", 120))
        start_time = int(check_params.get("start_time", time.time()))
        # wait x seconds before checking ods data
        sleep_timer = check_params.get("sleep_timer", 120)
        if sleep_timer > 0:
            await asyncio.sleep(sleep_timer)
        end_time = int(time.time())
        if end_time - start_time < min_ods_query_duration:
            start_time = end_time - min_ods_query_duration
        transform_desc = check_params.get("transform_desc", DAILY_TABLE_TRANSFORM_DESC)
        reduce_desc = check_params.get("reduce_desc", "")
        validation_expr = check_params.get("validation_expr")
        custom_jq_expr = check_params.get("custom_jq_expr")
        assert validation_expr or custom_jq_expr
        ods_data = await async_query_ods(
            entity_desc=obj.name,
            key_desc=key_desc,
            reduce_desc=reduce_desc,
            transform_desc=transform_desc,
            start_time=int(start_time),
            end_time=int(end_time),
        )
        if not ods_data:
            ods_query_url = await async_generate_ods_url(
                entity_desc=obj.name,
                key_desc=key_desc,
                start_time=int(start_time),
                end_time=int(end_time),
            )
            msg = f"ODS query returned no data: {ods_query_url}"
            self.logger.debug(msg)
            return hc_types.HealthCheckResult(
                status=hc_types.HealthCheckStatus.SKIP,
                message=msg,
            )
        ods_data = ods_data.get(obj.name, {})
        ods_data_dict = dict(ods_data)
        violations = []
        if validation_expr:
            jq_expr = f". | .[] | to_entries | map(select(.value {validation_expr} | not)) | from_entries"
            violation_data = eval_jq(jq_expr, ods_data_dict)  # pyre-ignore
            if violation_data:
                for timestamp, value in violation_data.items():
                    log_message = (
                        f"Validation Error: {key_desc} at {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(timestamp)))} "
                        f"failed validation check '{validation_expr}' with value: {value}"
                    )
                    self.logger.debug(log_message)
                    violations.append(log_message)
        elif custom_jq_expr:
            violation_data = eval_jq(custom_jq_expr, ods_data_dict)  # pyre-ignore
            if violation_data:
                log_message = f"Custom Validation Error: Data '{violation_data}' failed custom JQ expression '{custom_jq_expr}'"
                self.logger.debug(log_message)
                violations.append(log_message)

        if violations:
            return hc_types.HealthCheckResult(
                status=hc_types.HealthCheckStatus.FAIL,
                message=f"Validation checks failed: {violations}",
            )
        return hc_types.HealthCheckResult(
            status=hc_types.HealthCheckStatus.PASS,
        )
