# pyre-unsafe
import json

from ixia.ixia import types as ixia_types
from taac.constants import Gigabyte
from taac.step_definitions import (
    create_longevity_step,
    create_prefix_flap_step,
    create_service_convergence_step,
    create_service_interruption_step,
    create_validation_step,
)
from taac.task_definitions import (
    create_configure_parallel_bgp_peers_task,
    create_coop_apply_patchers_task,
    create_coop_register_patcher_task,
    create_coop_unregister_patchers_task,
    create_wait_for_agent_convergence_task,
)
from taac.utils.json_thrift_utils import thrift_to_json
from taac.health_check.health_check import types as hc_types
from taac.test_as_a_config import types as taac_types
from taac.test_as_a_config.types import (
    Params,
    Playbook,
    PointInTimeHealthCheck,
    SnapshotHealthCheck,
    Stage,
    TestConfig,
)

# ============================================================================
# Constants
# ============================================================================

STABLE_TAG = "STABLE"
FLAPPING_TAG = "FLAPPING"

# Durations (seconds) — production values
SETUP_WAIT_S = 300
FLAP_PHASE_DURATION_S = 300  # 5 minutes per flap phase
CONVERGENCE_WAIT_S = 180  # 3 minutes for agent restart convergence

# Iteration count
ROUNDS = 2
AGENT_RESTARTS_PER_ROUND = 2

# Flap timing ranges (seconds) — re-randomized every RERANDOMIZE_INTERVAL_S
FLAP_UPTIME_RANGE = (10, 30)
FLAP_DOWNTIME_RANGE = (10, 30)
RERANDOMIZE_INTERVAL_S = 60

# ECMP capacity defaults
DEFAULT_MAX_ECMP_MEMBER_COUNT = 16000


# ============================================================================
# Health Check Helpers
# ============================================================================


def _get_packet_loss_check(device_name):
    """IXIA packet loss check targeting STABLE group traffic items."""
    return PointInTimeHealthCheck(
        name=hc_types.CheckName.IXIA_PACKET_LOSS_CHECK,
        input_json=thrift_to_json(
            hc_types.IxiaPacketLossHealthCheckIn(
                thresholds=[
                    hc_types.PacketLossThreshold(
                        names=[
                            f"{device_name.upper()}_V6_TRAFFIC",
                            f"{device_name.upper()}_V4_TRAFFIC",
                        ],
                        str_value="0.1",
                        expect_packet_loss=False,
                    ),
                ]
            )
        ),
    )


def _get_ecmp_check(ecmp_member_count, ecmp_group_count):
    """ECMP group and member count check with custom thresholds."""
    return PointInTimeHealthCheck(
        name=hc_types.CheckName.ECMP_GROUP_AND_MEMBER_COUNT_CHECK,
        check_params=Params(
            json_params=json.dumps(
                {
                    "ecmp_member_count": ecmp_member_count,
                    "ecmp_group_count": ecmp_group_count,
                }
            ),
        ),
    )


def _get_common_checks(device_name, ecmp_member_count, ecmp_group_count):
    """Return reusable health check objects.

    Args:
        device_name: Device hostname for packet loss check naming.
        ecmp_member_count: Max ECMP member count threshold.
        ecmp_group_count: Max ECMP group count threshold.
    """
    packet_loss_check = _get_packet_loss_check(device_name)

    ecmp_check = _get_ecmp_check(ecmp_member_count, ecmp_group_count)

    memory_check = PointInTimeHealthCheck(
        name=hc_types.CheckName.MEMORY_UTILIZATION_CHECK,
        check_params=Params(
            jq_params={
                "start_time": ".test_case_start_time",
            },
            json_params=json.dumps(
                {
                    "threshold": Gigabyte.GIG_5.value,
                    "threshold_by_service": {
                        "bgpd": Gigabyte.GIG_10.value,
                        "fsdb": Gigabyte.GIG_5.value,
                        "fboss_sw_agent": Gigabyte.GIG_9.value,
                        "fboss_hw_agent@0": Gigabyte.GIG_8.value,
                    },
                }
            ),
        ),
    )

    cpu_check = PointInTimeHealthCheck(
        name=hc_types.CheckName.CPU_UTILIZATION_CHECK,
        check_params=Params(
            jq_params={
                "start_time": ".test_case_start_time",
            },
            json_params=json.dumps(
                {
                    "threshold": 400.0,
                }
            ),
        ),
    )

    bgp_session_check = PointInTimeHealthCheck(
        name=hc_types.CheckName.BGP_SESSION_ESTABLISH_CHECK,
    )

    bgp_session_snapshot = SnapshotHealthCheck(
        name=hc_types.CheckName.BGP_SESSION_CHECK,
    )

    return (
        packet_loss_check,
        ecmp_check,
        memory_check,
        cpu_check,
        bgp_session_check,
        bgp_session_snapshot,
    )


# ============================================================================
# Cleanup Steps
# ============================================================================


def _get_cleanup_steps():
    """Steps to disable all prefix flaps."""
    return [
        create_prefix_flap_step(
            enable=False,
            is_all_groups=True,
            duration_s=60,
        ),
    ]


# ============================================================================
# Playbook 1: Setup — validate baseline with wide ECMP groups
# ============================================================================


def get_setup_playbook(device_name, ecmp_member_count, ecmp_group_count):
    """Playbook 1: Validate baseline with all peers established.

    Waits for all STABLE and FLAPPING peers to establish, then validates
    packet loss, ECMP group/member counts, CPU, memory, and BGP sessions.
    """
    (
        packet_loss_check,
        ecmp_check,
        memory_check,
        cpu_check,
        bgp_session_check,
        bgp_session_snapshot,
    ) = _get_common_checks(device_name, ecmp_member_count, ecmp_group_count)

    return Playbook(
        name="test_setup_stable_state",
        postchecks=[
            packet_loss_check,
            ecmp_check,
            memory_check,
            cpu_check,
            bgp_session_check,
        ],
        snapshot_checks=[
            bgp_session_snapshot,
        ],
        skip_test_config_postchecks=True,
        cleanup_steps=_get_cleanup_steps(),
        stages=[
            Stage(
                id="setup_stable_state",
                steps=[
                    create_longevity_step(
                        duration=SETUP_WAIT_S,
                        description="Wait for all peers to establish and ECMP groups to form",
                    ),
                    create_validation_step(
                        point_in_time_checks=[
                            packet_loss_check,
                            ecmp_check,
                        ],
                        description="Validate baseline: packet loss and ECMP width",
                    ),
                ],
            ),
        ],
    )


# ============================================================================
# Playbook 2: Wide ECMP stress — prefix flaps + agent restarts
# ============================================================================


def get_wide_ecmp_stress_playbook(device_name, ecmp_member_count, ecmp_group_count):
    """Playbook 2: Stress test with prefix flaps and agent restarts.

    Each round:
    1. Enable prefix flaps on FLAPPING group, wait FLAP_PHASE_DURATION_S
    2. Disable prefix flaps
    3. Restart AGENT, wait for convergence
    4. Enable prefix flaps on FLAPPING group, wait FLAP_PHASE_DURATION_S
    5. Disable prefix flaps
    6. Restart AGENT, wait for convergence
    7. Enable prefix flaps on FLAPPING group, wait FLAP_PHASE_DURATION_S
    8. Disable prefix flaps, wait for final convergence

    Post-checks validate packet loss, ECMP counts, CPU, memory, BGP sessions.
    """
    (
        packet_loss_check,
        ecmp_check,
        memory_check,
        cpu_check,
        bgp_session_check,
        _bgp_session_snapshot,
    ) = _get_common_checks(device_name, ecmp_member_count, ecmp_group_count)

    # Build the steps for one round
    round_steps = []

    for i in range(3):  # 3 flap phases per round
        # Enable prefix flaps on FLAPPING group
        round_steps.append(
            create_prefix_flap_step(
                enable=True,
                tag_names=[FLAPPING_TAG],
                duration_s=FLAP_PHASE_DURATION_S,
                uptime_range=FLAP_UPTIME_RANGE,
                downtime_range=FLAP_DOWNTIME_RANGE,
                rerandomize_interval_s=RERANDOMIZE_INTERVAL_S,
                description=f"Flap phase {i + 1}: enable prefix flaps on FLAPPING group",
            ),
        )

        # Disable prefix flaps
        round_steps.append(
            create_prefix_flap_step(
                enable=False,
                is_all_groups=True,
                duration_s=60,
                description=f"Flap phase {i + 1}: disable prefix flaps",
            ),
        )

        if i < AGENT_RESTARTS_PER_ROUND:
            # Agent restart + convergence wait
            round_steps.append(
                create_service_interruption_step(
                    service=taac_types.Service.AGENT,
                    trigger=taac_types.ServiceInterruptionTrigger.SYSTEMCTL_RESTART,
                    description=f"Agent restart {i + 1} after flap phase {i + 1}",
                ),
            )
            round_steps.append(
                create_service_convergence_step(
                    services=[taac_types.Service.AGENT],
                    description=f"Wait for agent convergence after restart {i + 1}",
                ),
            )
            round_steps.append(
                create_longevity_step(
                    duration=CONVERGENCE_WAIT_S,
                    description=f"Convergence wait after agent restart {i + 1}",
                ),
            )
        else:
            # Final flap phase — just wait for convergence
            round_steps.append(
                create_longevity_step(
                    duration=CONVERGENCE_WAIT_S,
                    description="Final convergence wait after last flap phase",
                ),
            )

    # Post-round validation
    round_steps.append(
        create_validation_step(
            point_in_time_checks=[
                packet_loss_check,
                ecmp_check,
                memory_check,
                cpu_check,
                bgp_session_check,
            ],
            description="Validate health after stress round",
        ),
    )

    return Playbook(
        name="test_wide_ecmp_stress",
        postchecks=[
            packet_loss_check,
            ecmp_check,
            memory_check,
            cpu_check,
            bgp_session_check,
        ],
        snapshot_checks=[],
        skip_test_config_postchecks=True,
        cleanup_steps=_get_cleanup_steps(),
        stages=[
            Stage(
                id="wide_ecmp_stress_round",
                iteration=ROUNDS,
                steps=round_steps,
            ),
        ],
    )


# ============================================================================
# Playbook 3: Core dump and unclean exit checks
# ============================================================================


def get_dump_unclean_exit_playbook(device_name, ecmp_member_count, ecmp_group_count):
    """Playbook 3: Verify no core dumps or unclean exits occurred.

    Runs after all disruptive playbooks to confirm that no service
    crashed unexpectedly (core dumps) and no unclean exits were
    recorded during the entire test window.
    """
    (
        packet_loss_check,
        _ecmp_check,
        memory_check,
        cpu_check,
        bgp_session_check,
        _bgp_session_snapshot,
    ) = _get_common_checks(device_name, ecmp_member_count, ecmp_group_count)

    core_dump_snapshot = SnapshotHealthCheck(
        name=hc_types.CheckName.CORE_DUMPS_CHECK,
    )

    unclean_exit_check = PointInTimeHealthCheck(
        name=hc_types.CheckName.UNCLEAN_EXIT_CHECK,
        check_params=Params(
            jq_params={
                "start_time": ".test_case_start_time",
            },
        ),
    )

    return Playbook(
        name="test_dump_unclean_exit",
        postchecks=[
            unclean_exit_check,
            packet_loss_check,
            bgp_session_check,
        ],
        snapshot_checks=[
            core_dump_snapshot,
        ],
        skip_test_config_postchecks=True,
        cleanup_steps=_get_cleanup_steps(),
        stages=[
            Stage(
                id="dump_unclean_exit_validation",
                steps=[
                    create_longevity_step(
                        duration=SETUP_WAIT_S,
                        description="Wait for BGP sessions to stabilize",
                    ),
                    create_validation_step(
                        point_in_time_checks=[
                            unclean_exit_check,
                            bgp_session_check,
                        ],
                        description="Validate no unclean exits",
                    ),
                ],
            ),
        ],
    )


# ============================================================================
# Main TestConfig Constructor
# ============================================================================


def test_config_wide_ecmp(
    test_config_name,
    device_name,
    local_mac_address,
    ixia_uplink_interface,
    ixia_downlink_interface,
    # BGP peering
    peergroup_uplink_mimic_v6,
    peergroup_uplink_mimic_v4,
    peergroup_downlink_mimic_v6,
    peergroup_downlink_mimic_v4,
    route_map_uplink_ingress,
    route_map_uplink_egress,
    route_map_downlink_ingress,
    route_map_downlink_egress,
    uplink_peer_tag,
    downlink_peer_tag,
    # IP addressing
    ixia_uplink_ic_parent_network_v6,
    ixia_uplink_ic_parent_network_v4,
    ixia_downlink_ic_parent_network_v6,
    ixia_downlink_ic_parent_network_v4,
    # AS numbers
    remote_uplink_as_4byte,
    remote_downlink_as_4byte,
    is_uplink_peer_confed,
    is_downlink_peer_confed,
    # Communities, pool
    ixia_uplink_communities,
    ixia_downlink_communities,
    basset_pool,
    # ECMP parameters
    max_ecmp_width_per_group,
    max_ecmp_member_count=DEFAULT_MAX_ECMP_MEMBER_COUNT,
    # Prefix address space
    v6_uplink_prefix="6000",
    v4_uplink_prefix="102",
    v6_downlink_prefix="3000",
    v4_downlink_prefix="101",
    # Peer route limits
    per_peer_max_route_limit="25000",
):
    # ---- ECMP capacity math ----
    # ecmp_width = number of peers per direction (uplink or downlink)
    ecmp_width = int(max_ecmp_width_per_group * 0.98)
    # The DUT sees 4 independent prefix sets (uplink v6, uplink v4,
    # downlink v6, downlink v4), each creating prefix_count ECMP groups
    # with ecmp_width members. We size prefix_count so total members
    # across all 4 sets fill ~98% of the ECMP member table.
    num_prefix_sets = 4  # v6+v4 × uplink+downlink
    prefix_count = int(max_ecmp_member_count * 0.98) // (ecmp_width * num_prefix_sets)

    # Split peers into STABLE (always up) and FLAPPING (toggled during stress)
    stable_peer_count = ecmp_width // 2
    flapping_peer_count = ecmp_width - stable_peer_count
    total_peer_count = ecmp_width  # per direction (stable + flapping)

    # ECMP thresholds for health checks — allow the full table
    ecmp_member_threshold = max_ecmp_member_count
    ecmp_group_threshold = prefix_count * num_prefix_sets + 100

    # Compute IXIA flapping group address offsets.
    # STABLE peers occupy the first stable_peer_count * 2 addresses.
    # V6: stable starts at ::11/::10, flapping starts after stable.
    v6_flapping_ixia_start = 0x11 + stable_peer_count * 2
    v6_flapping_gw_start = 0x10 + stable_peer_count * 2
    # V4: stable starts at .1/.0, flapping starts after stable.
    v4_flapping_ixia_start = 1 + stable_peer_count * 2
    v4_flapping_gw_start = stable_peer_count * 2

    # Flapping device groups start their AS at base + stable_peer_count
    uplink_flapping_as = remote_uplink_as_4byte + stable_peer_count
    downlink_flapping_as = remote_downlink_as_4byte + stable_peer_count

    playbooks = [
        get_setup_playbook(device_name, ecmp_member_threshold, ecmp_group_threshold),
        get_wide_ecmp_stress_playbook(
            device_name, ecmp_member_threshold, ecmp_group_threshold
        ),
        get_dump_unclean_exit_playbook(
            device_name, ecmp_member_threshold, ecmp_group_threshold
        ),
    ]

    # Helper to create route scales for a device group.
    # All groups (STABLE and FLAPPING) advertise the SAME prefix set
    # so the DUT sees all peers as nexthops for the same destinations,
    # creating wide ECMP groups.
    def _v6_route_scale(direction_prefix, communities):
        return taac_types.RouteScaleSpec(
            network_group_index=0,
            v6_route_scale=taac_types.RouteScale(
                multiplier=1,
                prefix_count=prefix_count,
                prefix_length=64,
                starting_prefixes=f"{direction_prefix}:1::",
                prefix_step="0:0:0:0::0",
                bgp_communities=communities,
                ip_address_family=ixia_types.IpAddressFamily.IPV6,
            ),
        )

    def _v4_route_scale(direction_prefix, communities):
        return taac_types.RouteScaleSpec(
            network_group_index=0,
            v4_route_scale=taac_types.RouteScale(
                multiplier=1,
                prefix_count=prefix_count,
                prefix_length=24,
                starting_prefixes=f"{direction_prefix}.1.0.0",
                prefix_step="0.0.0.0",
                bgp_communities=communities,
                ip_address_family=ixia_types.IpAddressFamily.IPV4,
            ),
        )

    return TestConfig(
        name=test_config_name,
        ixia_protocol_verification_timeout=300,
        skip_ixia_protocol_verification=True,
        basset_pool=basset_pool,
        endpoints=[
            taac_types.Endpoint(
                name=device_name,
                ixia_ports=[
                    ixia_uplink_interface,
                    ixia_downlink_interface,
                ],
                dut=True,
                mac_address=local_mac_address,
            ),
        ],
        setup_tasks=[
            # ---- Step 1: Clean slate ----
            create_coop_unregister_patchers_task(device_name),
            create_coop_apply_patchers_task(
                hostnames=[device_name],
            ),
            create_wait_for_agent_convergence_task([device_name]),
            # ---- Step 2: Remove existing BGP peers ----
            create_coop_register_patcher_task(
                hostname=device_name,
                config_name="bgpcpp",
                patcher_name="a_remove_bgp_peers",
                task_name="coop_register_patcher",
                patcher_args={"delete_all": "True"},
                py_func_name="remove_bgp_peers",
            ),
            # ---- Step 3: Enable IXIA ports ----
            create_coop_register_patcher_task(
                hostname=device_name,
                config_name="agent",
                patcher_name="enable_port_all_ixia_ports",
                task_name="coop_register_patcher",
                patcher_args={
                    f"{ixia_uplink_interface}": "enable",
                    f"{ixia_downlink_interface}": "enable",
                },
                py_func_name="change_port_admin_state",
            ),
            # ---- Step 4: Update existing V6 peer groups ----
            create_coop_register_patcher_task(
                hostname=device_name,
                config_name="bgpcpp",
                patcher_name="update_peer_group_patcher_V6_Downlink",
                task_name="coop_register_patcher",
                patcher_args={
                    "name": peergroup_downlink_mimic_v6,
                    "attributes_to_update_json": json.dumps(
                        {
                            "disable_ipv4_afi": "True",
                            "v4_over_v6_nexthop": "False",
                            "is_passive": "False",
                            "is_confed_peer": is_downlink_peer_confed,
                            "max_routes": per_peer_max_route_limit,
                        }
                    ),
                },
                py_func_name="configure_bgp_peer_group",
            ),
            create_coop_register_patcher_task(
                hostname=device_name,
                config_name="bgpcpp",
                patcher_name=f"update_peer_group_patcher_{peergroup_uplink_mimic_v6}_Uplink",
                task_name="coop_register_patcher",
                patcher_args={
                    "name": peergroup_uplink_mimic_v6,
                    "attributes_to_update_json": json.dumps(
                        {
                            "disable_ipv4_afi": "True",
                            "v4_over_v6_nexthop": "False",
                            "is_passive": "False",
                            "is_confed_peer": is_uplink_peer_confed,
                            "max_routes": per_peer_max_route_limit,
                        }
                    ),
                },
                py_func_name="configure_bgp_peer_group",
            ),
            # ---- Step 5: Create V4 peer groups ----
            create_coop_register_patcher_task(
                hostname=device_name,
                config_name="bgpcpp",
                patcher_name=f"add_peer_group_patcher_{peergroup_uplink_mimic_v4}",
                task_name="coop_register_patcher",
                patcher_args={
                    "name": peergroup_uplink_mimic_v4,
                    "description": "BGP peering from SSW to FSW, IPv4 sessions",
                    "next_hop_self": "True",
                    "disable_ipv4_afi": "False",
                    "disable_ipv6_afi": "True",
                    "is_confed_peer": is_uplink_peer_confed,
                    "peer_tag": uplink_peer_tag,
                    "ingress_policy_name": route_map_uplink_ingress,
                    "egress_policy_name": route_map_uplink_egress,
                    "bgp_peer_timers_hold_time_seconds": "30",
                    "bgp_peer_timers_keep_alive_seconds": "10",
                    "bgp_peer_timers_out_delay_seconds": "7",
                    "bgp_peer_timers_withdraw_unprog_delay_seconds": "0",
                    "max_routes": per_peer_max_route_limit,
                    "warning_only": "True",
                    "warning_limit": "0",
                    "link_bandwidth_bps": "auto",
                    "v4_over_v6_nexthop": "False",
                    "is_passive": "False",
                },
                py_func_name="add_peer_group_patcher",
            ),
            create_coop_register_patcher_task(
                hostname=device_name,
                config_name="bgpcpp",
                patcher_name=f"add_peer_group_patcher_{peergroup_downlink_mimic_v4}",
                task_name="coop_register_patcher",
                patcher_args={
                    "name": peergroup_downlink_mimic_v4,
                    "description": "BGP peering from RSW to FSW, IPv4 sessions",
                    "next_hop_self": "True",
                    "disable_ipv4_afi": "False",
                    "disable_ipv6_afi": "True",
                    "is_confed_peer": is_downlink_peer_confed,
                    "ingress_policy_name": route_map_downlink_ingress,
                    "egress_policy_name": route_map_downlink_egress,
                    "bgp_peer_timers_hold_time_seconds": "30",
                    "bgp_peer_timers_keep_alive_seconds": "10",
                    "bgp_peer_timers_out_delay_seconds": "7",
                    "bgp_peer_timers_withdraw_unprog_delay_seconds": "0",
                    "peer_tag": downlink_peer_tag,
                    "max_routes": per_peer_max_route_limit,
                    "warning_only": "True",
                    "warning_limit": "0",
                    "link_bandwidth_bps": "auto",
                    "v4_over_v6_nexthop": "False",
                    "is_passive": "False",
                },
                py_func_name="add_peer_group_patcher",
            ),
            # ---- Step 6: Configure DUT VLANs and BGP peers ----
            # Uplink: Configure DUT-side VLANs and BGP peers.
            create_configure_parallel_bgp_peers_task(
                hostname=device_name,
                configure_vlans_patcher_name="configure_vlans_patcher_uplink",
                add_bgp_peers_patcher_name="add_bgp_peers_patcher_uplink",
                config_json=json.dumps(
                    {
                        ixia_uplink_interface: [
                            {
                                "starting_ip": f"{ixia_uplink_ic_parent_network_v6}::10",
                                "increment_ip": "0:0:0:0::2",
                                "prefix_length": 127,
                                "description": "Uplink IPv6 Peers",
                                "peer_group_name": peergroup_uplink_mimic_v6,
                                "num_sessions": total_peer_count,
                                "remote_as_4_byte": remote_uplink_as_4byte,
                                "remote_as_4_byte_step": 1,
                                "gateway_starting_ip": f"{ixia_uplink_ic_parent_network_v6}::11",
                                "gateway_increment_ip": "0:0:0:0::2",
                            },
                            {
                                "starting_ip": f"{ixia_uplink_ic_parent_network_v4}.0",
                                "increment_ip": "0.0.0.2",
                                "prefix_length": 31,
                                "description": "Uplink IPv4 Peers",
                                "peer_group_name": peergroup_uplink_mimic_v4,
                                "num_sessions": total_peer_count,
                                "remote_as_4_byte": remote_uplink_as_4byte,
                                "remote_as_4_byte_step": 1,
                                "gateway_starting_ip": f"{ixia_uplink_ic_parent_network_v4}.1",
                                "gateway_increment_ip": "0.0.0.2",
                            },
                        ],
                    }
                ),
            ),
            # Downlink: Configure DUT-side VLANs and BGP peers.
            create_configure_parallel_bgp_peers_task(
                hostname=device_name,
                configure_vlans_patcher_name="configure_vlans_patcher_downlink",
                add_bgp_peers_patcher_name="add_bgp_peers_patcher_downlink",
                config_json=json.dumps(
                    {
                        ixia_downlink_interface: [
                            {
                                "starting_ip": f"{ixia_downlink_ic_parent_network_v6}::10",
                                "increment_ip": "0:0:0:0::2",
                                "prefix_length": 127,
                                "description": "Downlink IPv6 Peers",
                                "peer_group_name": peergroup_downlink_mimic_v6,
                                "num_sessions": total_peer_count,
                                "remote_as_4_byte": remote_downlink_as_4byte,
                                "remote_as_4_byte_step": 1,
                                "gateway_starting_ip": f"{ixia_downlink_ic_parent_network_v6}::11",
                                "gateway_increment_ip": "0:0:0:0::2",
                            },
                            {
                                "starting_ip": f"{ixia_downlink_ic_parent_network_v4}.0",
                                "increment_ip": "0.0.0.2",
                                "prefix_length": 31,
                                "description": "Downlink IPv4 Peers",
                                "peer_group_name": peergroup_downlink_mimic_v4,
                                "num_sessions": total_peer_count,
                                "remote_as_4_byte": remote_downlink_as_4byte,
                                "remote_as_4_byte_step": 1,
                                "gateway_starting_ip": f"{ixia_downlink_ic_parent_network_v4}.1",
                                "gateway_increment_ip": "0.0.0.2",
                            },
                        ],
                    }
                ),
            ),
            # ---- Step 7: Apply all registered patchers ----
            create_coop_apply_patchers_task(
                hostnames=[device_name],
            ),
            create_wait_for_agent_convergence_task([device_name]),
        ],
        # ================================================================
        # IXIA Port Configs: Device Groups
        # ================================================================
        # Each port has 4 device groups:
        #   DG0: STABLE IPv6 (stable_peer_count peers, same prefixes)
        #   DG1: STABLE IPv4 (stable_peer_count peers, same prefixes)
        #   DG2: FLAPPING IPv6 (flapping_peer_count peers, same prefixes)
        #   DG3: FLAPPING IPv4 (flapping_peer_count peers, same prefixes)
        # All groups advertise the SAME prefix set to create wide ECMP.
        basic_port_configs=[
            # ---- UPLINK PORT ----
            taac_types.BasicPortConfig(
                endpoint=f"{device_name}:{ixia_uplink_interface}",
                device_group_configs=[
                    # DG0: STABLE IPv6
                    taac_types.DeviceGroupConfig(
                        device_group_index=0,
                        tag_name=STABLE_TAG,
                        multiplier=stable_peer_count,
                        v6_addresses_config=taac_types.IpAddressesConfig(
                            starting_ip=f"{ixia_uplink_ic_parent_network_v6}::11",
                            increment_ip="0:0:0:0::2",
                            gateway_starting_ip=f"{ixia_uplink_ic_parent_network_v6}::10",
                            gateway_increment_ip="0:0:0:0::2",
                            mask=127,
                        ),
                        v6_bgp_config=taac_types.BgpConfig(
                            local_as_4_bytes=remote_uplink_as_4byte,
                            local_as_increment=1,
                            enable_4_byte_local_as=True,
                            is_confed=is_uplink_peer_confed == "True",
                            bgp_capabilities=[ixia_types.BgpCapability.IpV6Unicast],
                            route_scales=[
                                _v6_route_scale(
                                    v6_uplink_prefix, ixia_uplink_communities
                                ),
                            ],
                        ),
                    ),
                    # DG1: STABLE IPv4
                    taac_types.DeviceGroupConfig(
                        device_group_index=1,
                        tag_name=STABLE_TAG,
                        multiplier=stable_peer_count,
                        v4_addresses_config=taac_types.IpAddressesConfig(
                            starting_ip=f"{ixia_uplink_ic_parent_network_v4}.1",
                            increment_ip="0.0.0.2",
                            gateway_starting_ip=f"{ixia_uplink_ic_parent_network_v4}.0",
                            gateway_increment_ip="0.0.0.2",
                            mask=31,
                        ),
                        v4_bgp_config=taac_types.BgpConfig(
                            local_as_4_bytes=remote_uplink_as_4byte,
                            local_as_increment=1,
                            enable_4_byte_local_as=True,
                            is_confed=is_uplink_peer_confed == "True",
                            bgp_capabilities=[ixia_types.BgpCapability.IpV4Unicast],
                            route_scales=[
                                _v4_route_scale(
                                    v4_uplink_prefix, ixia_uplink_communities
                                ),
                            ],
                        ),
                    ),
                    # DG2: FLAPPING IPv6
                    taac_types.DeviceGroupConfig(
                        device_group_index=2,
                        tag_name=FLAPPING_TAG,
                        multiplier=flapping_peer_count,
                        v6_addresses_config=taac_types.IpAddressesConfig(
                            starting_ip=f"{ixia_uplink_ic_parent_network_v6}::{v6_flapping_ixia_start:x}",
                            increment_ip="0:0:0:0::2",
                            gateway_starting_ip=f"{ixia_uplink_ic_parent_network_v6}::{v6_flapping_gw_start:x}",
                            gateway_increment_ip="0:0:0:0::2",
                            mask=127,
                        ),
                        v6_bgp_config=taac_types.BgpConfig(
                            local_as_4_bytes=uplink_flapping_as,
                            local_as_increment=1,
                            enable_4_byte_local_as=True,
                            is_confed=is_uplink_peer_confed == "True",
                            bgp_capabilities=[ixia_types.BgpCapability.IpV6Unicast],
                            route_scales=[
                                _v6_route_scale(
                                    v6_uplink_prefix, ixia_uplink_communities
                                ),
                            ],
                        ),
                    ),
                    # DG3: FLAPPING IPv4
                    taac_types.DeviceGroupConfig(
                        device_group_index=3,
                        tag_name=FLAPPING_TAG,
                        multiplier=flapping_peer_count,
                        v4_addresses_config=taac_types.IpAddressesConfig(
                            starting_ip=f"{ixia_uplink_ic_parent_network_v4}.{v4_flapping_ixia_start}",
                            increment_ip="0.0.0.2",
                            gateway_starting_ip=f"{ixia_uplink_ic_parent_network_v4}.{v4_flapping_gw_start}",
                            gateway_increment_ip="0.0.0.2",
                            mask=31,
                        ),
                        v4_bgp_config=taac_types.BgpConfig(
                            local_as_4_bytes=uplink_flapping_as,
                            local_as_increment=1,
                            enable_4_byte_local_as=True,
                            is_confed=is_uplink_peer_confed == "True",
                            bgp_capabilities=[ixia_types.BgpCapability.IpV4Unicast],
                            route_scales=[
                                _v4_route_scale(
                                    v4_uplink_prefix, ixia_uplink_communities
                                ),
                            ],
                        ),
                    ),
                ],
            ),
            # ---- DOWNLINK PORT ----
            taac_types.BasicPortConfig(
                endpoint=f"{device_name}:{ixia_downlink_interface}",
                device_group_configs=[
                    # DG0: STABLE IPv6
                    taac_types.DeviceGroupConfig(
                        device_group_index=0,
                        tag_name=STABLE_TAG,
                        multiplier=stable_peer_count,
                        v6_addresses_config=taac_types.IpAddressesConfig(
                            starting_ip=f"{ixia_downlink_ic_parent_network_v6}::11",
                            increment_ip="0:0:0:0::2",
                            gateway_starting_ip=f"{ixia_downlink_ic_parent_network_v6}::10",
                            gateway_increment_ip="0:0:0:0::2",
                            mask=127,
                        ),
                        v6_bgp_config=taac_types.BgpConfig(
                            local_as_4_bytes=remote_downlink_as_4byte,
                            local_as_increment=1,
                            enable_4_byte_local_as=True,
                            is_confed=is_downlink_peer_confed == "True",
                            bgp_capabilities=[ixia_types.BgpCapability.IpV6Unicast],
                            route_scales=[
                                _v6_route_scale(
                                    v6_downlink_prefix, ixia_downlink_communities
                                ),
                            ],
                        ),
                    ),
                    # DG1: STABLE IPv4
                    taac_types.DeviceGroupConfig(
                        device_group_index=1,
                        tag_name=STABLE_TAG,
                        multiplier=stable_peer_count,
                        v4_addresses_config=taac_types.IpAddressesConfig(
                            starting_ip=f"{ixia_downlink_ic_parent_network_v4}.1",
                            increment_ip="0.0.0.2",
                            gateway_starting_ip=f"{ixia_downlink_ic_parent_network_v4}.0",
                            gateway_increment_ip="0.0.0.2",
                            mask=31,
                        ),
                        v4_bgp_config=taac_types.BgpConfig(
                            local_as_4_bytes=remote_downlink_as_4byte,
                            local_as_increment=1,
                            enable_4_byte_local_as=True,
                            is_confed=is_downlink_peer_confed == "True",
                            bgp_capabilities=[ixia_types.BgpCapability.IpV4Unicast],
                            route_scales=[
                                _v4_route_scale(
                                    v4_downlink_prefix, ixia_downlink_communities
                                ),
                            ],
                        ),
                    ),
                    # DG2: FLAPPING IPv6
                    taac_types.DeviceGroupConfig(
                        device_group_index=2,
                        tag_name=FLAPPING_TAG,
                        multiplier=flapping_peer_count,
                        v6_addresses_config=taac_types.IpAddressesConfig(
                            starting_ip=f"{ixia_downlink_ic_parent_network_v6}::{v6_flapping_ixia_start:x}",
                            increment_ip="0:0:0:0::2",
                            gateway_starting_ip=f"{ixia_downlink_ic_parent_network_v6}::{v6_flapping_gw_start:x}",
                            gateway_increment_ip="0:0:0:0::2",
                            mask=127,
                        ),
                        v6_bgp_config=taac_types.BgpConfig(
                            local_as_4_bytes=downlink_flapping_as,
                            local_as_increment=1,
                            enable_4_byte_local_as=True,
                            is_confed=is_downlink_peer_confed == "True",
                            bgp_capabilities=[ixia_types.BgpCapability.IpV6Unicast],
                            route_scales=[
                                _v6_route_scale(
                                    v6_downlink_prefix, ixia_downlink_communities
                                ),
                            ],
                        ),
                    ),
                    # DG3: FLAPPING IPv4
                    taac_types.DeviceGroupConfig(
                        device_group_index=3,
                        tag_name=FLAPPING_TAG,
                        multiplier=flapping_peer_count,
                        v4_addresses_config=taac_types.IpAddressesConfig(
                            starting_ip=f"{ixia_downlink_ic_parent_network_v4}.{v4_flapping_ixia_start}",
                            increment_ip="0.0.0.2",
                            gateway_starting_ip=f"{ixia_downlink_ic_parent_network_v4}.{v4_flapping_gw_start}",
                            gateway_increment_ip="0.0.0.2",
                            mask=31,
                        ),
                        v4_bgp_config=taac_types.BgpConfig(
                            local_as_4_bytes=downlink_flapping_as,
                            local_as_increment=1,
                            enable_4_byte_local_as=True,
                            is_confed=is_downlink_peer_confed == "True",
                            bgp_capabilities=[ixia_types.BgpCapability.IpV4Unicast],
                            route_scales=[
                                _v4_route_scale(
                                    v4_downlink_prefix, ixia_downlink_communities
                                ),
                            ],
                        ),
                    ),
                ],
            ),
        ],
        # ================================================================
        # Traffic Items
        # ================================================================
        # Traffic flows between uplink and downlink peer-link IPs.
        # ECMP group validation is done via ECMP_GROUP_AND_MEMBER_COUNT_CHECK.
        basic_traffic_item_configs=[
            # V6 traffic: uplink -> downlink (peer-link IPs)
            taac_types.BasicTrafficItemConfig(
                name=f"{device_name.upper()}_V6_TRAFFIC",
                bidirectional=False,
                merge_destinations=True,
                line_rate=10,
                src_dest_mesh=ixia_types.SrcDestMeshType.MANY_TO_MANY,
                src_endpoints=[
                    taac_types.TrafficEndpoint(
                        name=f"{device_name}:{ixia_uplink_interface}",
                        device_group_index=0,
                    )
                ],
                dest_endpoints=[
                    taac_types.TrafficEndpoint(
                        name=f"{device_name}:{ixia_downlink_interface}",
                        device_group_index=0,
                    )
                ],
                traffic_type=ixia_types.TrafficType.IPV6,
                tracking_types=[ixia_types.TrafficStatsTrackingType.TRAFFIC_ITEM],
            ),
            # V4 traffic: uplink -> downlink (peer-link IPs)
            taac_types.BasicTrafficItemConfig(
                name=f"{device_name.upper()}_V4_TRAFFIC",
                bidirectional=False,
                merge_destinations=True,
                line_rate=10,
                src_dest_mesh=ixia_types.SrcDestMeshType.MANY_TO_MANY,
                src_endpoints=[
                    taac_types.TrafficEndpoint(
                        name=f"{device_name}:{ixia_uplink_interface}",
                        device_group_index=1,
                    )
                ],
                dest_endpoints=[
                    taac_types.TrafficEndpoint(
                        name=f"{device_name}:{ixia_downlink_interface}",
                        device_group_index=1,
                    )
                ],
                traffic_type=ixia_types.TrafficType.IPV4,
                tracking_types=[ixia_types.TrafficStatsTrackingType.TRAFFIC_ITEM],
            ),
        ],
        playbooks=playbooks,
    )
