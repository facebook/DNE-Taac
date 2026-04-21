# (c) Meta Platforms, Inc. and affiliates. Confidential and proprietary.

# pyre-unsafe

import typing as t
from collections import defaultdict

from neteng.fboss.bgp_thrift.types import TBgpPeerState
from taac.constants import TestDevice
from taac.health_checks.abstract_health_check import (
    AbstractDeviceHealthCheck,
)
from taac.health_check.health_check import types as hc_types


class BgpSessionEstablishedHealthCheck(
    AbstractDeviceHealthCheck[hc_types.BaseHealthCheckIn]
):
    CHECK_NAME = hc_types.CheckName.BGP_SESSION_ESTABLISH_CHECK
    OPERATING_SYSTEMS = [
        "FBOSS",
        "EOS",
    ]
    # DEFAULT_PRIORITY = hc_types.DEFAULT_HC_PRIORITY

    async def _run(
        self,
        obj: TestDevice,
        input: hc_types.BaseHealthCheckIn,  # Required by the AbstractDeviceHealthCheck interface
        check_params: t.Dict[str, t.Any],
    ) -> hc_types.HealthCheckResult:
        """
        Run a health check to verify BGP session count matches expectation.

        Args:
            obj: Test device
            input: Base health check input
            check_params: Dictionary containing:
                - expected_established_session_count: Expected number of established BGP sessions (optional, defaults to "all established")
                - ignore_prefixes: Optional list of prefixes to ignore
                - ignore_all_prefixes_except: Optional list of prefixes to exclusively check
                  (only sessions with these prefixes will be checked, all others will be ignored)
                - verbose: Optional boolean to enable verbose output (defaults to False)

        Returns:
            HealthCheckResult: Result of the health check
        """
        hostname = obj.name

        ignore_prefixes = check_params.get("ignore_prefixes", [])
        ignore_all_prefixes_except = check_params.get("ignore_all_prefixes_except", [])
        verbose = check_params.get("verbose", False)
        expected_established_session_count = check_params.get(
            "expected_established_session_count"
        )

        if expected_established_session_count is not None:
            try:
                expected_established_session_count = int(
                    expected_established_session_count
                )
                self.logger.info(
                    f"Expected_established_session_count = {expected_established_session_count}"
                )
            except (ValueError, TypeError):
                self.logger.warning(
                    f"Invalid expected_established_session_count value: {expected_established_session_count}, ignoring"
                )
                expected_established_session_count = None

        self.logger.info(f"Running BGP session health check on {hostname}")

        # Get all BGP sessions
        bgp_sessions = await self.driver.async_get_bgp_sessions()

        # Handle case where no BGP sessions are configured at all
        if not bgp_sessions:
            # If we expected 0 established sessions and there are no sessions at all, that's a pass
            if expected_established_session_count == 0:
                return hc_types.HealthCheckResult(
                    status=hc_types.HealthCheckStatus.PASS,
                    message=f"No BGP sessions configured on {hostname} - matches expected 0 established sessions",
                )
            # If we expected some established sessions but there are no sessions at all, that's a fail
            elif (
                expected_established_session_count is not None
                and expected_established_session_count > 0
            ):
                return hc_types.HealthCheckResult(
                    status=hc_types.HealthCheckStatus.FAIL,
                    message=f"No BGP sessions configured on {hostname}, but expected {expected_established_session_count} established sessions",
                )
            # If no expectation was set and there are no sessions, that's also a fail
            else:
                return hc_types.HealthCheckResult(
                    status=hc_types.HealthCheckStatus.FAIL,
                    message=f"No BGP sessions found on {hostname}",
                )

        # Count sessions by state
        session_states = defaultdict(int)
        non_established_sessions = []

        for session in bgp_sessions:
            # Skip sessions with ignored prefixes
            if ignore_prefixes and any(
                session.peer_addr.startswith(prefix) for prefix in ignore_prefixes
            ):
                continue

            # If ignore_all_prefixes_except is specified, only check sessions with these prefixes
            if ignore_all_prefixes_except and not any(
                session.peer_addr == prefix for prefix in ignore_all_prefixes_except
            ):
                continue

            session_states[session.peer.peer_state] += 1

            if session.peer.peer_state != TBgpPeerState.ESTABLISHED:
                non_established_sessions.append(
                    {
                        "peer_addr": session.peer_addr,
                        "my_addr": session.my_addr,
                        "state": str(session.peer.peer_state),
                        "uptime": session.uptime,
                        "asn": session.peer.remote_as,
                    }
                )

        total_sessions = sum(session_states.values())
        established_sessions = session_states.get(TBgpPeerState.ESTABLISHED, 0)

        self.logger.info(f"Total BGP sessions: {total_sessions}")
        self.logger.info(f"Established BGP sessions: {established_sessions}")

        # Print session state counts
        for state, count in session_states.items():
            self.logger.info(f"Sessions in {state} state: {count}")

        # Print details of non-established sessions if verbose
        if verbose and non_established_sessions:
            self.logger.info("Non-established BGP sessions:")
            for session in non_established_sessions:
                self.logger.info(
                    f"  Peer: {session['peer_addr']} (ASN: {session['asn']})"
                )
                self.logger.info(f"  Local: {session['my_addr']}")
                self.logger.info(f"  State: {session['state']}")
                self.logger.info(f"  Uptime: {session['uptime']} seconds")
                self.logger.info("  ---")

        # Format non-established session details for failure messages
        non_established_details = [
            f"{s['peer_addr']} (state={s['state']}, ASN={s['asn']})"
            for s in non_established_sessions
        ]

        # Generalized logic: If expected count is provided, use simple comparison
        if expected_established_session_count is not None:
            if established_sessions == expected_established_session_count:
                return hc_types.HealthCheckResult(
                    status=hc_types.HealthCheckStatus.PASS,
                    message=f"BGP session count matches expected: {established_sessions} established sessions on {hostname}",
                )
            else:
                return hc_types.HealthCheckResult(
                    status=hc_types.HealthCheckStatus.FAIL,
                    message=f"BGP session count mismatch on {hostname}: expected {expected_established_session_count} established sessions, found {established_sessions}. "
                    f"Total sessions: {total_sessions}. "
                    f"Non-established: {non_established_details}",
                )
        else:
            # Backward compatibility: Original behavior when no expected count is provided
            if non_established_sessions:
                return hc_types.HealthCheckResult(
                    status=hc_types.HealthCheckStatus.FAIL,
                    message=f"Found {len(non_established_sessions)} BGP sessions that are not established on {hostname}. "
                    f"Total sessions: {total_sessions}, Established sessions: {established_sessions}. "
                    f"Non-established: {non_established_details}",
                )

            self.logger.info(
                f"All {total_sessions} BGP sessions are established on {hostname}"
            )
            return hc_types.HealthCheckResult(
                status=hc_types.HealthCheckStatus.PASS,
                message=f"All {total_sessions} BGP sessions are established on {hostname}",
            )

    async def _run_arista(
        self,
        obj: TestDevice,
        input: hc_types.BaseHealthCheckIn,
        check_params: t.Dict[str, t.Any],
    ) -> hc_types.HealthCheckResult:
        """
        Verify BGP sessions on ar-bgp (native EOS BGP) devices via EOS CLI.

        ar-bgp devices have no BGP++ thrift API, so async_get_bgp_sessions()
        is not available. Instead, uses 'show bgp ipv6 unicast summary | json'
        and 'show bgp ipv4 unicast summary | json' to get peer states.

        Args:
            obj: Test device
            input: Base health check input
            check_params: Dictionary containing:
                - expected_established_session_count: Expected established sessions (optional)
                - address_family: "ipv4", "ipv6", or "both" (optional, defaults to "both")
        """
        hostname = obj.name
        expected_established_session_count = check_params.get(
            "expected_established_session_count"
        )
        address_family = check_params.get("address_family", "both")

        if expected_established_session_count is not None:
            try:
                expected_established_session_count = int(
                    expected_established_session_count
                )
            except (ValueError, TypeError):
                expected_established_session_count = None

        self.logger.info(
            f"Running ar-bgp session health check on {hostname} via EOS CLI"
        )

        try:
            all_peers = {}
            bgp_inactive = False

            # Query IPv6 BGP summary
            if address_family in ("ipv6", "both"):
                try:
                    v6_result = await self.driver.async_execute_show_json_on_shell(
                        "show bgp ipv6 unicast summary | json"
                    )
                    v6_peers = (
                        v6_result.get("vrfs", {}).get("default", {}).get("peers", {})
                    )
                    for peer_ip, peer_info in v6_peers.items():
                        all_peers[f"v6:{peer_ip}"] = peer_info
                except Exception as e:
                    if "BGP inactive" in str(e):
                        bgp_inactive = True
                    self.logger.warning(
                        f"Failed to get IPv6 BGP summary on {hostname}: {e}"
                    )

            # Query IPv4 BGP summary
            if address_family in ("ipv4", "both"):
                try:
                    v4_result = await self.driver.async_execute_show_json_on_shell(
                        "show bgp ipv4 unicast summary | json"
                    )
                    v4_peers = (
                        v4_result.get("vrfs", {}).get("default", {}).get("peers", {})
                    )
                    for peer_ip, peer_info in v4_peers.items():
                        all_peers[f"v4:{peer_ip}"] = peer_info
                except Exception as e:
                    if "BGP inactive" in str(e):
                        bgp_inactive = True
                    self.logger.warning(
                        f"Failed to get IPv4 BGP summary on {hostname}: {e}"
                    )

            # If native EOS BGP is inactive, this is likely an ARISTA_FBOSS device
            # running BGP++ instead of native EOS BGP. Fall back to the Thrift-based
            # check which queries BGP++ sessions directly.
            if bgp_inactive and not all_peers:
                self.logger.info(
                    f"Native EOS BGP is inactive on {hostname}, "
                    f"falling back to BGP++ Thrift-based session check"
                )
                return await self._run(obj, input, check_params)

            if not all_peers:
                if expected_established_session_count == 0:
                    return hc_types.HealthCheckResult(
                        status=hc_types.HealthCheckStatus.PASS,
                        message=f"No BGP peers found on {hostname} — matches expected 0",
                    )
                return hc_types.HealthCheckResult(
                    status=hc_types.HealthCheckStatus.FAIL,
                    message=f"No BGP peers found on {hostname} via EOS CLI",
                )

            established = 0
            non_established = []
            for peer_key, peer_info in all_peers.items():
                state = peer_info.get("peerState", "Unknown")
                if state == "Established":
                    established += 1
                else:
                    non_established.append(
                        f"{peer_key} (state={state}, asn={peer_info.get('asn', '?')})"
                    )

            total = len(all_peers)
            self.logger.info(
                f"ar-bgp sessions on {hostname}: {established}/{total} Established"
            )

            if expected_established_session_count is not None:
                if established == expected_established_session_count:
                    return hc_types.HealthCheckResult(
                        status=hc_types.HealthCheckStatus.PASS,
                        message=(
                            f"ar-bgp session count matches on {hostname}: "
                            f"{established} established"
                        ),
                    )
                return hc_types.HealthCheckResult(
                    status=hc_types.HealthCheckStatus.FAIL,
                    message=(
                        f"ar-bgp session count mismatch on {hostname}: "
                        f"expected {expected_established_session_count}, "
                        f"found {established}/{total}. "
                        f"Non-established: {non_established}"
                    ),
                )

            if non_established:
                return hc_types.HealthCheckResult(
                    status=hc_types.HealthCheckStatus.FAIL,
                    message=(
                        f"{len(non_established)} ar-bgp sessions not established "
                        f"on {hostname}: {non_established}"
                    ),
                )

            return hc_types.HealthCheckResult(
                status=hc_types.HealthCheckStatus.PASS,
                message=(f"All {total} ar-bgp sessions established on {hostname}"),
            )

        except Exception as e:
            return hc_types.HealthCheckResult(
                status=hc_types.HealthCheckStatus.ERROR,
                message=f"Error checking ar-bgp sessions on {hostname}: {e}",
            )
