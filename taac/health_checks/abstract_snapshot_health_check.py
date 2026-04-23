# (c) Meta Platforms, Inc. and affiliates. Confidential and proprietary.

# pyre-unsafe
import typing as t
from abc import ABC

from taac.constants import TestDevice, TestTopology
from taac.health_checks.common_utils import (
    async_get_everpaste_fburl_if_needed,
)
from taac.health_checks.constants import Snapshot
from taac.utils.driver_factory import async_get_device_driver
from taac.utils.oss_taac_lib_utils import (
    async_retryable,
    ConsoleFileLogger,
)
from taac.health_check.health_check import types as hc_types


HealthCheckIn = t.TypeVar("HealthCheckIn", bound=t.Any)
Object = t.TypeVar("Object", bound=t.Any)


class AbstractSnapshotHealthCheck(t.Generic[HealthCheckIn, Object], ABC):
    CHECK_NAME: hc_types.CheckName = hc_types.CheckName.UNDEFINED
    CHECK_SCOPE = hc_types.Scope.DEFAULT
    DEFAULT_PRIORITY = hc_types.DEFAULT_HC_PRIORITY

    def __init__(
        self,
        obj: Object,
        input: HealthCheckIn,
        pre_snapshot_checkpoint_id: str,
        post_snapshot_checkpoint_id: str,
        check_params: t.Dict[str, t.Any],
        logger: ConsoleFileLogger,
    ):
        if self.__class__.CHECK_NAME is hc_types.CheckName.UNDEFINED:
            raise ValueError(
                f"{self.__class__.__name__} must have a valid CHECK_NAME defined"
            )
        self._input = input
        self._check_params = check_params
        self._obj = obj
        self._pre_snapshot_checkpoint_id = pre_snapshot_checkpoint_id
        self._post_snapshot_checkpoint_id = post_snapshot_checkpoint_id
        self.logger = logger

        self._pre_snapshot: Snapshot = ...
        self._post_snapshot: Snapshot = ...
        self._should_skip = False

    async def setup(self, obj: Object) -> None:
        pass

    @async_retryable(retries=3, exceptions=(Exception,))  # pyre-ignore[56]
    async def _capture_pre_snapshot(
        self,
        obj: Object,
        input: HealthCheckIn,
        check_params: t.Dict[str, t.Any],
        timestamp: int,
    ) -> Snapshot:
        try:
            if self._should_skip:
                return Snapshot(timestamp=0)
            return await self.capture_pre_snapshot(obj, input, check_params, timestamp)
        except Exception as e:
            self.logger.info(
                f"Error occured while capturing pre snapshot for {self.__class__.CHECK_NAME}: {e}"
            )
            raise e

    async def capture_pre_snapshot(
        self,
        obj: Object,
        input: HealthCheckIn,
        check_params: t.Dict[str, t.Any],
        timestamp: int,
    ) -> Snapshot:
        return Snapshot(timestamp=timestamp)

    @async_retryable(retries=3, exceptions=(Exception,))  # pyre-ignore[56]
    async def _capture_post_snapshot(
        self,
        obj: Object,
        input: HealthCheckIn,
        check_params: t.Dict[str, t.Any],
        timestamp: int,
    ) -> Snapshot:
        try:
            if self._should_skip:
                return Snapshot(timestamp=0)
            return await self.capture_post_snapshot(obj, input, check_params, timestamp)
        except Exception as e:
            self.logger.info(
                f"Error occured while capturing post snapshot for {self.__class__.CHECK_NAME}: {e}"
            )
            raise e

    async def capture_post_snapshot(
        self,
        obj: Object,
        input: HealthCheckIn,
        check_params: t.Dict[str, t.Any],
        timestamp: int,
    ) -> Snapshot:
        return Snapshot(timestamp=timestamp)

    @async_retryable(retries=3, exceptions=(Exception,))  # pyre-ignore[56]
    async def _compare_snapshots(
        self,
        obj: Object,
        input: HealthCheckIn,
        check_params: t.Dict[str, t.Any],
        pre_snapshot: Snapshot,
        post_snapshot: Snapshot,
    ) -> hc_types.HealthCheckResult:
        try:
            if self._should_skip:
                return hc_types.HealthCheckResult(
                    status=hc_types.HealthCheckStatus.SKIP,
                )
            check_result = await self.compare_snapshots(
                obj, input, check_params, pre_snapshot, post_snapshot
            )
            check_result = check_result(
                message=await async_get_everpaste_fburl_if_needed(check_result.message),
                name=self.__class__.CHECK_NAME,
            )
            return check_result
        except Exception as e:
            self.logger.info(
                f"Error occured while comparing pre and post snapshots for {self.__class__.CHECK_NAME}: {e}"
            )
            raise e

    async def compare_snapshots(
        self,
        obj: Object,
        input: HealthCheckIn,
        check_params: t.Dict[str, t.Any],
        pre_snapshot: Snapshot,
        post_snapshot: Snapshot,
    ) -> hc_types.HealthCheckResult:
        raise NotImplementedError


class AbstractDeviceSnapshotHealthCheck(
    AbstractSnapshotHealthCheck[HealthCheckIn, TestDevice], ABC
):
    OPERATING_SYSTEMS = ["FBOSS", "EOS"]

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.driver = ...

    async def setup(self, obj: Object) -> None:
        if obj.attributes.operating_system in self.__class__.OPERATING_SYSTEMS:
            self.driver = await async_get_device_driver(obj.name)
        else:
            self._should_skip = True
        await super().setup(obj)


class AbstractTopologySnapshotHealthCheck(
    AbstractSnapshotHealthCheck[HealthCheckIn, TestTopology], ABC
):
    pass
