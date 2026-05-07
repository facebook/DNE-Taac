# pyre-unsafe
import os
import typing as t

TAAC_OSS = os.environ.get("TAAC_OSS", "").lower() in ("1", "true", "yes")

# DSF health checks live under the Meta-internal taac.ai_bb subpackage
# which isn't shipped in the OSS slice.
if not TAAC_OSS:
    from taac.ai_bb.dsf.dsf_drain_state_health_check import (
        DsfDrainStateHealthCheck,
    )
    from taac.ai_bb.dsf.dsf_fabric_reachability_health_check import (
        DsfFabricReachabilityHealthCheck,
    )
    from taac.ai_bb.dsf.dsf_fsdb_session_health_check import (
        DsfFsdbSessionHealthCheck,
    )
    from taac.ai_bb.dsf.dsf_fsdb_subscriber_timestamp_health_check import (
        DsfFsdbSubscriberTimestampHealthCheck,
    )
    from taac.ai_bb.dsf.dsf_pfc_health_check import DsfPfcHealthCheck
    from taac.ai_bb.dsf.dsf_traffic_rebalance_health_check import (
        DsfTrafficRebalanceHealthCheck,
    )
from taac.health_checks.abstract_health_check import (
    AbstractDeviceHealthCheck,
    AbstractIxiaHealthCheck,
    AbstractPointInTimeHealthCheck,
    AbstractTopologyHealthCheck,
)
from taac.health_checks.abstract_snapshot_health_check import (
    AbstractSnapshotHealthCheck,
)
from taac.health_checks.device_health_checks.bgp_convergence_health_check import (
    BgpConvergenceHealthCheck,
)
from taac.health_checks.device_health_checks.bgp_fib_programming_health_check import (
    BgpFibProgrammingCheck,
)
from taac.health_checks.device_health_checks.bgp_graceful_restart_health_check import (
    BgpGracefulRestartHealthCheck,
)
from taac.health_checks.device_health_checks.bgp_multipath_next_hop_count_health_check import (
    BgpMultipathNextHopCountHealthCheck,
)
from taac.health_checks.device_health_checks.bgp_non_best_route_health_check import (
    BgpNonBestRouteHealthCheck,
)
from taac.health_checks.device_health_checks.bgp_route_count_verification_health_check import (
    BgpRouteCountVerificationHealthCheck,
)
from taac.health_checks.device_health_checks.bgp_session_health_check import (
    BgpSessionEstablishedHealthCheck,
)
from taac.health_checks.device_health_checks.bgp_stale_route_health_check import (
    BgpStaleRouteHealthCheck,
)
from taac.health_checks.device_health_checks.bgp_tcpdump_health_check import (
    BgpTcpdumpHealthCheck,
)
from taac.health_checks.device_health_checks.clear_counters_health_check import (
    ClearCountersHealthCheck,
)
# ODS-dependent; taac.internal isn't shipped in the OSS slice.
if not TAAC_OSS:
    from taac.health_checks.device_health_checks.cpu_utilization_health_check import (
        CpuUtilizationHealthCheck,
    )
from taac.health_checks.device_health_checks.device_core_dumps_health_check import (
    DeviceCoreDumpsHealthCheck,
)
from taac.health_checks.device_health_checks.dlb_resource_stickiness_health_check import (
    DlbResourceStickinessHealthCheck,
)
from taac.health_checks.device_health_checks.drain_state_health_check import (
    DrainStateHealthCheck,
)
from taac.health_checks.device_health_checks.ecmp_group_and_member_count_health_check import (
    EcmpGroupAndMemberCountHealthCheck,
)
from taac.health_checks.device_health_checks.file_exists_health_check import (
    FileExistsHealthCheck,
)
# ODS-dependent; taac.internal isn't shipped in the OSS slice.
if not TAAC_OSS:
    from taac.health_checks.device_health_checks.generic_ods_health_check import (
        GenericOdsHealthCheck,
    )
from taac.health_checks.device_health_checks.hardware_capacity_health_check import (
    HardwareCapacityHealthCheck,
)
from taac.health_checks.device_health_checks.l2_entry_threshold_health_check import (
    L2EntryThresholdHealthCheck,
)
from taac.health_checks.device_health_checks.lldp_health_check import (
    LldpHealthCheck,
)
from taac.health_checks.device_health_checks.log_parsing_health_check import (
    LogParsingHealthCheck,
)
# ODS-dependent; taac.internal isn't shipped in the OSS slice.
if not TAAC_OSS:
    from taac.health_checks.device_health_checks.memory_utilization_health_check import (
        MemoryUtilizationHealthCheck,
    )
from taac.health_checks.device_health_checks.oomd_kill_health_check import (
    OomdKillHealthCheck,
)
from taac.health_checks.device_health_checks.pfc_wd_health_check import (
    PfcWdHealthCheck,
)
from taac.health_checks.device_health_checks.port_counters_health_check import (
    PortCountersHealthCheck,
)
from taac.health_checks.device_health_checks.port_flap_health_check import (
    PortFlapHealthCheck,
)
from taac.health_checks.device_health_checks.port_queue_rate_health_check import (
    PortQueueRateHealthCheck,
)
from taac.health_checks.device_health_checks.port_speed_health_check import (
    PortSpeedHealthCheck,
)
from taac.health_checks.device_health_checks.port_state_health_check import (
    PortStateHealthCheck,
)
from taac.health_checks.device_health_checks.route_convergence_time_health_check import (
    RouteConvergenceTimeHealthCheck,
)
from taac.health_checks.device_health_checks.service_restart_health_check import (
    ServiceRestartHealthCheck,
)
from taac.health_checks.device_health_checks.system_cpu_load_average_health_check import (
    SystemCpuLoadAverageHealthCheck,
)
from taac.health_checks.device_health_checks.systemctl_active_state_health_check import (
    SystemctlActiveStateHealthCheck,
)
# ODS-dependent; taac.internal isn't shipped in the OSS slice.
if not TAAC_OSS:
    from taac.health_checks.device_health_checks.ucmp_traffic_distribution_health_check import (
        UcmpTrafficDistributionHealthCheck,
    )
# ODS-dependent; taac.internal isn't shipped in the OSS slice.
if not TAAC_OSS:
    from taac.health_checks.device_health_checks.unclean_exit_health_check import (
        UncleanExitHealthCheck,
    )
from taac.health_checks.device_health_checks.wedge_agent_configured_health_check import (
    WedgeAgentConfiguredHealthCheck,
)
from taac.health_checks.ixia_health_checks.ixia_packet_loss_health_check import (
    IxiaPacketLossHealthCheck,
)
from taac.health_checks.ixia_health_checks.ixia_port_stats_health_check import (
    IxiaPortStatsHealthCheck,
)
from taac.health_checks.ixia_health_checks.ixia_ptp_health_check import (
    IxiaPTPHealthCheck,
)
from taac.health_checks.ixia_health_checks.ixia_traffic_rate_health_check import (
    IxiaTrafficRateHealthCheck,
)
from taac.health_checks.snapshot_health_checks.bgp_peers_health_check import (
    BgpPeersHealthCheck,
)
from taac.health_checks.snapshot_health_checks.bgp_session_health_check import (
    BgpSessionHealthCheck,
)
from taac.health_checks.snapshot_health_checks.buffer_utilization_health_check import (
    BufferUtilizationHealthCheck,
)
from taac.health_checks.snapshot_health_checks.coredumps_health_check import (
    CoreDumpsHealthCheck,
)
from taac.health_checks.snapshot_health_checks.cpu_queue_health_check import (
    CpuQueueHealthCheck,
)
from taac.health_checks.snapshot_health_checks.port_channel_state_health_check import (
    PortChannelStateHealthCheck,
)
from taac.health_checks.snapshot_health_checks.port_speed_health_check import (
    PortSpeedHealtchCheck as PortSpeedSnapshotHealthCheck,
)
from taac.health_checks.snapshot_health_checks.qos_dscp_tx_queue_health_check import (
    QoSDscpTxQueueHealthCheck,
)
from taac.health_checks.topology_health_checks.ndp_health_check import (
    NdpHealthCheck,
)
from taac.health_check.health_check import types as hc_types

HealthCheck = t.Union[
    t.Type[AbstractIxiaHealthCheck],
    t.Type[AbstractDeviceHealthCheck],
    t.Type[AbstractTopologyHealthCheck],
]

# pyre-ignore
OSS_HEALTH_CHECKS: t.List[HealthCheck] = [
    IxiaPacketLossHealthCheck,
    DrainStateHealthCheck,
    # DsfDrainStateHealthCheck,  # DSF-specific (taac.ai_bb), excluded in OSS
    # DsfFabricReachabilityHealthCheck,  # DSF-specific (taac.ai_bb), excluded in OSS
    # DsfTrafficRebalanceHealthCheck,  # DSF-specific (taac.ai_bb), excluded in OSS
    # DsfFsdbSessionHealthCheck,  # DSF-specific (taac.ai_bb), excluded in OSS
    # DsfFsdbSubscriberTimestampHealthCheck,  # DSF-specific (taac.ai_bb), excluded in OSS
    NdpHealthCheck,
    IxiaPortStatsHealthCheck,
    SystemctlActiveStateHealthCheck,
    WedgeAgentConfiguredHealthCheck,
    # DsfPfcHealthCheck,  # DSF-specific (taac.ai_bb), excluded in OSS
    CoreDumpsHealthCheck,
    PortStateHealthCheck,
    LldpHealthCheck,
    IxiaTrafficRateHealthCheck,
    PfcWdHealthCheck,
    CpuQueueHealthCheck,
    # UncleanExitHealthCheck,  # ODS-dependent (taac.internal), excluded in OSS
    # CpuUtilizationHealthCheck,  # ODS-dependent (taac.internal), excluded in OSS
    # MemoryUtilizationHealthCheck,  # ODS-dependent (taac.internal), excluded in OSS
    BgpSessionEstablishedHealthCheck,
    BgpConvergenceHealthCheck,
    BgpGracefulRestartHealthCheck,
    HardwareCapacityHealthCheck,
    BgpStaleRouteHealthCheck,
    BgpNonBestRouteHealthCheck,
    BgpTcpdumpHealthCheck,
    L2EntryThresholdHealthCheck,
    # GenericOdsHealthCheck,  # ODS-dependent (taac.internal), excluded in OSS
    OomdKillHealthCheck,
    EcmpGroupAndMemberCountHealthCheck,
    DeviceCoreDumpsHealthCheck,
    FileExistsHealthCheck,
    LogParsingHealthCheck,
    BgpSessionHealthCheck,
    BgpPeersHealthCheck,
    ServiceRestartHealthCheck,
    IxiaPTPHealthCheck,
    ClearCountersHealthCheck,
    PortCountersHealthCheck,
    PortFlapHealthCheck,
    PortQueueRateHealthCheck,
    QoSDscpTxQueueHealthCheck,
    BufferUtilizationHealthCheck,
    SystemCpuLoadAverageHealthCheck,
    BgpFibProgrammingCheck,
    PortSpeedHealthCheck,
    PortSpeedSnapshotHealthCheck,
    # UcmpTrafficDistributionHealthCheck,  # ODS-dependent (taac.internal), excluded in OSS
    BgpRouteCountVerificationHealthCheck,
    BgpMultipathNextHopCountHealthCheck,
    RouteConvergenceTimeHealthCheck,
    DlbResourceStickinessHealthCheck,
    PortChannelStateHealthCheck,
]

if not TAAC_OSS:
    from taac.internal.health_checks.internal_health_checks import (
        INTERNAL_HEALTH_CHECKS,
    )
else:
    INTERNAL_HEALTH_CHECKS = []

ALL_HEALTH_CHECKS: t.List[HealthCheck] = OSS_HEALTH_CHECKS + INTERNAL_HEALTH_CHECKS

POINT_IN_TIME_HEALTH_CHECKS: t.List[HealthCheck] = [
    check
    for check in ALL_HEALTH_CHECKS
    if issubclass(check, AbstractPointInTimeHealthCheck)
]

SNAPSHOT_HEALTH_CHECKS: t.List[HealthCheck] = [
    check
    for check in ALL_HEALTH_CHECKS
    if issubclass(check, AbstractSnapshotHealthCheck)
]

NAME_TO_POINT_IN_TIME_HEALTH_CHECK: t.Dict[hc_types.CheckName, HealthCheck] = {
    health_check.CHECK_NAME: health_check
    for health_check in POINT_IN_TIME_HEALTH_CHECKS
}

HEALTH_CHECK_NAME_TO_INPUT = {
    # pyre-ignore
    health_check.CHECK_NAME: t.get_args(health_check.__orig_bases__[0])[0]
    for health_check in ALL_HEALTH_CHECKS
}


NAME_TO_HEALTH_CHECK: t.Dict[hc_types.CheckName, HealthCheck] = {
    health_check.CHECK_NAME: health_check for health_check in ALL_HEALTH_CHECKS
}
