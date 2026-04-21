# (c) Meta Platforms, Inc. and affiliates. Confidential and proprietary.

# pyre-unsafe
import typing as t

from neteng.qosdb.Cos import types as qos_types
from taac.test_as_a_config.types import Playbook


# Playbook constants - single source of truth for QoS scheduling playbook names.
# Used by both qos_scheduling_test_config.py and UTP test case definitions.
# UTP uses .name to get the playbook name string.

# Scheduling playbooks (one per ClassOfService queue)
TEST_QOS_SCHEDULING_QUEUE7_NC = Playbook(
    name="test_qos_scheduling_queue7_nc",
)
TEST_QOS_SCHEDULING_QUEUE6_ICP = Playbook(
    name="test_qos_scheduling_queue6_icp",
)
TEST_QOS_SCHEDULING_QUEUE3_GOLD = Playbook(
    name="test_qos_scheduling_queue3_gold",
)
TEST_QOS_SCHEDULING_QUEUE2_SILVER = Playbook(
    name="test_qos_scheduling_queue2_silver",
)
TEST_QOS_SCHEDULING_QUEUE1_BRONZE = Playbook(
    name="test_qos_scheduling_queue1_bronze",
)
# NCNF is not yet a first-class ClassOfService enum value, so it is not
# included in the COS_TO_SCHEDULING_PLAYBOOK dict.  The test config
# generates its playbook separately using this constant.
TEST_QOS_SCHEDULING_QUEUE0_NCNF = Playbook(
    name="test_qos_scheduling_queue0_ncnf",
)

# Per-queue congestion playbooks (one per CoS queue, same DSCP on both ports)
TEST_QOS_PER_QUEUE_CONGESTION_QUEUE7_NC = Playbook(
    name="test_qos_per_queue_congestion_queue7_nc",
)
TEST_QOS_PER_QUEUE_CONGESTION_QUEUE6_ICP = Playbook(
    name="test_qos_per_queue_congestion_queue6_icp",
)
TEST_QOS_PER_QUEUE_CONGESTION_QUEUE3_GOLD = Playbook(
    name="test_qos_per_queue_congestion_queue3_gold",
)
TEST_QOS_PER_QUEUE_CONGESTION_QUEUE2_SILVER = Playbook(
    name="test_qos_per_queue_congestion_queue2_silver",
)
TEST_QOS_PER_QUEUE_CONGESTION_QUEUE1_BRONZE = Playbook(
    name="test_qos_per_queue_congestion_queue1_bronze",
)
# NCNF is not yet a first-class ClassOfService enum value, so it is not
# included in the COS_TO_PER_QUEUE_CONGESTION_PLAYBOOK dict.
TEST_QOS_PER_QUEUE_CONGESTION_QUEUE0_NCNF = Playbook(
    name="test_qos_per_queue_congestion_queue0_ncnf",
)

# Congestion playbooks (one per priority pair)
TEST_QOS_CONGESTION_QUEUE7_NC_VS_QUEUE6_ICP = Playbook(
    name="test_qos_congestion_queue7_nc_vs_queue6_icp",
)
TEST_QOS_CONGESTION_QUEUE7_NC_VS_QUEUE3_GOLD = Playbook(
    name="test_qos_congestion_queue7_nc_vs_queue3_gold",
)
TEST_QOS_CONGESTION_QUEUE7_NC_VS_QUEUE2_SILVER = Playbook(
    name="test_qos_congestion_queue7_nc_vs_queue2_silver",
)
TEST_QOS_CONGESTION_QUEUE7_NC_VS_QUEUE1_BRONZE = Playbook(
    name="test_qos_congestion_queue7_nc_vs_queue1_bronze",
)
TEST_QOS_CONGESTION_QUEUE6_ICP_VS_QUEUE3_GOLD = Playbook(
    name="test_qos_congestion_queue6_icp_vs_queue3_gold",
)
TEST_QOS_CONGESTION_QUEUE6_ICP_VS_QUEUE2_SILVER = Playbook(
    name="test_qos_congestion_queue6_icp_vs_queue2_silver",
)
TEST_QOS_CONGESTION_QUEUE6_ICP_VS_QUEUE1_BRONZE = Playbook(
    name="test_qos_congestion_queue6_icp_vs_queue1_bronze",
)
TEST_QOS_CONGESTION_QUEUE3_GOLD_VS_QUEUE2_SILVER = Playbook(
    name="test_qos_congestion_queue3_gold_vs_queue2_silver",
)
TEST_QOS_CONGESTION_QUEUE3_GOLD_VS_QUEUE1_BRONZE = Playbook(
    name="test_qos_congestion_queue3_gold_vs_queue1_bronze",
)
TEST_QOS_CONGESTION_QUEUE2_SILVER_VS_QUEUE1_BRONZE = Playbook(
    name="test_qos_congestion_queue2_silver_vs_queue1_bronze",
)

# Multi-queue congestion playbooks (multiple queues congested simultaneously)
# Each test sends congestion traffic on multiple lower-priority queues while
# the highest-priority queue of the group carries the 3 existing traffic items.
TEST_QOS_MULTI_CONGESTION_NC_VS_ICP_GOLD = Playbook(
    name="test_qos_multi_congestion_nc_vs_icp_gold",
)
TEST_QOS_MULTI_CONGESTION_NC_VS_ICP_GOLD_SILVER = Playbook(
    name="test_qos_multi_congestion_nc_vs_icp_gold_silver",
)
TEST_QOS_MULTI_CONGESTION_NC_VS_ICP_GOLD_SILVER_BRONZE = Playbook(
    name="test_qos_multi_congestion_nc_vs_icp_gold_silver_bronze",
)
TEST_QOS_MULTI_CONGESTION_ICP_VS_GOLD_SILVER = Playbook(
    name="test_qos_multi_congestion_icp_vs_gold_silver",
)
TEST_QOS_MULTI_CONGESTION_ICP_VS_GOLD_SILVER_BRONZE = Playbook(
    name="test_qos_multi_congestion_icp_vs_gold_silver_bronze",
)
TEST_QOS_MULTI_CONGESTION_GOLD_VS_SILVER_BRONZE = Playbook(
    name="test_qos_multi_congestion_gold_vs_silver_bronze",
)

# Lookup dict: (priority_cos, tuple_of_congested_cos) → multi-congestion Playbook.
COS_MULTI_CONGESTION_PLAYBOOK: t.Dict[
    t.Tuple[qos_types.ClassOfService, t.Tuple[qos_types.ClassOfService, ...]], Playbook
] = {
    (
        qos_types.ClassOfService.NC,
        (qos_types.ClassOfService.ICP, qos_types.ClassOfService.GOLD),
    ): TEST_QOS_MULTI_CONGESTION_NC_VS_ICP_GOLD,
    (
        qos_types.ClassOfService.NC,
        (
            qos_types.ClassOfService.ICP,
            qos_types.ClassOfService.GOLD,
            qos_types.ClassOfService.SILVER,
        ),
    ): TEST_QOS_MULTI_CONGESTION_NC_VS_ICP_GOLD_SILVER,
    (
        qos_types.ClassOfService.NC,
        (
            qos_types.ClassOfService.ICP,
            qos_types.ClassOfService.GOLD,
            qos_types.ClassOfService.SILVER,
            qos_types.ClassOfService.BRONZE,
        ),
    ): TEST_QOS_MULTI_CONGESTION_NC_VS_ICP_GOLD_SILVER_BRONZE,
    (
        qos_types.ClassOfService.ICP,
        (qos_types.ClassOfService.GOLD, qos_types.ClassOfService.SILVER),
    ): TEST_QOS_MULTI_CONGESTION_ICP_VS_GOLD_SILVER,
    (
        qos_types.ClassOfService.ICP,
        (
            qos_types.ClassOfService.GOLD,
            qos_types.ClassOfService.SILVER,
            qos_types.ClassOfService.BRONZE,
        ),
    ): TEST_QOS_MULTI_CONGESTION_ICP_VS_GOLD_SILVER_BRONZE,
    (
        qos_types.ClassOfService.GOLD,
        (qos_types.ClassOfService.SILVER, qos_types.ClassOfService.BRONZE),
    ): TEST_QOS_MULTI_CONGESTION_GOLD_VS_SILVER_BRONZE,
}


# Single-queue congestion playbooks (one queue congested at a time via the
# per-queue congestion traffic item from the third port).
# The 3 existing items run on NC (highest priority), while one per-queue
# congestion item overloads the target queue.
TEST_QOS_SINGLE_CONGESTION_QUEUE6_ICP = Playbook(
    name="test_qos_single_congestion_queue6_icp",
)
TEST_QOS_SINGLE_CONGESTION_QUEUE3_GOLD = Playbook(
    name="test_qos_single_congestion_queue3_gold",
)
TEST_QOS_SINGLE_CONGESTION_QUEUE2_SILVER = Playbook(
    name="test_qos_single_congestion_queue2_silver",
)
TEST_QOS_SINGLE_CONGESTION_QUEUE1_BRONZE = Playbook(
    name="test_qos_single_congestion_queue1_bronze",
)

# Lookup dict: congested_cos → single-queue congestion Playbook constant.
COS_TO_SINGLE_CONGESTION_PLAYBOOK: t.Dict[qos_types.ClassOfService, Playbook] = {
    qos_types.ClassOfService.ICP: TEST_QOS_SINGLE_CONGESTION_QUEUE6_ICP,
    qos_types.ClassOfService.GOLD: TEST_QOS_SINGLE_CONGESTION_QUEUE3_GOLD,
    qos_types.ClassOfService.SILVER: TEST_QOS_SINGLE_CONGESTION_QUEUE2_SILVER,
    qos_types.ClassOfService.BRONZE: TEST_QOS_SINGLE_CONGESTION_QUEUE1_BRONZE,
}


# Lookup dict: ClassOfService → scheduling Playbook constant.
COS_TO_SCHEDULING_PLAYBOOK: t.Dict[qos_types.ClassOfService, Playbook] = {
    qos_types.ClassOfService.NC: TEST_QOS_SCHEDULING_QUEUE7_NC,
    qos_types.ClassOfService.ICP: TEST_QOS_SCHEDULING_QUEUE6_ICP,
    qos_types.ClassOfService.GOLD: TEST_QOS_SCHEDULING_QUEUE3_GOLD,
    qos_types.ClassOfService.SILVER: TEST_QOS_SCHEDULING_QUEUE2_SILVER,
    qos_types.ClassOfService.BRONZE: TEST_QOS_SCHEDULING_QUEUE1_BRONZE,
}

# Lookup dict: (priority_cos, congested_cos) → congestion Playbook constant.
COS_PAIR_TO_CONGESTION_PLAYBOOK: t.Dict[
    t.Tuple[qos_types.ClassOfService, qos_types.ClassOfService], Playbook
] = {
    (
        qos_types.ClassOfService.NC,
        qos_types.ClassOfService.ICP,
    ): TEST_QOS_CONGESTION_QUEUE7_NC_VS_QUEUE6_ICP,
    (
        qos_types.ClassOfService.NC,
        qos_types.ClassOfService.GOLD,
    ): TEST_QOS_CONGESTION_QUEUE7_NC_VS_QUEUE3_GOLD,
    (
        qos_types.ClassOfService.NC,
        qos_types.ClassOfService.SILVER,
    ): TEST_QOS_CONGESTION_QUEUE7_NC_VS_QUEUE2_SILVER,
    (
        qos_types.ClassOfService.NC,
        qos_types.ClassOfService.BRONZE,
    ): TEST_QOS_CONGESTION_QUEUE7_NC_VS_QUEUE1_BRONZE,
    (
        qos_types.ClassOfService.ICP,
        qos_types.ClassOfService.GOLD,
    ): TEST_QOS_CONGESTION_QUEUE6_ICP_VS_QUEUE3_GOLD,
    (
        qos_types.ClassOfService.ICP,
        qos_types.ClassOfService.SILVER,
    ): TEST_QOS_CONGESTION_QUEUE6_ICP_VS_QUEUE2_SILVER,
    (
        qos_types.ClassOfService.ICP,
        qos_types.ClassOfService.BRONZE,
    ): TEST_QOS_CONGESTION_QUEUE6_ICP_VS_QUEUE1_BRONZE,
    (
        qos_types.ClassOfService.GOLD,
        qos_types.ClassOfService.SILVER,
    ): TEST_QOS_CONGESTION_QUEUE3_GOLD_VS_QUEUE2_SILVER,
    (
        qos_types.ClassOfService.GOLD,
        qos_types.ClassOfService.BRONZE,
    ): TEST_QOS_CONGESTION_QUEUE3_GOLD_VS_QUEUE1_BRONZE,
    (
        qos_types.ClassOfService.SILVER,
        qos_types.ClassOfService.BRONZE,
    ): TEST_QOS_CONGESTION_QUEUE2_SILVER_VS_QUEUE1_BRONZE,
}

# Lookup dict: ClassOfService → per-queue congestion Playbook constant.
COS_TO_PER_QUEUE_CONGESTION_PLAYBOOK: t.Dict[qos_types.ClassOfService, Playbook] = {
    qos_types.ClassOfService.NC: TEST_QOS_PER_QUEUE_CONGESTION_QUEUE7_NC,
    qos_types.ClassOfService.ICP: TEST_QOS_PER_QUEUE_CONGESTION_QUEUE6_ICP,
    qos_types.ClassOfService.GOLD: TEST_QOS_PER_QUEUE_CONGESTION_QUEUE3_GOLD,
    qos_types.ClassOfService.SILVER: TEST_QOS_PER_QUEUE_CONGESTION_QUEUE2_SILVER,
    qos_types.ClassOfService.BRONZE: TEST_QOS_PER_QUEUE_CONGESTION_QUEUE1_BRONZE,
}


# =========================================================================
# Programmatically generated playbook constants for remaining test categories.
# Uses _COS_INFO to generate names matching the UTP test case conventions.
# =========================================================================
_COS_INFO: t.List[t.Tuple[qos_types.ClassOfService, str, str]] = [
    (qos_types.ClassOfService.NC, "queue7", "nc"),
    (qos_types.ClassOfService.ICP, "queue6", "icp"),
    (qos_types.ClassOfService.GOLD, "queue3", "gold"),
    (qos_types.ClassOfService.SILVER, "queue2", "silver"),
    (qos_types.ClassOfService.BRONZE, "queue1", "bronze"),
]

# ---------------------------------------------------------------------------
# Microburst congestion playbooks (one per CoS, same DSCP on both ports,
# Port 1 microburst + Port 2 continuous)
# ---------------------------------------------------------------------------
COS_TO_MICROBURST_CONGESTION_PLAYBOOK: t.Dict[qos_types.ClassOfService, Playbook] = {
    cos: Playbook(name=f"test_qos_microburst_congestion_{queue}_{name}")
    for cos, queue, name in _COS_INFO
}
TEST_QOS_MICROBURST_CONGESTION_QUEUE0_NCNF = Playbook(
    name="test_qos_microburst_congestion_queue0_ncnf",
)

# ---------------------------------------------------------------------------
# 2-Queue Priority Congestion — Higher Priority Bursty
# ---------------------------------------------------------------------------
COS_PAIR_TO_CONGESTION_HI_BURST_PLAYBOOK: t.Dict[
    t.Tuple[qos_types.ClassOfService, qos_types.ClassOfService], Playbook
] = {
    (hi_cos, lo_cos): Playbook(
        name=f"test_qos_congestion_hi_burst_{hi_q}_{hi_n}_vs_{lo_q}_{lo_n}"
    )
    for i, (hi_cos, hi_q, hi_n) in enumerate(_COS_INFO)
    for lo_cos, lo_q, lo_n in _COS_INFO[i + 1 :]
}

# ---------------------------------------------------------------------------
# 2-Queue Priority Congestion — Lower Priority Bursty
# ---------------------------------------------------------------------------
COS_PAIR_TO_CONGESTION_LO_BURST_PLAYBOOK: t.Dict[
    t.Tuple[qos_types.ClassOfService, qos_types.ClassOfService], Playbook
] = {
    (hi_cos, lo_cos): Playbook(
        name=f"test_qos_congestion_lo_burst_{hi_q}_{hi_n}_vs_{lo_q}_{lo_n}"
    )
    for i, (hi_cos, hi_q, hi_n) in enumerate(_COS_INFO)
    for lo_cos, lo_q, lo_n in _COS_INFO[i + 1 :]
}

# ---------------------------------------------------------------------------
# 3-Queue Priority Congestion — Continuous
# ---------------------------------------------------------------------------
COS_TRIPLE_TO_3Q_CONGESTION_PLAYBOOK: t.Dict[
    t.Tuple[
        qos_types.ClassOfService,
        qos_types.ClassOfService,
        qos_types.ClassOfService,
    ],
    Playbook,
] = {
    (hi_cos, mid_cos, lo_cos): Playbook(
        name=f"test_qos_3q_congestion_{hi_q}_{hi_n}_vs_{mid_q}_{mid_n}_vs_{lo_q}_{lo_n}"
    )
    for i, (hi_cos, hi_q, hi_n) in enumerate(_COS_INFO)
    for j, (mid_cos, mid_q, mid_n) in enumerate(_COS_INFO[i + 1 :], start=i + 1)
    for lo_cos, lo_q, lo_n in _COS_INFO[j + 1 :]
}

# ---------------------------------------------------------------------------
# 3-Queue Priority Congestion — Highest Bursty
# ---------------------------------------------------------------------------
COS_TRIPLE_TO_3Q_HI_BURST_PLAYBOOK: t.Dict[
    t.Tuple[
        qos_types.ClassOfService,
        qos_types.ClassOfService,
        qos_types.ClassOfService,
    ],
    Playbook,
] = {
    (hi_cos, mid_cos, lo_cos): Playbook(
        name=f"test_qos_3q_congestion_hi_burst_{hi_q}_{hi_n}_vs_{mid_q}_{mid_n}_vs_{lo_q}_{lo_n}"
    )
    for i, (hi_cos, hi_q, hi_n) in enumerate(_COS_INFO)
    for j, (mid_cos, mid_q, mid_n) in enumerate(_COS_INFO[i + 1 :], start=i + 1)
    for lo_cos, lo_q, lo_n in _COS_INFO[j + 1 :]
}

# ---------------------------------------------------------------------------
# 3-Queue Priority Congestion — Lowest Bursty
# ---------------------------------------------------------------------------
COS_TRIPLE_TO_3Q_LO_BURST_PLAYBOOK: t.Dict[
    t.Tuple[
        qos_types.ClassOfService,
        qos_types.ClassOfService,
        qos_types.ClassOfService,
    ],
    Playbook,
] = {
    (hi_cos, mid_cos, lo_cos): Playbook(
        name=f"test_qos_3q_congestion_lo_burst_{hi_q}_{hi_n}_vs_{mid_q}_{mid_n}_vs_{lo_q}_{lo_n}"
    )
    for i, (hi_cos, hi_q, hi_n) in enumerate(_COS_INFO)
    for j, (mid_cos, mid_q, mid_n) in enumerate(_COS_INFO[i + 1 :], start=i + 1)
    for lo_cos, lo_q, lo_n in _COS_INFO[j + 1 :]
}

# ---------------------------------------------------------------------------
# Multi-Port Single-Queue Congestion
# ---------------------------------------------------------------------------
COS_TO_MULTI_PORT_CONGESTION_PLAYBOOK: t.Dict[qos_types.ClassOfService, Playbook] = {
    cos: Playbook(name=f"test_qos_multi_port_congestion_{queue}_{name}")
    for cos, queue, name in _COS_INFO
}
TEST_QOS_MULTI_PORT_CONGESTION_QUEUE0_NCNF = Playbook(
    name="test_qos_multi_port_congestion_queue0_ncnf",
)

# ---------------------------------------------------------------------------
# Multi-Port 2-Queue Congestion
# ---------------------------------------------------------------------------
COS_PAIR_TO_MULTI_PORT_2Q_PLAYBOOK: t.Dict[
    t.Tuple[qos_types.ClassOfService, qos_types.ClassOfService], Playbook
] = {
    (hi_cos, lo_cos): Playbook(
        name=f"test_qos_multi_port_2q_congestion_{hi_q}_{hi_n}_vs_{lo_q}_{lo_n}"
    )
    for i, (hi_cos, hi_q, hi_n) in enumerate(_COS_INFO)
    for lo_cos, lo_q, lo_n in _COS_INFO[i + 1 :]
}
