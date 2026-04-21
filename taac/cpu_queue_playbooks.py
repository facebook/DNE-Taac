# (c) Meta Platforms, Inc. and affiliates. Confidential and proprietary.

# pyre-unsafe
import json
import typing as t

from taac.health_checks.constants import (
    SERVICES_TO_MONITOR_DURING_AGENT_RESTART,
)
from taac.step_definitions import (
    create_custom_step,
    create_interface_flap_step,
    create_longevity_step,
    create_service_convergence_step,
    create_service_interruption_step,
)
from taac.utils.json_thrift_utils import thrift_to_json
from taac.health_check.health_check import types as hc_types
from taac.test_as_a_config import types as taac_types
from taac.test_as_a_config.types import (
    Params,
    Playbook,
    PointInTimeHealthCheck,
    Service,
    SnapshotHealthCheck,
    Stage,
    Step,
    StepName,
)


# Playbook constants - single source of truth for playbook definitions.
# Used by both create_cpu_queue_playbooks() and UTP test case definitions.
# UTP uses .name to get the playbook name string.
TEST_LLDP_TRAFFIC_PUNTED_TO_CPU_MID_QUEUE = Playbook(
    name="test_lldp_traffic_punted_to_cpu_mid_queue",
)
TEST_BGP_CP_TRAFFIC_PUNTED_TO_CPU_HIGH_QUEUE = Playbook(
    name="test_bgp_cp_traffic_punted_to_cpu_high_queue",
)
TEST_DHCP_V6_TRAFFIC_PUNTED_TO_CPU_MID_QUEUE = Playbook(
    name="test_dhcp_v6_traffic_punted_to_cpu_mid_queue",
)
TEST_ICMP_V6_REQUEST_TRAFFIC_PUNTED_TO_CPU_MID_QUEUE = Playbook(
    name="test_icmp_v6_request_traffic_punted_to_cpu_mid_queue",
)
TEST_FBOSS_CPU_REMOTE_SUBNET_128_UNH = Playbook(
    name="test_fboss_cpu_remote_subnet_128_unh",
)
TEST_FBOSS_CPU_REMOTE_SUBNET_UNH = Playbook(
    name="test_fboss_cpu_remote_subnet_unh",
)
TEST_FBOSS_CPU_DIR_CONN_HOST_UNH = Playbook(
    name="test_fboss_cpu_dir_conn_host_unh",
)
TEST_LACP_TRAFFIC_PUNTED_TO_CPU_HIGH_QUEUE = Playbook(
    name="test_lacp_traffic_punted_to_cpu_high_queue",
)
TEST_NEXTHOP_LIMIT_1_PUNTED_TO_CPU_LOW_QUEUE = Playbook(
    name="test_nexthop_limit_1_punted_to_cpu_low_queue",
)
TEST_NEXTHOP_LIMIT_0_NOT_PUNTED_TO_CPU = Playbook(
    name="test_nexthop_limit_0_not_punted_to_cpu",
)
TEST_ARP_TRAFFIC_PUNTED_TO_CPU_HIGH_QUEUE = Playbook(
    name="test_arp_traffic_punted_to_cpu_high_queue",
)
TEST_ARP_RESPONSE_TRAFFIC_PUNTED_TO_CPU_HIGH_QUEUE = Playbook(
    name="test_arp_response_traffic_punted_to_cpu_high_queue",
)
TEST_QUEUE_PRIORITIZATION_HIGH_QUEUE_NO_DROPS = Playbook(
    name="test_queue_prioritization_high_queue_no_drops",
)
TEST_TTL_1_IPV4_TRAFFIC_PUNTED_TO_CPU_LOW_QUEUE = Playbook(
    name="test_ttl_1_ipv4_traffic_punted_to_cpu_low_queue",
)
TEST_TTL_0_IPV4_TRAFFIC_NOT_PUNTED_TO_CPU = Playbook(
    name="test_ttl_0_ipv4_traffic_not_punted_to_cpu",
)
# ICMP v4 sub-test playbooks (CPU_012 expansion)
TEST_ICMP_V4_ECHO_REQUEST_TRAFFIC_PUNTED_TO_CPU_MID_QUEUE = Playbook(
    name="test_icmp_v4_echo_request_traffic_punted_to_cpu_mid_queue",
)
TEST_ICMP_V4_ECHO_REPLY_TRAFFIC_PUNTED_TO_CPU_MID_QUEUE = Playbook(
    name="test_icmp_v4_echo_reply_traffic_punted_to_cpu_mid_queue",
)
TEST_ICMP_V4_DEST_UNREACHABLE_TRAFFIC_PUNTED_TO_CPU_MID_QUEUE = Playbook(
    name="test_icmp_v4_dest_unreachable_traffic_punted_to_cpu_mid_queue",
)
TEST_ICMP_V4_TIME_EXCEEDED_TRAFFIC_PUNTED_TO_CPU_MID_QUEUE = Playbook(
    name="test_icmp_v4_time_exceeded_traffic_punted_to_cpu_mid_queue",
)
# ICMPv6 global DSCP 48 sub-test playbooks (CPU_019 expansion)
TEST_ICMPV6_ECHO_REQUEST_GLOBAL_DSCP48_TRAFFIC_PUNTED_TO_CPU_MID_QUEUE = Playbook(
    name="test_icmpv6_echo_request_global_dscp48_traffic_punted_to_cpu_mid_queue",
)
TEST_ICMPV6_ECHO_REPLY_GLOBAL_DSCP48_TRAFFIC_PUNTED_TO_CPU_MID_QUEUE = Playbook(
    name="test_icmpv6_echo_reply_global_dscp48_traffic_punted_to_cpu_mid_queue",
)
TEST_ICMPV6_DEST_UNREACHABLE_GLOBAL_DSCP48_TRAFFIC_PUNTED_TO_CPU_MID_QUEUE = Playbook(
    name="test_icmpv6_dest_unreachable_global_dscp48_traffic_punted_to_cpu_mid_queue",
)
TEST_ICMPV6_PACKET_TOO_BIG_GLOBAL_DSCP48_TRAFFIC_PUNTED_TO_CPU_MID_QUEUE = Playbook(
    name="test_icmpv6_packet_too_big_global_dscp48_traffic_punted_to_cpu_mid_queue",
)
TEST_ICMPV6_TIME_EXCEEDED_GLOBAL_DSCP48_TRAFFIC_PUNTED_TO_CPU_MID_QUEUE = Playbook(
    name="test_icmpv6_time_exceeded_global_dscp48_traffic_punted_to_cpu_mid_queue",
)
# ICMPv6 link local DSCP 0 sub-test playbooks (CPU_020 expansion)
TEST_ICMPV6_ECHO_REQUEST_LINK_LOCAL_TRAFFIC_PUNTED_TO_CPU_MID_QUEUE = Playbook(
    name="test_icmpv6_echo_request_link_local_traffic_punted_to_cpu_mid_queue",
)
TEST_ICMPV6_ECHO_REPLY_LINK_LOCAL_TRAFFIC_PUNTED_TO_CPU_MID_QUEUE = Playbook(
    name="test_icmpv6_echo_reply_link_local_traffic_punted_to_cpu_mid_queue",
)
TEST_ICMPV6_DEST_UNREACHABLE_LINK_LOCAL_TRAFFIC_PUNTED_TO_CPU_MID_QUEUE = Playbook(
    name="test_icmpv6_dest_unreachable_link_local_traffic_punted_to_cpu_mid_queue",
)
TEST_ICMPV6_PACKET_TOO_BIG_LINK_LOCAL_TRAFFIC_PUNTED_TO_CPU_MID_QUEUE = Playbook(
    name="test_icmpv6_packet_too_big_link_local_traffic_punted_to_cpu_mid_queue",
)
TEST_ICMPV6_TIME_EXCEEDED_LINK_LOCAL_TRAFFIC_PUNTED_TO_CPU_MID_QUEUE = Playbook(
    name="test_icmpv6_time_exceeded_link_local_traffic_punted_to_cpu_mid_queue",
)
# NDP multicast sub-test playbooks (CPU_021 expansion)
TEST_NDP_NS_MULTICAST_TRAFFIC_PUNTED_TO_CPU_HIGH_QUEUE = Playbook(
    name="test_ndp_ns_multicast_traffic_punted_to_cpu_high_queue",
)
TEST_NDP_NA_MULTICAST_TRAFFIC_PUNTED_TO_CPU_HIGH_QUEUE = Playbook(
    name="test_ndp_na_multicast_traffic_punted_to_cpu_high_queue",
)
TEST_NDP_RS_MULTICAST_TRAFFIC_PUNTED_TO_CPU_HIGH_QUEUE = Playbook(
    name="test_ndp_rs_multicast_traffic_punted_to_cpu_high_queue",
)
TEST_NDP_RA_MULTICAST_TRAFFIC_PUNTED_TO_CPU_HIGH_QUEUE = Playbook(
    name="test_ndp_ra_multicast_traffic_punted_to_cpu_high_queue",
)
# DHCP v4 sub-test playbooks (CPU_010/CPU_011)
TEST_DHCP_V4_DISCOVER_TRAFFIC_PUNTED_TO_CPU_MID_QUEUE = Playbook(
    name="test_dhcp_v4_discover_traffic_punted_to_cpu_mid_queue",
)
TEST_DHCP_V4_DISCOVER_TO_SERVER_TRAFFIC_PUNTED_TO_CPU_MID_QUEUE = Playbook(
    name="test_dhcp_v4_discover_to_server_traffic_punted_to_cpu_mid_queue",
)
# BGP v4 CP traffic playbooks (CPU_005/CPU_006)
TEST_BGP_CP_V4_TRAFFIC_PUNTED_TO_CPU_HIGH_QUEUE = Playbook(
    name="test_bgp_cp_v4_traffic_punted_to_cpu_high_queue",
)
TEST_BGP_CP_V4_DSCP0_TRAFFIC_PUNTED_TO_CPU_HIGH_QUEUE = Playbook(
    name="test_bgp_cp_v4_dscp0_traffic_punted_to_cpu_high_queue",
)


def create_cpu_queue_playbooks(
    low_queue: int,
    mid_queue: int,
    high_queue: int,
    ixia_downlink_interface: str,
) -> t.List[Playbook]:
    """Create all CPU queue test playbooks.

    Args:
        low_queue: Queue index for low priority traffic
        mid_queue: Queue index for mid priority traffic
        high_queue: Queue index for high priority traffic
        ixia_downlink_interface: IXIA downlink interface name (for UNH playbooks)

    Returns:
        List of all CPU queue test Playbook objects
    """
    longevity_playbook = Playbook(
        name="1_test_longevity",
        traffic_items_to_start=[
            "V6_DIRECTIONAL_TRAFFIC_BETWEEN_DOWNLINK_AND_UPLINK",
            "V4_DIRECTIONAL_TRAFFIC_BETWEEN_DOWNLINK_AND_UPLINK",
        ],
        stages=[
            Stage(
                steps=[create_longevity_step(duration=240)],
            )
        ],
    )

    test_cpu_mid_queue_traffic_playbook = Playbook(
        name="test_cpu_mid_queue_traffic",
        traffic_items_to_start=[
            "TEST_RAW_LLDP_TRAFFIC",
            "BGP_PREFIX_TRAFFIC",
        ],
        stages=[
            Stage(
                steps=[create_longevity_step(duration=60)],
            )
        ],
        snapshot_checks=[
            SnapshotHealthCheck(
                name=hc_types.CheckName.CPU_QUEUE_CHECK,
                input_json=thrift_to_json(
                    hc_types.CpuQueueHealthCheckIn(
                        active_queues=[mid_queue],
                        no_discard_queues=[high_queue],
                        active_min_out_pps_per_queue={low_queue: 10},
                    )
                ),
            )
        ],
    )

    test_cpu_high_queue_traffic_playbook = Playbook(
        name="test_cpu_high_queue_traffic",
        traffic_items_to_start=[
            "TEST_RAW_BGP_CP_TRAFFIC",
            "BGP_PREFIX_TRAFFIC",
        ],
        stages=[
            Stage(
                steps=[create_longevity_step(duration=60)],
            )
        ],
        snapshot_checks=[
            SnapshotHealthCheck(
                name=hc_types.CheckName.CPU_QUEUE_CHECK,
                input_json=thrift_to_json(
                    hc_types.CpuQueueHealthCheckIn(
                        active_queues=[high_queue],
                        no_discard_queues=[high_queue],
                        active_min_out_pps_per_queue={low_queue: 10},
                    )
                ),
            )
        ],
    )

    # Queue prioritization test: send burst traffic to LOW and MID queues
    # to create drops, while verifying no drops on HIGH queue (BGP_CP)
    # LOW queue: TTL=1 IPv4 traffic (punted for ICMP TTL exceeded)
    # MID queue: DHCPv6 traffic
    # HIGH queue: BGP CP traffic
    test_queue_prioritization_high_queue_no_drops_playbook = Playbook(
        name="test_queue_prioritization_high_queue_no_drops",
        traffic_items_to_start=[
            "BURST_LOW_QUEUE_TTL1_TRAFFIC",
            "BURST_MID_QUEUE_DHCPV6_TRAFFIC",
            "TEST_RAW_BGP_CP_TRAFFIC",
        ],
        stages=[
            Stage(
                steps=[create_longevity_step(duration=60)],
            )
        ],
        snapshot_checks=[
            SnapshotHealthCheck(
                name=hc_types.CheckName.CPU_QUEUE_CHECK,
                input_json=thrift_to_json(
                    hc_types.CpuQueueHealthCheckIn(
                        active_queues=[low_queue, mid_queue, high_queue],
                        no_discard_queues=[high_queue],
                    )
                ),
            )
        ],
    )

    test_icmp_v6_request_traffic_punted_to_cpu_mid_queue_playbook = Playbook(
        name=TEST_ICMP_V6_REQUEST_TRAFFIC_PUNTED_TO_CPU_MID_QUEUE.name,
        traffic_items_to_start=[
            "TEST_RAW_ICMP_V6_REQUEST_TRAFFIC",
            "BGP_PREFIX_TRAFFIC",
        ],
        stages=[
            Stage(
                steps=[create_longevity_step(duration=60)],
            )
        ],
        snapshot_checks=[
            SnapshotHealthCheck(
                name=hc_types.CheckName.CPU_QUEUE_CHECK,
                input_json=thrift_to_json(
                    hc_types.CpuQueueHealthCheckIn(
                        active_queues=[mid_queue],
                        no_discard_queues=[high_queue],
                        active_min_out_pps_per_queue={low_queue: 10},
                    )
                ),
            )
        ],
    )

    test_icmp_v4_echo_request_traffic_punted_to_cpu_mid_queue_playbook = Playbook(
        name="test_icmp_v4_echo_request_traffic_punted_to_cpu_mid_queue",
        traffic_items_to_start=[
            "TEST_RAW_ICMP_V4_ECHO_REQUEST_TRAFFIC",
            "BGP_PREFIX_TRAFFIC",
        ],
        stages=[
            Stage(
                steps=[create_longevity_step(duration=60)],
            )
        ],
        snapshot_checks=[
            SnapshotHealthCheck(
                name=hc_types.CheckName.CPU_QUEUE_CHECK,
                input_json=thrift_to_json(
                    hc_types.CpuQueueHealthCheckIn(
                        active_queues=[mid_queue],
                        no_discard_queues=[high_queue],
                        active_min_out_pps_per_queue={low_queue: 10},
                    )
                ),
            )
        ],
    )

    test_icmp_v4_echo_reply_traffic_punted_to_cpu_mid_queue_playbook = Playbook(
        name="test_icmp_v4_echo_reply_traffic_punted_to_cpu_mid_queue",
        traffic_items_to_start=[
            "TEST_RAW_ICMP_V4_ECHO_REPLY_TRAFFIC",
            "BGP_PREFIX_TRAFFIC",
        ],
        stages=[
            Stage(
                steps=[create_longevity_step(duration=60)],
            )
        ],
        snapshot_checks=[
            SnapshotHealthCheck(
                name=hc_types.CheckName.CPU_QUEUE_CHECK,
                input_json=thrift_to_json(
                    hc_types.CpuQueueHealthCheckIn(
                        active_queues=[mid_queue],
                        no_discard_queues=[high_queue],
                        active_min_out_pps_per_queue={low_queue: 10},
                    )
                ),
            )
        ],
    )

    test_icmp_v4_dest_unreachable_traffic_punted_to_cpu_mid_queue_playbook = Playbook(
        name="test_icmp_v4_dest_unreachable_traffic_punted_to_cpu_mid_queue",
        traffic_items_to_start=[
            "TEST_RAW_ICMP_V4_DEST_UNREACHABLE_TRAFFIC",
            "BGP_PREFIX_TRAFFIC",
        ],
        stages=[
            Stage(
                steps=[create_longevity_step(duration=60)],
            )
        ],
        snapshot_checks=[
            SnapshotHealthCheck(
                name=hc_types.CheckName.CPU_QUEUE_CHECK,
                input_json=thrift_to_json(
                    hc_types.CpuQueueHealthCheckIn(
                        active_queues=[mid_queue],
                        no_discard_queues=[high_queue],
                        active_min_out_pps_per_queue={low_queue: 10},
                    )
                ),
            )
        ],
    )

    test_icmp_v4_time_exceeded_traffic_punted_to_cpu_mid_queue_playbook = Playbook(
        name="test_icmp_v4_time_exceeded_traffic_punted_to_cpu_mid_queue",
        traffic_items_to_start=[
            "TEST_RAW_ICMP_V4_TIME_EXCEEDED_TRAFFIC",
            "BGP_PREFIX_TRAFFIC",
        ],
        stages=[
            Stage(
                steps=[create_longevity_step(duration=60)],
            )
        ],
        snapshot_checks=[
            SnapshotHealthCheck(
                name=hc_types.CheckName.CPU_QUEUE_CHECK,
                input_json=thrift_to_json(
                    hc_types.CpuQueueHealthCheckIn(
                        active_queues=[mid_queue],
                        no_discard_queues=[high_queue],
                        active_min_out_pps_per_queue={low_queue: 10},
                    )
                ),
            )
        ],
    )

    test_dhcp_v6_traffic_punted_to_cpu_mid_queue_playbook = Playbook(
        name=TEST_DHCP_V6_TRAFFIC_PUNTED_TO_CPU_MID_QUEUE.name,
        traffic_items_to_start=[
            "TEST_RAW_DHCP_V6_TRAFFIC",
            "BGP_PREFIX_TRAFFIC",
        ],
        stages=[
            Stage(
                steps=[create_longevity_step(duration=60)],
            )
        ],
        snapshot_checks=[
            SnapshotHealthCheck(
                name=hc_types.CheckName.CPU_QUEUE_CHECK,
                input_json=thrift_to_json(
                    hc_types.CpuQueueHealthCheckIn(
                        active_queues=[mid_queue],
                        no_discard_queues=[high_queue],
                        active_min_out_pps_per_queue={low_queue: 10},
                    )
                ),
            )
        ],
    )

    test_dhcp_v4_discover_traffic_punted_to_cpu_mid_queue_playbook = Playbook(
        name="test_dhcp_v4_discover_traffic_punted_to_cpu_mid_queue",
        traffic_items_to_start=[
            "TEST_RAW_DHCP_V4_DISCOVER_TRAFFIC",
            "BGP_PREFIX_TRAFFIC",
        ],
        stages=[
            Stage(
                steps=[create_longevity_step(duration=60)],
            )
        ],
        snapshot_checks=[
            SnapshotHealthCheck(
                name=hc_types.CheckName.CPU_QUEUE_CHECK,
                input_json=thrift_to_json(
                    hc_types.CpuQueueHealthCheckIn(
                        active_queues=[mid_queue],
                        no_discard_queues=[high_queue],
                        active_min_out_pps_per_queue={low_queue: 10},
                    )
                ),
            )
        ],
    )

    test_dhcp_v4_discover_to_server_traffic_punted_to_cpu_mid_queue_playbook = Playbook(
        name="test_dhcp_v4_discover_to_server_traffic_punted_to_cpu_mid_queue",
        traffic_items_to_start=[
            "TEST_RAW_DHCP_V4_DISCOVER_TO_SERVER_TRAFFIC",
            "BGP_PREFIX_TRAFFIC",
        ],
        stages=[
            Stage(
                steps=[create_longevity_step(duration=60)],
            )
        ],
        snapshot_checks=[
            SnapshotHealthCheck(
                name=hc_types.CheckName.CPU_QUEUE_CHECK,
                input_json=thrift_to_json(
                    hc_types.CpuQueueHealthCheckIn(
                        active_queues=[mid_queue],
                        no_discard_queues=[high_queue],
                        active_min_out_pps_per_queue={low_queue: 10},
                    )
                ),
            )
        ],
    )

    test_lldp_traffic_punted_to_cpu_mid_queue_playbook = Playbook(
        name=TEST_LLDP_TRAFFIC_PUNTED_TO_CPU_MID_QUEUE.name,
        traffic_items_to_start=[
            "TEST_RAW_LLDP_TRAFFIC",
            "BGP_PREFIX_TRAFFIC",
        ],
        stages=[
            Stage(
                steps=[create_longevity_step(duration=60)],
            )
        ],
        snapshot_checks=[
            SnapshotHealthCheck(
                name=hc_types.CheckName.CPU_QUEUE_CHECK,
                input_json=thrift_to_json(
                    hc_types.CpuQueueHealthCheckIn(
                        active_queues=[mid_queue],
                        no_discard_queues=[high_queue],
                        active_min_out_pps_per_queue={low_queue: 10},
                    )
                ),
            )
        ],
    )

    test_bgp_cp_traffic_punted_to_cpu_high_queue_playbook = Playbook(
        name=TEST_BGP_CP_TRAFFIC_PUNTED_TO_CPU_HIGH_QUEUE.name,
        traffic_items_to_start=[
            "TEST_RAW_BGP_CP_TRAFFIC",
            "BGP_PREFIX_TRAFFIC",
        ],
        stages=[
            Stage(
                steps=[create_longevity_step(duration=60)],
            )
        ],
        snapshot_checks=[
            SnapshotHealthCheck(
                name=hc_types.CheckName.CPU_QUEUE_CHECK,
                input_json=thrift_to_json(
                    hc_types.CpuQueueHealthCheckIn(
                        active_queues=[high_queue],
                        no_discard_queues=[high_queue],
                        active_min_out_pps_per_queue={low_queue: 10},
                    )
                ),
            )
        ],
    )

    test_bgp_cp_v4_traffic_punted_to_cpu_high_queue_playbook = Playbook(
        name=TEST_BGP_CP_V4_TRAFFIC_PUNTED_TO_CPU_HIGH_QUEUE.name,
        traffic_items_to_start=[
            "TEST_RAW_BGP_CP_V4_TRAFFIC",
            "BGP_PREFIX_TRAFFIC_V4",
        ],
        stages=[
            Stage(
                steps=[create_longevity_step(duration=60)],
            )
        ],
        snapshot_checks=[
            SnapshotHealthCheck(
                name=hc_types.CheckName.CPU_QUEUE_CHECK,
                input_json=thrift_to_json(
                    hc_types.CpuQueueHealthCheckIn(
                        active_queues=[high_queue],
                        no_discard_queues=[high_queue],
                        active_min_out_pps_per_queue={low_queue: 10},
                    )
                ),
            )
        ],
    )

    test_bgp_cp_v4_dscp0_traffic_punted_to_cpu_high_queue_playbook = Playbook(
        name=TEST_BGP_CP_V4_DSCP0_TRAFFIC_PUNTED_TO_CPU_HIGH_QUEUE.name,
        traffic_items_to_start=[
            "TEST_RAW_BGP_CP_V4_DSCP0_TRAFFIC",
            "BGP_PREFIX_TRAFFIC_V4",
        ],
        stages=[
            Stage(
                steps=[create_longevity_step(duration=60)],
            )
        ],
        snapshot_checks=[
            SnapshotHealthCheck(
                name=hc_types.CheckName.CPU_QUEUE_CHECK,
                input_json=thrift_to_json(
                    hc_types.CpuQueueHealthCheckIn(
                        active_queues=[high_queue],
                        no_discard_queues=[high_queue],
                        active_min_out_pps_per_queue={low_queue: 10},
                    )
                ),
            )
        ],
    )

    test_lacp_traffic_punted_to_cpu_high_queue_playbook = Playbook(
        name=TEST_LACP_TRAFFIC_PUNTED_TO_CPU_HIGH_QUEUE.name,
        traffic_items_to_start=[
            "TEST_LACP_SLOW_TIMER_TRAFFIC",
            "BGP_PREFIX_TRAFFIC",
        ],
        stages=[
            Stage(
                steps=[create_longevity_step(duration=60)],
            )
        ],
        snapshot_checks=[
            SnapshotHealthCheck(
                name=hc_types.CheckName.CPU_QUEUE_CHECK,
                input_json=thrift_to_json(
                    hc_types.CpuQueueHealthCheckIn(
                        active_queues=[high_queue],
                        no_discard_queues=[high_queue],
                        active_min_out_pps_per_queue={low_queue: 10},
                    )
                ),
            )
        ],
    )

    test_nexthop_limit_1_punted_to_cpu_low_queue_playbook = Playbook(
        name=TEST_NEXTHOP_LIMIT_1_PUNTED_TO_CPU_LOW_QUEUE.name,
        traffic_items_to_start=[
            "TEST_NEXTHOP_LIMIT_1_IPV6_TRAFFIC",
            "BGP_PREFIX_TRAFFIC",
        ],
        stages=[
            Stage(
                steps=[create_longevity_step(duration=60)],
            )
        ],
        snapshot_checks=[
            SnapshotHealthCheck(
                name=hc_types.CheckName.CPU_QUEUE_CHECK,
                input_json=thrift_to_json(
                    hc_types.CpuQueueHealthCheckIn(
                        active_queues=[low_queue],
                        no_discard_queues=[mid_queue, high_queue],
                        active_min_out_pps_per_queue={low_queue: 10},
                    )
                ),
            )
        ],
    )

    test_nexthop_limit_0_not_punted_to_cpu_playbook = Playbook(
        name=TEST_NEXTHOP_LIMIT_0_NOT_PUNTED_TO_CPU.name,
        traffic_items_to_start=[
            "TEST_NEXTHOP_LIMIT_0_IPV6_TRAFFIC",
            "BGP_PREFIX_TRAFFIC",
        ],
        stages=[
            Stage(
                steps=[create_longevity_step(duration=60)],
            )
        ],
        snapshot_checks=[
            SnapshotHealthCheck(
                name=hc_types.CheckName.CPU_QUEUE_CHECK,
                input_json=thrift_to_json(
                    hc_types.CpuQueueHealthCheckIn(
                        active_queues=[],
                        no_discard_queues=[low_queue, mid_queue, high_queue],
                        active_min_out_pps_per_queue={low_queue: 10},
                    )
                ),
            )
        ],
    )

    test_ttl_1_ipv4_traffic_punted_to_cpu_low_queue_playbook = Playbook(
        name="test_ttl_1_ipv4_traffic_punted_to_cpu_low_queue",
        traffic_items_to_start=[
            "TEST_TTL_1_IPV4_TRAFFIC",
            "BGP_PREFIX_TRAFFIC",
        ],
        stages=[
            Stage(
                steps=[create_longevity_step(duration=30)],
            )
        ],
        snapshot_checks=[
            SnapshotHealthCheck(
                name=hc_types.CheckName.CPU_QUEUE_CHECK,
                input_json=thrift_to_json(
                    hc_types.CpuQueueHealthCheckIn(
                        active_queues=[low_queue],
                        no_discard_queues=[mid_queue, high_queue],
                        active_min_out_pps_per_queue={low_queue: 10},
                    )
                ),
            )
        ],
    )

    test_ttl_0_ipv4_traffic_not_punted_to_cpu_playbook = Playbook(
        name="test_ttl_0_ipv4_traffic_not_punted_to_cpu",
        traffic_items_to_start=[
            "TEST_TTL_0_IPV4_TRAFFIC",
            "BGP_PREFIX_TRAFFIC",
        ],
        stages=[
            Stage(
                steps=[create_longevity_step(duration=30)],
            )
        ],
        snapshot_checks=[
            SnapshotHealthCheck(
                name=hc_types.CheckName.CPU_QUEUE_CHECK,
                input_json=thrift_to_json(
                    hc_types.CpuQueueHealthCheckIn(
                        active_queues=[],
                        no_discard_queues=[low_queue, mid_queue, high_queue],
                        active_min_out_pps_per_queue={low_queue: 10},
                    )
                ),
            )
        ],
    )

    test_arp_traffic_punted_to_cpu_high_queue_playbook = Playbook(
        name="test_arp_traffic_punted_to_cpu_high_queue",
        traffic_items_to_start=[
            "TEST_RAW_ARP_REQUEST_TRAFFIC",
            "BGP_PREFIX_TRAFFIC",
        ],
        stages=[
            Stage(
                id="test_arp_traffic_punted_to_cpu_high_queue",
                steps=[
                    create_longevity_step(duration=60),
                ],
            ),
        ],
        snapshot_checks=[
            SnapshotHealthCheck(
                name=hc_types.CheckName.CPU_QUEUE_CHECK,
                input_json=thrift_to_json(
                    hc_types.CpuQueueHealthCheckIn(
                        active_queues=[high_queue],  # ARP should go to HIGH queue
                        no_discard_queues=[high_queue],  # No drops allowed
                        active_min_out_pps_per_queue={high_queue: 10},
                    )
                ),
            ),
        ],
    )

    test_arp_response_traffic_punted_to_cpu_high_queue_playbook = Playbook(
        name="test_arp_response_traffic_punted_to_cpu_high_queue",
        traffic_items_to_start=[
            "TEST_RAW_ARP_RESPONSE_TRAFFIC",
            "BGP_PREFIX_TRAFFIC",
        ],
        stages=[
            Stage(
                id="test_arp_response_traffic_punted_to_cpu_high_queue",
                steps=[
                    create_longevity_step(duration=60),
                ],
            ),
        ],
        snapshot_checks=[
            SnapshotHealthCheck(
                name=hc_types.CheckName.CPU_QUEUE_CHECK,
                input_json=thrift_to_json(
                    hc_types.CpuQueueHealthCheckIn(
                        active_queues=[
                            high_queue
                        ],  # ARP Response should go to HIGH queue
                        no_discard_queues=[high_queue],  # No drops allowed
                        active_min_out_pps_per_queue={high_queue: 10},
                    )
                ),
            ),
        ],
    )

    test_ndp_ns_multicast_traffic_punted_to_cpu_high_queue_playbook = Playbook(
        name="test_ndp_ns_multicast_traffic_punted_to_cpu_high_queue",
        traffic_items_to_start=[
            "TEST_NDP_NS_MULTICAST_TRAFFIC",
            "BGP_PREFIX_TRAFFIC",
        ],
        stages=[
            Stage(
                id="test_ndp_ns_multicast_traffic_punted_to_cpu_high_queue",
                steps=[
                    create_longevity_step(duration=60),
                ],
            ),
        ],
        snapshot_checks=[
            SnapshotHealthCheck(
                name=hc_types.CheckName.CPU_QUEUE_CHECK,
                input_json=thrift_to_json(
                    hc_types.CpuQueueHealthCheckIn(
                        active_queues=[high_queue],  # NDP NS should go to HIGH queue
                        no_discard_queues=[high_queue],  # No drops allowed
                        active_min_out_pps_per_queue={high_queue: 10},
                    )
                ),
            ),
        ],
    )

    test_ndp_na_multicast_traffic_punted_to_cpu_high_queue_playbook = Playbook(
        name="test_ndp_na_multicast_traffic_punted_to_cpu_high_queue",
        traffic_items_to_start=[
            "TEST_NDP_NA_MULTICAST_TRAFFIC",
            "BGP_PREFIX_TRAFFIC",
        ],
        stages=[
            Stage(
                id="test_ndp_na_multicast_traffic_punted_to_cpu_high_queue",
                steps=[
                    create_longevity_step(duration=60),
                ],
            ),
        ],
        snapshot_checks=[
            SnapshotHealthCheck(
                name=hc_types.CheckName.CPU_QUEUE_CHECK,
                input_json=thrift_to_json(
                    hc_types.CpuQueueHealthCheckIn(
                        active_queues=[high_queue],  # NDP NA should go to HIGH queue
                        no_discard_queues=[high_queue],  # No drops allowed
                        active_min_out_pps_per_queue={high_queue: 10},
                    )
                ),
            ),
        ],
    )

    test_ndp_rs_multicast_traffic_punted_to_cpu_high_queue_playbook = Playbook(
        name="test_ndp_rs_multicast_traffic_punted_to_cpu_high_queue",
        traffic_items_to_start=[
            "TEST_NDP_RS_MULTICAST_TRAFFIC",
            "BGP_PREFIX_TRAFFIC",
        ],
        stages=[
            Stage(
                id="test_ndp_rs_multicast_traffic_punted_to_cpu_high_queue",
                steps=[
                    create_longevity_step(duration=60),
                ],
            ),
        ],
        snapshot_checks=[
            SnapshotHealthCheck(
                name=hc_types.CheckName.CPU_QUEUE_CHECK,
                input_json=thrift_to_json(
                    hc_types.CpuQueueHealthCheckIn(
                        active_queues=[high_queue],  # NDP RS should go to HIGH queue
                        no_discard_queues=[high_queue],  # No drops allowed
                        active_min_out_pps_per_queue={high_queue: 10},
                    )
                ),
            ),
        ],
    )

    test_ndp_ra_multicast_traffic_punted_to_cpu_high_queue_playbook = Playbook(
        name="test_ndp_ra_multicast_traffic_punted_to_cpu_high_queue",
        traffic_items_to_start=[
            "TEST_NDP_RA_MULTICAST_TRAFFIC",
            "BGP_PREFIX_TRAFFIC",
        ],
        stages=[
            Stage(
                id="test_ndp_ra_multicast_traffic_punted_to_cpu_high_queue",
                steps=[
                    create_longevity_step(duration=60),
                ],
            ),
        ],
        snapshot_checks=[
            SnapshotHealthCheck(
                name=hc_types.CheckName.CPU_QUEUE_CHECK,
                input_json=thrift_to_json(
                    hc_types.CpuQueueHealthCheckIn(
                        active_queues=[high_queue],  # NDP RA should go to HIGH queue
                        no_discard_queues=[high_queue],  # No drops allowed
                        active_min_out_pps_per_queue={high_queue: 10},
                    )
                ),
            ),
        ],
    )

    # Commented out as this is not supported in the current version of the testbed for KO3 devices T252169955
    # Playbook(
    #     name="test_ndp_ns_unicast_traffic_punted_to_cpu_high_queue",
    #     ...
    # ),
    # Playbook(
    #     name="test_ndp_na_unicast_traffic_punted_to_cpu_high_queue",
    #     ...
    # ),
    # Playbook(
    #     name="test_ndp_rs_unicast_traffic_punted_to_cpu_high_queue",
    #     ...
    # ),
    # Playbook(
    #     name="test_ndp_ra_unicast_traffic_punted_to_cpu_high_queue",
    #     ...
    # ),
    # ICMPv6 Non-NDP with Link-Local Addresses - Punted to MID queue
    test_icmpv6_echo_request_link_local_traffic_punted_to_cpu_mid_queue_playbook = Playbook(
        name="test_icmpv6_echo_request_link_local_traffic_punted_to_cpu_mid_queue",
        traffic_items_to_start=[
            "TEST_ICMPV6_ECHO_REQUEST_LINK_LOCAL_TRAFFIC",
            "BGP_PREFIX_TRAFFIC",
        ],
        stages=[
            Stage(
                id="test_icmpv6_echo_request_link_local_traffic_punted_to_cpu_mid_queue",
                steps=[
                    create_longevity_step(duration=60),
                ],
            ),
        ],
        snapshot_checks=[
            SnapshotHealthCheck(
                name=hc_types.CheckName.CPU_QUEUE_CHECK,
                input_json=thrift_to_json(
                    hc_types.CpuQueueHealthCheckIn(
                        active_queues=[mid_queue],
                        no_discard_queues=[high_queue],
                        active_min_out_pps_per_queue={low_queue: 10},
                    )
                ),
            ),
        ],
    )

    test_icmpv6_echo_reply_link_local_traffic_punted_to_cpu_mid_queue_playbook = Playbook(
        name="test_icmpv6_echo_reply_link_local_traffic_punted_to_cpu_mid_queue",
        traffic_items_to_start=[
            "TEST_ICMPV6_ECHO_REPLY_LINK_LOCAL_TRAFFIC",
            "BGP_PREFIX_TRAFFIC",
        ],
        stages=[
            Stage(
                id="test_icmpv6_echo_reply_link_local_traffic_punted_to_cpu_mid_queue",
                steps=[
                    create_longevity_step(duration=60),
                ],
            ),
        ],
        snapshot_checks=[
            SnapshotHealthCheck(
                name=hc_types.CheckName.CPU_QUEUE_CHECK,
                input_json=thrift_to_json(
                    hc_types.CpuQueueHealthCheckIn(
                        active_queues=[mid_queue],
                        no_discard_queues=[high_queue],
                        active_min_out_pps_per_queue={low_queue: 10},
                    )
                ),
            ),
        ],
    )

    test_icmpv6_dest_unreachable_link_local_traffic_punted_to_cpu_mid_queue_playbook = Playbook(
        name="test_icmpv6_dest_unreachable_link_local_traffic_punted_to_cpu_mid_queue",
        traffic_items_to_start=[
            "TEST_ICMPV6_DEST_UNREACHABLE_LINK_LOCAL_TRAFFIC",
            "BGP_PREFIX_TRAFFIC",
        ],
        stages=[
            Stage(
                id="test_icmpv6_dest_unreachable_link_local_traffic_punted_to_cpu_mid_queue",
                steps=[
                    create_longevity_step(duration=60),
                ],
            ),
        ],
        snapshot_checks=[
            SnapshotHealthCheck(
                name=hc_types.CheckName.CPU_QUEUE_CHECK,
                input_json=thrift_to_json(
                    hc_types.CpuQueueHealthCheckIn(
                        active_queues=[mid_queue],
                        no_discard_queues=[high_queue],
                        active_min_out_pps_per_queue={low_queue: 10},
                    )
                ),
            ),
        ],
    )

    test_icmpv6_packet_too_big_link_local_traffic_punted_to_cpu_mid_queue_playbook = Playbook(
        name="test_icmpv6_packet_too_big_link_local_traffic_punted_to_cpu_mid_queue",
        traffic_items_to_start=[
            "TEST_ICMPV6_PACKET_TOO_BIG_LINK_LOCAL_TRAFFIC",
            "BGP_PREFIX_TRAFFIC",
        ],
        stages=[
            Stage(
                id="test_icmpv6_packet_too_big_link_local_traffic_punted_to_cpu_mid_queue",
                steps=[
                    create_longevity_step(duration=60),
                ],
            ),
        ],
        snapshot_checks=[
            SnapshotHealthCheck(
                name=hc_types.CheckName.CPU_QUEUE_CHECK,
                input_json=thrift_to_json(
                    hc_types.CpuQueueHealthCheckIn(
                        active_queues=[mid_queue],
                        no_discard_queues=[high_queue],
                        active_min_out_pps_per_queue={low_queue: 10},
                    )
                ),
            ),
        ],
    )

    test_icmpv6_time_exceeded_link_local_traffic_punted_to_cpu_mid_queue_playbook = Playbook(
        name="test_icmpv6_time_exceeded_link_local_traffic_punted_to_cpu_mid_queue",
        traffic_items_to_start=[
            "TEST_ICMPV6_TIME_EXCEEDED_LINK_LOCAL_TRAFFIC",
            "BGP_PREFIX_TRAFFIC",
        ],
        stages=[
            Stage(
                id="test_icmpv6_time_exceeded_link_local_traffic_punted_to_cpu_mid_queue",
                steps=[
                    create_longevity_step(duration=60),
                ],
            ),
        ],
        snapshot_checks=[
            SnapshotHealthCheck(
                name=hc_types.CheckName.CPU_QUEUE_CHECK,
                input_json=thrift_to_json(
                    hc_types.CpuQueueHealthCheckIn(
                        active_queues=[mid_queue],
                        no_discard_queues=[high_queue],
                        active_min_out_pps_per_queue={low_queue: 10},
                    )
                ),
            ),
        ],
    )

    # ICMPv6 Non-NDP with Global Addresses and DSCP 48 - Punted to MID queue
    test_icmpv6_echo_request_global_dscp48_traffic_punted_to_cpu_mid_queue_playbook = Playbook(
        name="test_icmpv6_echo_request_global_dscp48_traffic_punted_to_cpu_mid_queue",
        traffic_items_to_start=[
            "TEST_ICMPV6_ECHO_REQUEST_GLOBAL_DSCP48_TRAFFIC",
            "BGP_PREFIX_TRAFFIC",
        ],
        stages=[
            Stage(
                id="test_icmpv6_echo_request_global_dscp48_traffic_punted_to_cpu_mid_queue",
                steps=[
                    create_longevity_step(duration=60),
                ],
            ),
        ],
        snapshot_checks=[
            SnapshotHealthCheck(
                name=hc_types.CheckName.CPU_QUEUE_CHECK,
                input_json=thrift_to_json(
                    hc_types.CpuQueueHealthCheckIn(
                        active_queues=[mid_queue],
                        no_discard_queues=[high_queue],
                        active_min_out_pps_per_queue={low_queue: 10},
                    )
                ),
            ),
        ],
    )

    test_icmpv6_echo_reply_global_dscp48_traffic_punted_to_cpu_mid_queue_playbook = Playbook(
        name="test_icmpv6_echo_reply_global_dscp48_traffic_punted_to_cpu_mid_queue",
        traffic_items_to_start=[
            "TEST_ICMPV6_ECHO_REPLY_GLOBAL_DSCP48_TRAFFIC",
            "BGP_PREFIX_TRAFFIC",
        ],
        stages=[
            Stage(
                id="test_icmpv6_echo_reply_global_dscp48_traffic_punted_to_cpu_mid_queue",
                steps=[
                    create_longevity_step(duration=60),
                ],
            ),
        ],
        snapshot_checks=[
            SnapshotHealthCheck(
                name=hc_types.CheckName.CPU_QUEUE_CHECK,
                input_json=thrift_to_json(
                    hc_types.CpuQueueHealthCheckIn(
                        active_queues=[mid_queue],
                        no_discard_queues=[high_queue],
                        active_min_out_pps_per_queue={low_queue: 10},
                    )
                ),
            ),
        ],
    )

    test_icmpv6_dest_unreachable_global_dscp48_traffic_punted_to_cpu_mid_queue_playbook = Playbook(
        name="test_icmpv6_dest_unreachable_global_dscp48_traffic_punted_to_cpu_mid_queue",
        traffic_items_to_start=[
            "TEST_ICMPV6_DEST_UNREACHABLE_GLOBAL_DSCP48_TRAFFIC",
            "BGP_PREFIX_TRAFFIC",
        ],
        stages=[
            Stage(
                id="test_icmpv6_dest_unreachable_global_dscp48_traffic_punted_to_cpu_mid_queue",
                steps=[
                    create_longevity_step(duration=60),
                ],
            ),
        ],
        snapshot_checks=[
            SnapshotHealthCheck(
                name=hc_types.CheckName.CPU_QUEUE_CHECK,
                input_json=thrift_to_json(
                    hc_types.CpuQueueHealthCheckIn(
                        active_queues=[mid_queue],
                        no_discard_queues=[high_queue],
                        active_min_out_pps_per_queue={low_queue: 10},
                    )
                ),
            ),
        ],
    )

    test_icmpv6_packet_too_big_global_dscp48_traffic_punted_to_cpu_mid_queue_playbook = Playbook(
        name="test_icmpv6_packet_too_big_global_dscp48_traffic_punted_to_cpu_mid_queue",
        traffic_items_to_start=[
            "TEST_ICMPV6_PACKET_TOO_BIG_GLOBAL_DSCP48_TRAFFIC",
            "BGP_PREFIX_TRAFFIC",
        ],
        stages=[
            Stage(
                id="test_icmpv6_packet_too_big_global_dscp48_traffic_punted_to_cpu_mid_queue",
                steps=[
                    create_longevity_step(duration=60),
                ],
            ),
        ],
        snapshot_checks=[
            SnapshotHealthCheck(
                name=hc_types.CheckName.CPU_QUEUE_CHECK,
                input_json=thrift_to_json(
                    hc_types.CpuQueueHealthCheckIn(
                        active_queues=[mid_queue],
                        no_discard_queues=[high_queue],
                        active_min_out_pps_per_queue={low_queue: 10},
                    )
                ),
            ),
        ],
    )

    test_icmpv6_time_exceeded_global_dscp48_traffic_punted_to_cpu_mid_queue_playbook = Playbook(
        name="test_icmpv6_time_exceeded_global_dscp48_traffic_punted_to_cpu_mid_queue",
        traffic_items_to_start=[
            "TEST_ICMPV6_TIME_EXCEEDED_GLOBAL_DSCP48_TRAFFIC",
            "BGP_PREFIX_TRAFFIC",
        ],
        stages=[
            Stage(
                id="test_icmpv6_time_exceeded_global_dscp48_traffic_punted_to_cpu_mid_queue",
                steps=[
                    create_longevity_step(duration=60),
                ],
            ),
        ],
        snapshot_checks=[
            SnapshotHealthCheck(
                name=hc_types.CheckName.CPU_QUEUE_CHECK,
                input_json=thrift_to_json(
                    hc_types.CpuQueueHealthCheckIn(
                        active_queues=[mid_queue],
                        no_discard_queues=[high_queue],
                        active_min_out_pps_per_queue={low_queue: 10},
                    )
                ),
            ),
        ],
    )

    # Complex UNH playbooks - require ixia_downlink_interface
    test_fboss_cpu_remote_subnet_unh_playbook = Playbook(
        postchecks=[
            PointInTimeHealthCheck(
                name=hc_types.CheckName.IXIA_PACKET_LOSS_CHECK,
                input_json=thrift_to_json(
                    hc_types.IxiaPacketLossHealthCheckIn(
                        clear_traffic_stats=True,
                    )
                ),
            ),
            PointInTimeHealthCheck(
                name=hc_types.CheckName.SERVICE_RESTART_CHECK,
                check_params=Params(
                    jq_params={
                        "start_time": ".test_case_start_time",
                    },
                    json_params=json.dumps(
                        {
                            "services": SERVICES_TO_MONITOR_DURING_AGENT_RESTART,
                        }
                    ),
                ),
            ),
        ],
        traffic_items_to_start=["BGP_PREFIX_TRAFFIC"],
        name=TEST_FBOSS_CPU_REMOTE_SUBNET_UNH.name,
        snapshot_checks=[
            SnapshotHealthCheck(
                name=hc_types.CheckName.CPU_QUEUE_CHECK,
                input_json=thrift_to_json(
                    hc_types.CpuQueueHealthCheckIn(
                        active_queues=[low_queue],
                        no_discard_queues=[mid_queue, high_queue],
                    )
                ),
                pre_snapshot_checkpoint_id="stage.test_fboss_cpu_remote_subnet_unh.step.disable_next_hop_egress_port.end",
                post_snapshot_checkpoint_id="stage.test_fboss_cpu_remote_subnet_unh.step.enable_next_hop_egress_port.start",
            ),
            SnapshotHealthCheck(
                name=hc_types.CheckName.CPU_QUEUE_CHECK,
                input_json=thrift_to_json(
                    hc_types.CpuQueueHealthCheckIn(
                        active_queues=[],
                        no_discard_queues=[high_queue],
                    )
                ),
                pre_snapshot_checkpoint_id="stage.test_fboss_cpu_remote_subnet_unh.step.enable_next_hop_egress_port.end",
            ),
        ],
        stages=[
            Stage(
                id="test_fboss_cpu_remote_subnet_unh",
                steps=[
                    create_custom_step(
                        params_dict={
                            "custom_step_name": "register_cpu_queue_static_route_patcher",
                            "static_route_mask": 64,
                            "next_hop_egress_port": ixia_downlink_interface,
                            "patcher_name": "cpu_queue_static_route_patcher",
                        },
                    ),
                    create_service_interruption_step(service=Service.AGENT),
                    create_service_convergence_step(),
                    create_interface_flap_step(
                        enable=False,
                        interfaces=[ixia_downlink_interface],
                        interface_flap_method=4,  # SSH_PORT_STATE_CHANGE
                        step_id="disable_next_hop_egress_port",
                    ),
                    create_longevity_step(duration=60),
                    create_interface_flap_step(
                        enable=True,
                        interfaces=[ixia_downlink_interface],
                        interface_flap_method=4,  # SSH_PORT_STATE_CHANGE
                        step_id="enable_next_hop_egress_port",
                    ),
                    create_longevity_step(duration=60),
                    Step(
                        name=StepName.REGISTER_PATCHER_STEP,
                        input_json=thrift_to_json(
                            taac_types.RegisterPatcherInput(
                                register_patcher=False,
                                name="cpu_queue_static_route_patcher",
                                config_name="agent",
                            )
                        ),
                    ),
                    create_service_interruption_step(service=Service.AGENT),
                    create_service_convergence_step(),
                ],
            )
        ],
    )

    test_fboss_cpu_remote_subnet_128_unh_playbook = Playbook(
        postchecks=[
            PointInTimeHealthCheck(
                name=hc_types.CheckName.IXIA_PACKET_LOSS_CHECK,
                input_json=thrift_to_json(
                    hc_types.IxiaPacketLossHealthCheckIn(
                        clear_traffic_stats=True,
                    )
                ),
            ),
            PointInTimeHealthCheck(
                name=hc_types.CheckName.SERVICE_RESTART_CHECK,
                check_params=Params(
                    jq_params={
                        "start_time": ".test_case_start_time",
                    },
                    json_params=json.dumps(
                        {
                            "services": SERVICES_TO_MONITOR_DURING_AGENT_RESTART,
                        }
                    ),
                ),
            ),
        ],
        traffic_items_to_start=["BGP_PREFIX_TRAFFIC"],
        name=TEST_FBOSS_CPU_REMOTE_SUBNET_128_UNH.name,
        snapshot_checks=[
            SnapshotHealthCheck(
                name=hc_types.CheckName.CPU_QUEUE_CHECK,
                input_json=thrift_to_json(
                    hc_types.CpuQueueHealthCheckIn(
                        active_queues=[low_queue],
                        no_discard_queues=[mid_queue, high_queue],
                    )
                ),
                pre_snapshot_checkpoint_id="stage.test_fboss_cpu_remote_subnet_128_unh.step.disable_next_hop_egress_port.end",
                post_snapshot_checkpoint_id="stage.test_fboss_cpu_remote_subnet_128_unh.step.enable_next_hop_egress_port.start",
            ),
            SnapshotHealthCheck(
                name=hc_types.CheckName.CPU_QUEUE_CHECK,
                input_json=thrift_to_json(
                    hc_types.CpuQueueHealthCheckIn(
                        active_queues=[],
                        no_discard_queues=[high_queue],
                    )
                ),
                pre_snapshot_checkpoint_id="stage.test_fboss_cpu_remote_subnet_128_unh.step.enable_next_hop_egress_port.end",
            ),
        ],
        stages=[
            Stage(
                id="test_fboss_cpu_remote_subnet_128_unh",
                steps=[
                    create_custom_step(
                        params_dict={
                            "custom_step_name": "register_cpu_queue_static_route_patcher",
                            "static_route_mask": 128,
                            "next_hop_egress_port": ixia_downlink_interface,
                            "patcher_name": "cpu_queue_static_route_patcher",
                        },
                    ),
                    create_service_interruption_step(service=Service.AGENT),
                    create_service_convergence_step(),
                    create_interface_flap_step(
                        enable=False,
                        interfaces=[ixia_downlink_interface],
                        interface_flap_method=4,  # SSH_PORT_STATE_CHANGE
                        step_id="disable_next_hop_egress_port",
                    ),
                    create_longevity_step(duration=60),
                    create_interface_flap_step(
                        enable=True,
                        interfaces=[ixia_downlink_interface],
                        interface_flap_method=4,  # SSH_PORT_STATE_CHANGE
                        step_id="enable_next_hop_egress_port",
                    ),
                    create_longevity_step(duration=60),
                    Step(
                        name=StepName.REGISTER_PATCHER_STEP,
                        input_json=thrift_to_json(
                            taac_types.RegisterPatcherInput(
                                register_patcher=False,
                                name="cpu_queue_static_route_patcher",
                                config_name="agent",
                            )
                        ),
                    ),
                    create_service_interruption_step(service=Service.AGENT),
                    create_service_convergence_step(),
                ],
            )
        ],
    )

    test_fboss_cpu_dir_conn_host_unh_playbook = Playbook(
        postchecks=[
            PointInTimeHealthCheck(
                name=hc_types.CheckName.IXIA_PACKET_LOSS_CHECK,
                input_json=thrift_to_json(
                    hc_types.IxiaPacketLossHealthCheckIn(
                        clear_traffic_stats=True,
                    )
                ),
            ),
            PointInTimeHealthCheck(
                name=hc_types.CheckName.SERVICE_RESTART_CHECK,
                check_params=Params(
                    jq_params={
                        "start_time": ".test_case_start_time",
                    },
                    json_params=json.dumps(
                        {
                            "services": SERVICES_TO_MONITOR_DURING_AGENT_RESTART,
                        }
                    ),
                ),
            ),
        ],
        traffic_items_to_start=["IPV6_TRAFFIC"],
        name=TEST_FBOSS_CPU_DIR_CONN_HOST_UNH.name,
        snapshot_checks=[
            SnapshotHealthCheck(
                name=hc_types.CheckName.CPU_QUEUE_CHECK,
                input_json=thrift_to_json(
                    hc_types.CpuQueueHealthCheckIn(
                        active_queues=[low_queue],
                        no_discard_queues=[mid_queue, high_queue],
                    )
                ),
                pre_snapshot_checkpoint_id="stage.test_fboss_cpu_dir_conn_host_unh.step.disable_next_hop_egress_port.end",
                post_snapshot_checkpoint_id="stage.test_fboss_cpu_dir_conn_host_unh.step.enable_next_hop_egress_port.start",
            ),
            SnapshotHealthCheck(
                name=hc_types.CheckName.CPU_QUEUE_CHECK,
                input_json=thrift_to_json(
                    hc_types.CpuQueueHealthCheckIn(
                        active_queues=[],
                        no_discard_queues=[high_queue],
                    )
                ),
                pre_snapshot_checkpoint_id="stage.test_fboss_cpu_dir_conn_host_unh.step.enable_next_hop_egress_port.end",
            ),
        ],
        stages=[
            Stage(
                id="test_fboss_cpu_dir_conn_host_unh",
                steps=[
                    create_custom_step(
                        params_dict={
                            "custom_step_name": "register_cpu_queue_static_route_patcher",
                            "static_route_mask": 64,
                            "next_hop_egress_port": ixia_downlink_interface,
                            "patcher_name": "cpu_queue_static_route_patcher",
                        },
                    ),
                    create_service_interruption_step(service=Service.AGENT),
                    create_service_convergence_step(),
                    create_interface_flap_step(
                        enable=False,
                        interfaces=[ixia_downlink_interface],
                        interface_flap_method=4,  # SSH_PORT_STATE_CHANGE
                        step_id="disable_next_hop_egress_port",
                    ),
                    create_longevity_step(duration=60),
                    create_interface_flap_step(
                        enable=True,
                        interfaces=[ixia_downlink_interface],
                        interface_flap_method=4,  # SSH_PORT_STATE_CHANGE
                        step_id="enable_next_hop_egress_port",
                    ),
                    create_longevity_step(duration=60),
                    Step(
                        name=StepName.REGISTER_PATCHER_STEP,
                        input_json=thrift_to_json(
                            taac_types.RegisterPatcherInput(
                                register_patcher=False,
                                name="cpu_queue_static_route_patcher",
                                config_name="agent",
                            )
                        ),
                    ),
                    create_service_interruption_step(service=Service.AGENT),
                    create_service_convergence_step(),
                ],
            )
        ],
    )

    return [
        longevity_playbook,
        test_cpu_mid_queue_traffic_playbook,
        test_cpu_high_queue_traffic_playbook,
        test_queue_prioritization_high_queue_no_drops_playbook,
        test_icmp_v6_request_traffic_punted_to_cpu_mid_queue_playbook,
        test_icmp_v4_echo_request_traffic_punted_to_cpu_mid_queue_playbook,
        test_icmp_v4_echo_reply_traffic_punted_to_cpu_mid_queue_playbook,
        test_icmp_v4_dest_unreachable_traffic_punted_to_cpu_mid_queue_playbook,
        test_icmp_v4_time_exceeded_traffic_punted_to_cpu_mid_queue_playbook,
        test_dhcp_v6_traffic_punted_to_cpu_mid_queue_playbook,
        test_dhcp_v4_discover_traffic_punted_to_cpu_mid_queue_playbook,
        test_dhcp_v4_discover_to_server_traffic_punted_to_cpu_mid_queue_playbook,
        test_lldp_traffic_punted_to_cpu_mid_queue_playbook,
        test_bgp_cp_traffic_punted_to_cpu_high_queue_playbook,
        test_bgp_cp_v4_traffic_punted_to_cpu_high_queue_playbook,
        test_bgp_cp_v4_dscp0_traffic_punted_to_cpu_high_queue_playbook,
        test_lacp_traffic_punted_to_cpu_high_queue_playbook,
        test_nexthop_limit_1_punted_to_cpu_low_queue_playbook,
        test_nexthop_limit_0_not_punted_to_cpu_playbook,
        test_ttl_1_ipv4_traffic_punted_to_cpu_low_queue_playbook,
        test_ttl_0_ipv4_traffic_not_punted_to_cpu_playbook,
        test_arp_traffic_punted_to_cpu_high_queue_playbook,
        test_arp_response_traffic_punted_to_cpu_high_queue_playbook,
        test_ndp_ns_multicast_traffic_punted_to_cpu_high_queue_playbook,
        test_ndp_na_multicast_traffic_punted_to_cpu_high_queue_playbook,
        test_ndp_rs_multicast_traffic_punted_to_cpu_high_queue_playbook,
        test_ndp_ra_multicast_traffic_punted_to_cpu_high_queue_playbook,
        test_icmpv6_echo_request_link_local_traffic_punted_to_cpu_mid_queue_playbook,
        test_icmpv6_echo_reply_link_local_traffic_punted_to_cpu_mid_queue_playbook,
        test_icmpv6_dest_unreachable_link_local_traffic_punted_to_cpu_mid_queue_playbook,
        test_icmpv6_packet_too_big_link_local_traffic_punted_to_cpu_mid_queue_playbook,
        test_icmpv6_time_exceeded_link_local_traffic_punted_to_cpu_mid_queue_playbook,
        test_icmpv6_echo_request_global_dscp48_traffic_punted_to_cpu_mid_queue_playbook,
        test_icmpv6_echo_reply_global_dscp48_traffic_punted_to_cpu_mid_queue_playbook,
        test_icmpv6_dest_unreachable_global_dscp48_traffic_punted_to_cpu_mid_queue_playbook,
        test_icmpv6_packet_too_big_global_dscp48_traffic_punted_to_cpu_mid_queue_playbook,
        test_icmpv6_time_exceeded_global_dscp48_traffic_punted_to_cpu_mid_queue_playbook,
        test_fboss_cpu_remote_subnet_unh_playbook,
        test_fboss_cpu_remote_subnet_128_unh_playbook,
        test_fboss_cpu_dir_conn_host_unh_playbook,
    ]
