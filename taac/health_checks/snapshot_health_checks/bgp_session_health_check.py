# (c) Meta Platforms, Inc. and affiliates. Confidential and proprietary.

# pyre-unsafe

import typing as t
from collections import namedtuple

from neteng.fboss.bgp_thrift.types import TBgpPeerState, TBgpSession
from taac.constants import TestDevice
from taac.health_checks.abstract_snapshot_health_check import (
    AbstractDeviceSnapshotHealthCheck,
)
from taac.health_checks.constants import Snapshot
from taac.utils.health_check_utils import is_parent_prefix
from taac.health_check.health_check import types as hc_types


BgpSessionId = namedtuple(
    "BgpSessionId", ["my_addr", "peer_addr", "peer_session_state"], defaults=(None,)
)


class BgpSessionHealthCheck(
    AbstractDeviceSnapshotHealthCheck[hc_types.BaseHealthCheckIn],
):
    CHECK_NAME = hc_types.CheckName.BGP_SESSION_CHECK
    OPERATING_SYSTEMS = [
        "FBOSS",
        "EOS",
    ]
    DEFAULT_PRIORITY = hc_types.DEFAULT_HC_PRIORITY

    async def capture_pre_snapshot(
        self,
        obj: TestDevice,
        input: hc_types.BaseHealthCheckIn,
        check_params: t.Dict[str, t.Any],
        timestamp: int,
    ) -> Snapshot:
        parent_prefixes_to_ignore = check_params.get("parent_prefixes_to_ignore", [])
        bgp_sessions = await self.async_get_bgp_sessions(parent_prefixes_to_ignore)
        return Snapshot(data=bgp_sessions, timestamp=timestamp)

    async def capture_post_snapshot(
        self,
        obj: TestDevice,
        input: hc_types.BaseHealthCheckIn,
        check_params: t.Dict[str, t.Any],
        timestamp: int,
    ) -> Snapshot:
        parent_prefixes_to_ignore = check_params.get("parent_prefixes_to_ignore", [])
        bgp_sessions = await self.async_get_bgp_sessions(parent_prefixes_to_ignore)
        return Snapshot(data=bgp_sessions, timestamp=timestamp)

    async def compare_snapshots(
        self,
        obj: TestDevice,
        input: hc_types.BaseHealthCheckIn,
        check_params: t.Dict[str, t.Any],
        pre_snapshot: Snapshot,
        post_snapshot: Snapshot,
    ) -> hc_types.HealthCheckResult:
        skip_flap_check = check_params.get("skip_flap_check")
        skip_uptime_check = check_params.get("skip_uptime_check")
        pre_snapshot_bgp_sessions = pre_snapshot.data
        post_snapshot_bgp_sessions = post_snapshot.data
        deleted_bgp_sessions = list(
            set(pre_snapshot_bgp_sessions.keys())
            - set(post_snapshot_bgp_sessions.keys())
        )
        if deleted_bgp_sessions:
            return hc_types.HealthCheckResult(
                status=hc_types.HealthCheckStatus.FAIL,
                message=(
                    f"Bgp sessions with the following local_addr and peer_addr are "
                    f"not present in post snapshot: {deleted_bgp_sessions}"
                ),
            )

        issues = []

        if not skip_flap_check:
            flapped_bgp_sessions = []
            for key in post_snapshot_bgp_sessions.keys():
                pre_snapshot_bgp_session = pre_snapshot_bgp_sessions.get(key)
                post_snapshot_bgp_session = post_snapshot_bgp_sessions[key]
                if not pre_snapshot_bgp_session:
                    continue
                if (
                    pre_snapshot_bgp_session.details
                    and post_snapshot_bgp_session.details
                ):
                    if (
                        post_snapshot_bgp_session.details.num_of_flaps
                        > pre_snapshot_bgp_session.details.num_of_flaps
                    ):
                        flapped_bgp_sessions.append(key)
                        self.logger.debug(
                            f"The number of flaps increased from {pre_snapshot_bgp_session.details.num_of_flaps} "
                            f"to {post_snapshot_bgp_session.details.num_of_flaps} for {key}"
                        )
                else:
                    if (
                        post_snapshot_bgp_session.uptime
                        < pre_snapshot_bgp_session.uptime
                    ):
                        flapped_bgp_sessions.append(key)
                        self.logger.debug(
                            f"The uptime for {key} decreased from {pre_snapshot_bgp_session.uptime} to "
                            f"{post_snapshot_bgp_session.uptime}. This indicates a flap"
                        )
            if flapped_bgp_sessions:
                flapped_sessions_str = "\n    • ".join(
                    [
                        self._format_session_id(session)
                        for session in flapped_bgp_sessions
                    ]
                )
                issues.append(f"Flapped BGP sessions:\n    • {flapped_sessions_str}")

        # Enhanced uptime consistency check (ported from BGP Peer route check)
        uptime_issues = []
        if not skip_uptime_check:
            for key in post_snapshot_bgp_sessions.keys():
                pre_snapshot_bgp_session = pre_snapshot_bgp_sessions.get(key)
                post_snapshot_bgp_session = post_snapshot_bgp_sessions[key]
                if not pre_snapshot_bgp_session:
                    continue

                session_uptime_issues = self._check_uptime_consistency(
                    key,
                    pre_snapshot_bgp_session,
                    post_snapshot_bgp_session,
                    pre_snapshot.timestamp,
                    post_snapshot.timestamp,
                )
                uptime_issues.extend(session_uptime_issues)

        if uptime_issues:
            uptime_issues_str = "\n    • ".join(uptime_issues)
            issues.append(f"BGP session uptime issues:\n    • {uptime_issues_str}")

        if issues:
            formatted_message = "BGP session issues detected:\n\n" + "\n\n".join(issues)
            return hc_types.HealthCheckResult(
                status=hc_types.HealthCheckStatus.FAIL,
                message=formatted_message,
            )

        return hc_types.HealthCheckResult(
            status=hc_types.HealthCheckStatus.PASS,
        )

    async def async_get_bgp_sessions(
        self,
        parent_prefixes_to_ignore: t.List[str],
    ) -> t.Dict[BgpSessionId, TBgpSession]:
        """
        Retrieves BGP sessions from the driver and maps them to a dictionary.
        Args:
            hostname (str): The hostname of the device.
            rogue_bgp_peer_parent_prefix (Optional[str]): The parent prefix of the rogue BGP peer.
        Returns:
            A dictionary mapping BgpSessionId to TBgpSession.
        """
        bgp_sessions = await self.driver.async_get_bgp_sessions()
        bgp_sessions_map: t.Dict[BgpSessionId, TBgpSession] = {}
        for bgp_session in bgp_sessions:
            if parent_prefixes_to_ignore:
                should_ignore_prefix = any(
                    is_parent_prefix(bgp_session.peer_addr, parent_prefix)
                    for parent_prefix in parent_prefixes_to_ignore
                )
                if should_ignore_prefix:
                    continue
            if bgp_session.peer.peer_state != TBgpPeerState.ESTABLISHED:
                continue
            session_id = BgpSessionId(
                my_addr=bgp_session.my_addr,
                peer_addr=bgp_session.peer_addr,
                peer_session_state=bgp_session.peer.peer_state,
            )
            bgp_sessions_map[session_id] = bgp_session
        return bgp_sessions_map

    def _format_session_id(self, session_id: BgpSessionId) -> str:
        return f"{session_id.my_addr} (local_addr) → {session_id.peer_addr} (peer_addr)"

    def _check_uptime_consistency(
        self,
        session_key: BgpSessionId,
        pre_session: TBgpSession,
        post_session: TBgpSession,
        pre_timestamp: int,
        post_timestamp: int,
    ) -> t.List[str]:
        """
        Check uptime consistency between pre and post snapshots.
        Ported from BGP Peer route check for enhanced uptime validation.
        Returns list of issues found.
        """
        issues = []

        # Convert uptime from milliseconds to seconds
        pre_uptime_seconds = pre_session.uptime // 1000 if pre_session.uptime else 0
        post_uptime_seconds = post_session.uptime // 1000 if post_session.uptime else 0

        # Calculate time elapsed between snapshots (in seconds)
        time_elapsed = post_timestamp - pre_timestamp

        # Calculate expected post uptime
        expected_post_uptime = pre_uptime_seconds + time_elapsed
        actual_post_uptime = post_uptime_seconds

        # Tolerance for timing differences (10 seconds)
        UPTIME_TOLERANCE = 10

        session_str = self._format_session_id(session_key)

        # Check for BGP session restart
        # If actual uptime is significantly less than time elapsed, session likely restarted
        if actual_post_uptime < time_elapsed:
            issues.append(
                f"{session_str}: Session restarted (uptime: {actual_post_uptime}s, expected: >{time_elapsed}s)"
            )
        else:
            # Check for significant uptime discrepancy
            uptime_diff = abs(actual_post_uptime - expected_post_uptime)
            if uptime_diff > UPTIME_TOLERANCE:
                issues.append(
                    f"{session_str}: Uptime discrepancy (actual: {actual_post_uptime}s, "
                    f"expected: ~{expected_post_uptime}s, diff: {uptime_diff}s)"
                )

        return issues
