# pyre-unsafe
import json
import typing as t

from ixia.ixia import types as ixia_types
from taac.constants import (
    BGP_PORT,
    BROADCAST_DST_MAC_ADDRESS,
    DEFAULT_SRC_MAC_ADDRESS,
    DHCPV4_BROADCAST_ADDR,
    DHCPV4_CLIENT_PORT,
    DHCPV4_RELAY_SERVER_ADDR,
    DHCPV4_SERVER_PORT,
    DHCPV6_MULTICAST_ADDR,
    DHCPV6_RELAY_PORT,
    DHCPV6_SERVER_MULTICAST_ADDR,
    DHCPV6_SERVER_PORT,
    ICMPV4_TYPE_DEST_UNREACHABLE,
    ICMPV4_TYPE_ECHO_REPLY,
    ICMPV4_TYPE_ECHO_REQUEST,
    ICMPV4_TYPE_TIME_EXCEEDED,
    ICMPV6_TYPE_DEST_UNREACHABLE,
    ICMPV6_TYPE_ECHO_REPLY,
    ICMPV6_TYPE_ECHO_REQUEST,
    ICMPV6_TYPE_NA,
    ICMPV6_TYPE_NS,
    ICMPV6_TYPE_PACKET_TOO_BIG,
    ICMPV6_TYPE_RA,
    ICMPV6_TYPE_RS,
    ICMPV6_TYPE_TIME_EXCEEDED,
    LACP_DEST_MULTICAST_MAC,
    LLDP_DEST_MULTICAST_MAC,
    NDP_ALL_NODES_MULTICAST_IPV6,
    NDP_ALL_NODES_MULTICAST_MAC,
    NDP_ALL_ROUTERS_MULTICAST_IPV6,
    NDP_ALL_ROUTERS_MULTICAST_MAC,
    NDP_DSCP_48_TRAFFIC_CLASS,
    NDP_IXIA_LINK_LOCAL_IPV6,
    NDP_SOLICITED_NODE_MULTICAST_IPV6,
    NDP_SOLICITED_NODE_MULTICAST_MAC,
    RDMA_PORT,
)
from taac.utils.packet_header_utils import (
    create_field,
    create_packet_header,
)
from taac.test_as_a_config import types as taac_types


#############################################################
#                        Raw Traffic                        #
#############################################################


def create_generic_pfc_pause_packet_headers(
    priority_enable_vector_single_value: int,
    pfc_queue: int,
) -> t.List[taac_types.PacketHeader]:
    """
    Creates PFC pause packet headers with specific queue settings.

    Args:
        priority_enable_vector_single_value: Integer value for the priority enable vector
            that determines which priorities are enabled for flow control
        pfc_queue: Integer (0-7) specifying which queue to pause (set to "ffff")
            while all other queues are set to 0

    Returns:
        PFC pause packet headers
    """
    return [
        create_packet_header(
            stack_regex="pfcPause",
            append_to_stack_regex="^ethernet$",
            fields=[
                create_field(
                    field_regex="priority_enable_vector",
                    field_attrs={
                        "SingleValue": priority_enable_vector_single_value,
                    },
                ),
                *[
                    create_field(
                        field_regex=f"PFC Queue {i}",
                        field_attrs={"SingleValue": "ffff" if i == pfc_queue else 0},
                    )
                    for i in range(8)
                ],
            ],
        ),
        create_packet_header(
            stack_regex="^ethernet$",
            remove_from_stack=True,
        ),
    ]


# Basic PFC pause packet headers matching configerator version
PFC_PAUSE_PACKET_HEADERS: t.List[taac_types.PacketHeader] = [
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="pfcPause", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(
                    regex="priority_enable_vector",
                ),
                attrs_json=json.dumps(
                    {
                        "SingleValue": 4,
                    }
                ),
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="PFC Queue 0"),
                attrs_json=json.dumps(
                    {
                        "SingleValue": 0,
                    }
                ),
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="PFC Queue 2"),
                attrs_json=json.dumps(
                    {
                        "SingleValue": "ffff",
                    }
                ),
            ),
        ],
        append_to_query=ixia_types.Query(
            regex="^ethernet$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
    ),
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="^ethernet$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        remove_from_stack=True,
    ),
]

TC2_PFC_PAUSE_PACKET_HEADERS = create_generic_pfc_pause_packet_headers(
    priority_enable_vector_single_value=4,
    pfc_queue=2,
)

TC6_PFC_PAUSE_PACKET_HEADERS = create_generic_pfc_pause_packet_headers(
    priority_enable_vector_single_value=40,
    pfc_queue=6,
)

LLDP_TRAFFIC_PACKET_HEADERS: t.List[taac_types.PacketHeader] = [
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="^ethernet$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="Destination MAC Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "increment",
                        "StartValue": LLDP_DEST_MULTICAST_MAC,
                        "StepValue": "00:00:00:00:00:00",
                        "CountValue": 1,
                    }
                ),
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="Source MAC Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "increment",
                        "StartValue": DEFAULT_SRC_MAC_ADDRESS,
                        "StepValue": "00:00:00:00:00:00",
                        "CountValue": 1,
                    }
                ),
            ),
        ],
    ),
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="^lldp$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        append_to_query=ixia_types.Query(
            regex="^ethernet$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
    ),
]


ICMP_V6_REQUEST_TRAFFIC_PACKET_HEADERS: t.List[taac_types.PacketHeader] = [
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="^ethernet$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="Destination MAC Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "increment",
                        "StepValue": "00:00:00:00:00:00",
                        "CountValue": 1,
                    }
                ),
                references={
                    "StartValue": taac_types.Reference(
                        type=taac_types.ReferenceType.DST_MAC_ADDRESS
                    ),
                },
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="Source MAC Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "increment",
                        "StartValue": DEFAULT_SRC_MAC_ADDRESS,
                        "StepValue": "00:00:00:00:00:00",
                        "CountValue": 1,
                    }
                ),
            ),
        ],
    ),
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="^ipv6$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        append_to_query=ixia_types.Query(
            regex="^ethernet$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="Source Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "increment",
                        "StepValue": "::1",
                        "CountValue": 1,
                    }
                ),
                references={
                    "StartValue": taac_types.Reference(
                        type=taac_types.ReferenceType.SRC_IPV6_ADDRESS
                    ),
                },
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="Destination Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "valueList",
                    }
                ),
                references={
                    "ValueList": taac_types.Reference(
                        type=taac_types.ReferenceType.DST_GATEWAY_IPV6_ADDRESS,
                        data_type=taac_types.DataType.LIST,
                    ),
                },
            ),
        ],
    ),
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="icmpv6", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        append_to_query=ixia_types.Query(
            regex="ipv6", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
    ),
]

ICMP_V4_ECHO_REQUEST_TRAFFIC_PACKET_HEADERS: t.List[taac_types.PacketHeader] = [
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="^ethernet$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="Destination MAC Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "increment",
                        "StepValue": "00:00:00:00:00:00",
                        "CountValue": 1,
                    }
                ),
                references={
                    "StartValue": taac_types.Reference(
                        type=taac_types.ReferenceType.DST_MAC_ADDRESS
                    ),
                },
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="Source MAC Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "increment",
                        "StartValue": DEFAULT_SRC_MAC_ADDRESS,
                        "StepValue": "00:00:00:00:00:00",
                        "CountValue": 1,
                    }
                ),
            ),
        ],
    ),
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="^ipv4$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        append_to_query=ixia_types.Query(
            regex="^ethernet$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="Source Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "increment",
                        "StepValue": "0.0.0.1",
                        "CountValue": 1,
                    }
                ),
                references={
                    "StartValue": taac_types.Reference(
                        type=taac_types.ReferenceType.SRC_IPV4_ADDRESS,
                        device_group_index=1,
                    ),
                },
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="Destination Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "valueList",
                    }
                ),
                references={
                    "ValueList": taac_types.Reference(
                        type=taac_types.ReferenceType.DST_GATEWAY_IPV4_ADDRESS,
                        device_group_index=1,
                        data_type=taac_types.DataType.LIST,
                    ),
                },
            ),
        ],
    ),
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="icmpv1", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        append_to_query=ixia_types.Query(
            regex="ipv4", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="Type"),
                attrs_json=json.dumps(
                    {
                        "SingleValue": str(ICMPV4_TYPE_ECHO_REQUEST),
                    }
                ),
            ),
        ],
    ),
]

ICMP_V4_ECHO_REPLY_TRAFFIC_PACKET_HEADERS: t.List[taac_types.PacketHeader] = [
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="^ethernet$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="Destination MAC Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "increment",
                        "StepValue": "00:00:00:00:00:00",
                        "CountValue": 1,
                    }
                ),
                references={
                    "StartValue": taac_types.Reference(
                        type=taac_types.ReferenceType.DST_MAC_ADDRESS
                    ),
                },
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="Source MAC Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "increment",
                        "StartValue": DEFAULT_SRC_MAC_ADDRESS,
                        "StepValue": "00:00:00:00:00:00",
                        "CountValue": 1,
                    }
                ),
            ),
        ],
    ),
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="^ipv4$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        append_to_query=ixia_types.Query(
            regex="^ethernet$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="Source Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "increment",
                        "StepValue": "0.0.0.1",
                        "CountValue": 1,
                    }
                ),
                references={
                    "StartValue": taac_types.Reference(
                        type=taac_types.ReferenceType.SRC_IPV4_ADDRESS,
                        device_group_index=1,
                    ),
                },
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="Destination Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "valueList",
                    }
                ),
                references={
                    "ValueList": taac_types.Reference(
                        type=taac_types.ReferenceType.DST_GATEWAY_IPV4_ADDRESS,
                        device_group_index=1,
                        data_type=taac_types.DataType.LIST,
                    ),
                },
            ),
        ],
    ),
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="icmpv1", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        append_to_query=ixia_types.Query(
            regex="ipv4", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="Type"),
                attrs_json=json.dumps(
                    {
                        "SingleValue": str(ICMPV4_TYPE_ECHO_REPLY),
                    }
                ),
            ),
        ],
    ),
]

ICMP_V4_DEST_UNREACHABLE_TRAFFIC_PACKET_HEADERS: t.List[taac_types.PacketHeader] = [
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="^ethernet$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="Destination MAC Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "increment",
                        "StepValue": "00:00:00:00:00:00",
                        "CountValue": 1,
                    }
                ),
                references={
                    "StartValue": taac_types.Reference(
                        type=taac_types.ReferenceType.DST_MAC_ADDRESS
                    ),
                },
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="Source MAC Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "increment",
                        "StartValue": DEFAULT_SRC_MAC_ADDRESS,
                        "StepValue": "00:00:00:00:00:00",
                        "CountValue": 1,
                    }
                ),
            ),
        ],
    ),
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="^ipv4$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        append_to_query=ixia_types.Query(
            regex="^ethernet$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="Source Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "increment",
                        "StepValue": "0.0.0.1",
                        "CountValue": 1,
                    }
                ),
                references={
                    "StartValue": taac_types.Reference(
                        type=taac_types.ReferenceType.SRC_IPV4_ADDRESS,
                        device_group_index=1,
                    ),
                },
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="Destination Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "valueList",
                    }
                ),
                references={
                    "ValueList": taac_types.Reference(
                        type=taac_types.ReferenceType.DST_GATEWAY_IPV4_ADDRESS,
                        device_group_index=1,
                        data_type=taac_types.DataType.LIST,
                    ),
                },
            ),
        ],
    ),
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="icmpv1", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        append_to_query=ixia_types.Query(
            regex="ipv4", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="Type"),
                attrs_json=json.dumps(
                    {
                        "SingleValue": str(ICMPV4_TYPE_DEST_UNREACHABLE),
                    }
                ),
            ),
        ],
    ),
]

ICMP_V4_TIME_EXCEEDED_TRAFFIC_PACKET_HEADERS: t.List[taac_types.PacketHeader] = [
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="^ethernet$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="Destination MAC Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "increment",
                        "StepValue": "00:00:00:00:00:00",
                        "CountValue": 1,
                    }
                ),
                references={
                    "StartValue": taac_types.Reference(
                        type=taac_types.ReferenceType.DST_MAC_ADDRESS
                    ),
                },
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="Source MAC Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "increment",
                        "StartValue": DEFAULT_SRC_MAC_ADDRESS,
                        "StepValue": "00:00:00:00:00:00",
                        "CountValue": 1,
                    }
                ),
            ),
        ],
    ),
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="^ipv4$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        append_to_query=ixia_types.Query(
            regex="^ethernet$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="Source Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "increment",
                        "StepValue": "0.0.0.1",
                        "CountValue": 1,
                    }
                ),
                references={
                    "StartValue": taac_types.Reference(
                        type=taac_types.ReferenceType.SRC_IPV4_ADDRESS,
                        device_group_index=1,
                    ),
                },
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="Destination Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "valueList",
                    }
                ),
                references={
                    "ValueList": taac_types.Reference(
                        type=taac_types.ReferenceType.DST_GATEWAY_IPV4_ADDRESS,
                        device_group_index=1,
                        data_type=taac_types.DataType.LIST,
                    ),
                },
            ),
        ],
    ),
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="icmpv1", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        append_to_query=ixia_types.Query(
            regex="ipv4", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="Type"),
                attrs_json=json.dumps(
                    {
                        "SingleValue": str(ICMPV4_TYPE_TIME_EXCEEDED),
                    }
                ),
            ),
        ],
    ),
]

BGP_CP_TRAFFIC_PACKET_HEADERS: t.List[taac_types.PacketHeader] = [
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="^ethernet$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="Destination MAC Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "increment",
                        "StepValue": "00:00:00:00:00:00",
                        "CountValue": 1,
                    }
                ),
                references={
                    "StartValue": taac_types.Reference(
                        type=taac_types.ReferenceType.DST_MAC_ADDRESS
                    ),
                },
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="Source MAC Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "increment",
                        "StartValue": DEFAULT_SRC_MAC_ADDRESS,
                        "StepValue": "00:00:00:00:00:00",
                        "CountValue": 1,
                    }
                ),
            ),
        ],
    ),
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="^ipv6$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        append_to_query=ixia_types.Query(
            regex="^ethernet$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="Source Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "increment",
                        "StepValue": "::1",
                        "CountValue": 1,
                    }
                ),
                references={
                    "StartValue": taac_types.Reference(
                        type=taac_types.ReferenceType.SRC_IPV6_ADDRESS
                    ),
                },
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="Destination Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "valueList",
                    }
                ),
                references={
                    "ValueList": taac_types.Reference(
                        type=taac_types.ReferenceType.SRC_GATEWAY_IPV6_ADDRESS,
                        data_type=taac_types.DataType.LIST,
                    ),
                },
            ),
        ],
    ),
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="tcp", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        append_to_query=ixia_types.Query(
            regex="ipv6", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="TCP-Source-Port"),
                attrs_json=json.dumps(
                    {
                        "Auto": False,
                        "ValueType": "valueList",
                        "ValueList": [BGP_PORT],
                    }
                ),
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="TCP-Dest-Port"),
                attrs_json=json.dumps(
                    {
                        "Auto": False,
                        "SingleValue": BGP_PORT,
                    }
                ),
            ),
        ],
    ),
]

# BGP v4 CP traffic to CPU with DSCP 48 (ToS 192)
# Eth: SMAC=ixia mac, DMAC=switch mac
# IPv4: SIP=ixia v4 ip, DIP=switch v4 ip, DSCP=48
# TCP: SP=179, DP=179
BGP_CP_V4_TRAFFIC_PACKET_HEADERS: t.List[taac_types.PacketHeader] = [
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="^ethernet$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="Destination MAC Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "increment",
                        "StepValue": "00:00:00:00:00:00",
                        "CountValue": 1,
                    }
                ),
                references={
                    "StartValue": taac_types.Reference(
                        type=taac_types.ReferenceType.DST_MAC_ADDRESS
                    ),
                },
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="Source MAC Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "increment",
                        "StartValue": DEFAULT_SRC_MAC_ADDRESS,
                        "StepValue": "00:00:00:00:00:00",
                        "CountValue": 1,
                    }
                ),
            ),
        ],
    ),
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="^ipv4$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        append_to_query=ixia_types.Query(
            regex="^ethernet$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="Source Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "increment",
                        "StepValue": "0.0.0.1",
                        "CountValue": 1,
                    }
                ),
                references={
                    "StartValue": taac_types.Reference(
                        type=taac_types.ReferenceType.SRC_IPV4_ADDRESS,
                        device_group_index=1,
                    ),
                },
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="Destination Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "valueList",
                    }
                ),
                references={
                    "ValueList": taac_types.Reference(
                        type=taac_types.ReferenceType.DST_GATEWAY_IPV4_ADDRESS,
                        device_group_index=1,
                        data_type=taac_types.DataType.LIST,
                    ),
                },
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="Type of Service"),
                attrs_json=json.dumps(
                    {
                        "SingleValue": "192",
                    }
                ),
            ),
        ],
    ),
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="tcp", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        append_to_query=ixia_types.Query(
            regex="ipv4", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="TCP-Source-Port"),
                attrs_json=json.dumps(
                    {
                        "Auto": False,
                        "ValueType": "valueList",
                        "ValueList": [BGP_PORT],
                    }
                ),
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="TCP-Dest-Port"),
                attrs_json=json.dumps(
                    {
                        "Auto": False,
                        "SingleValue": BGP_PORT,
                    }
                ),
            ),
        ],
    ),
]

# BGP v4 CP traffic to CPU with DSCP 0 (ToS 0)
# Same as above but with DSCP 0 instead of 48
BGP_CP_V4_DSCP0_TRAFFIC_PACKET_HEADERS: t.List[taac_types.PacketHeader] = [
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="^ethernet$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="Destination MAC Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "increment",
                        "StepValue": "00:00:00:00:00:00",
                        "CountValue": 1,
                    }
                ),
                references={
                    "StartValue": taac_types.Reference(
                        type=taac_types.ReferenceType.DST_MAC_ADDRESS
                    ),
                },
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="Source MAC Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "increment",
                        "StartValue": DEFAULT_SRC_MAC_ADDRESS,
                        "StepValue": "00:00:00:00:00:00",
                        "CountValue": 1,
                    }
                ),
            ),
        ],
    ),
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="^ipv4$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        append_to_query=ixia_types.Query(
            regex="^ethernet$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="Source Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "increment",
                        "StepValue": "0.0.0.1",
                        "CountValue": 1,
                    }
                ),
                references={
                    "StartValue": taac_types.Reference(
                        type=taac_types.ReferenceType.SRC_IPV4_ADDRESS,
                        device_group_index=1,
                    ),
                },
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="Destination Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "valueList",
                    }
                ),
                references={
                    "ValueList": taac_types.Reference(
                        type=taac_types.ReferenceType.DST_GATEWAY_IPV4_ADDRESS,
                        device_group_index=1,
                        data_type=taac_types.DataType.LIST,
                    ),
                },
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="Type of Service"),
                attrs_json=json.dumps(
                    {
                        "SingleValue": "0",
                    }
                ),
            ),
        ],
    ),
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="tcp", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        append_to_query=ixia_types.Query(
            regex="ipv4", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="TCP-Source-Port"),
                attrs_json=json.dumps(
                    {
                        "Auto": False,
                        "ValueType": "valueList",
                        "ValueList": [BGP_PORT],
                    }
                ),
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="TCP-Dest-Port"),
                attrs_json=json.dumps(
                    {
                        "Auto": False,
                        "SingleValue": BGP_PORT,
                    }
                ),
            ),
        ],
    ),
]

DHCP_V6_TRAFFIC_PACKET_HEADERS: t.List[taac_types.PacketHeader] = [
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="^ethernet$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="Destination MAC Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "increment",
                        "StepValue": "00:00:00:00:00:00",
                        "CountValue": 1,
                    }
                ),
                references={
                    "StartValue": taac_types.Reference(
                        type=taac_types.ReferenceType.DST_MAC_ADDRESS
                    ),
                },
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="Source MAC Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "increment",
                        "StartValue": DEFAULT_SRC_MAC_ADDRESS,
                        "StepValue": "00:00:00:00:00:00",
                        "CountValue": 1,
                    }
                ),
            ),
        ],
    ),
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="^ipv6$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        append_to_query=ixia_types.Query(
            regex="^ethernet$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="Source Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "increment",
                        "StartValue": DHCPV6_MULTICAST_ADDR,
                        "StepValue": "::1",
                        "CountValue": 1,
                    }
                ),
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="Destination Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "valueList",
                        "ValueList": [DHCPV6_SERVER_MULTICAST_ADDR],
                    }
                ),
            ),
        ],
    ),
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="^udp$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        append_to_query=ixia_types.Query(
            regex="ipv6", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="UDP-Source-Port"),
                attrs_json=json.dumps(
                    {
                        "Auto": False,
                        "ValueType": "valueList",
                        "ValueList": [DHCPV6_RELAY_PORT],
                    }
                ),
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="UDP-Dest-Port"),
                attrs_json=json.dumps(
                    {
                        "Auto": False,
                        "SingleValue": DHCPV6_SERVER_PORT,
                    }
                ),
            ),
        ],
    ),
]

DHCP_V4_DISCOVER_TRAFFIC_PACKET_HEADERS: t.List[taac_types.PacketHeader] = [
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="^ethernet$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="Destination MAC Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "singleValue",
                        "SingleValue": BROADCAST_DST_MAC_ADDRESS,
                    }
                ),
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="Source MAC Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "singleValue",
                        "SingleValue": DEFAULT_SRC_MAC_ADDRESS,
                    }
                ),
            ),
        ],
    ),
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="^ipv4$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        append_to_query=ixia_types.Query(
            regex="^ethernet$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="Source Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "singleValue",
                        "SingleValue": "0.0.0.0",
                    }
                ),
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="Destination Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "singleValue",
                        "SingleValue": DHCPV4_BROADCAST_ADDR,
                    }
                ),
            ),
        ],
    ),
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="^udp$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        append_to_query=ixia_types.Query(
            regex="ipv4", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="UDP-Source-Port"),
                attrs_json=json.dumps(
                    {
                        "Auto": False,
                        "SingleValue": DHCPV4_CLIENT_PORT,
                    }
                ),
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="UDP-Dest-Port"),
                attrs_json=json.dumps(
                    {
                        "Auto": False,
                        "SingleValue": DHCPV4_SERVER_PORT,
                    }
                ),
            ),
        ],
    ),
]

# DHCP V4 Discover to Server Traffic Packet Headers
# Sends DHCP Discover to DHCP server IP address (from agent config dhcpRelayAddressV4)
# dmac: FF:FF:FF:FF:FF:FF, sport: 68, dport: 67
DHCP_V4_DISCOVER_TO_SERVER_TRAFFIC_PACKET_HEADERS: t.List[taac_types.PacketHeader] = [
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="^ethernet$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="Destination MAC Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "singleValue",
                        "SingleValue": BROADCAST_DST_MAC_ADDRESS,
                    }
                ),
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="Source MAC Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "singleValue",
                        "SingleValue": DEFAULT_SRC_MAC_ADDRESS,
                    }
                ),
            ),
        ],
    ),
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="^ipv4$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        append_to_query=ixia_types.Query(
            regex="^ethernet$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="Source Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "singleValue",
                        "SingleValue": "0.0.0.0",
                    }
                ),
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="Destination Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "singleValue",
                        "SingleValue": DHCPV4_RELAY_SERVER_ADDR,
                    }
                ),
            ),
        ],
    ),
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="^udp$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        append_to_query=ixia_types.Query(
            regex="ipv4", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="UDP-Source-Port"),
                attrs_json=json.dumps(
                    {
                        "Auto": False,
                        "SingleValue": DHCPV4_CLIENT_PORT,
                    }
                ),
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="UDP-Dest-Port"),
                attrs_json=json.dumps(
                    {
                        "Auto": False,
                        "SingleValue": DHCPV4_SERVER_PORT,
                    }
                ),
            ),
        ],
    ),
]

# DSCP Values for Monitoring or TC6: 30, 32, 35, ...
# Multiply by 4 to offset to ECN bits: 120
DSF_MONITORING_PACKET_HEADERS: t.List[taac_types.PacketHeader] = [
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="^ipv6$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="Traffic Class"),
                attrs_json=json.dumps(
                    {
                        "SingleValue": 120,
                    }
                ),
            ),
        ],
    ),
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="^udp$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        append_to_query=ixia_types.Query(
            regex="ipv6", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
    ),
]

ARP_TRAFFIC_PACKET_HEADERS: t.List[taac_types.PacketHeader] = [
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="^ethernet$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="Ethernet-Type"),
                attrs_json=json.dumps({"Auto": False, "SingleValue": "0806"}),
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="Destination MAC Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "increment",
                        "StepValue": "00:00:00:00:00:00",
                        "CountValue": 1,
                    }
                ),
                references={
                    "StartValue": taac_types.Reference(
                        type=taac_types.ReferenceType.DST_MAC_ADDRESS
                    ),
                },
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="Source MAC Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "increment",
                        "StartValue": DEFAULT_SRC_MAC_ADDRESS,
                        "StepValue": "00:00:00:00:00:00",
                        "CountValue": 1,
                    }
                ),
            ),
        ],
    ),
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="^arp$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        append_to_query=ixia_types.Query(
            regex="^ethernet$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
    ),
]

DSF_NC_PACKET_HEADERS: t.List[taac_types.PacketHeader] = [
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="^ipv6$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="Traffic Class"),
                attrs_json=json.dumps(
                    {
                        "SingleValue": 192,
                    }
                ),
            ),
        ],
    ),
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="^udp$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        append_to_query=ixia_types.Query(
            regex="ipv6", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
    ),
]

DEFAULT_IPV6_HEADER: t.List[taac_types.PacketHeader] = [
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="ipv6", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
    ),
]

DSF_BE_PACKET_HEADERS: t.List[taac_types.PacketHeader] = [
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="^udp$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        append_to_query=ixia_types.Query(
            regex="ipv6", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
    ),
]

DSF_RDMA_PACKET_HEADERS: t.List[taac_types.PacketHeader] = [
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="^ethernet$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="PFC Queue"),
                attrs_json=json.dumps(
                    {
                        "SingleValue": 0,
                    }
                ),
            ),
        ],
    ),
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="^ipv6$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="Traffic Class"),
                attrs_json=json.dumps(
                    {
                        "SingleValue": 224,
                    }
                ),
            ),
        ],
    ),
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="^udp$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="UDP-Dest-Port"),
                attrs_json=json.dumps(
                    {
                        "Auto": False,
                        "SingleValue": RDMA_PORT,
                    }
                ),
            ),
        ],
        append_to_query=ixia_types.Query(
            regex="ipv6", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
    ),
]

DSF_RDMA_IB_PACKET_HEADERS: t.List[taac_types.PacketHeader] = [
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="^ethernet$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="PFC Queue"),
                attrs_json=json.dumps(
                    {
                        "SingleValue": 0,
                    }
                ),
            ),
        ],
    ),
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="^ipv6$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="Traffic Class"),
                attrs_json=json.dumps(
                    {
                        "SingleValue": 224,
                    }
                ),
            ),
        ],
    ),
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="^udp$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="UDP-Dest-Port"),
                attrs_json=json.dumps(
                    {
                        "Auto": False,
                        "SingleValue": RDMA_PORT,
                    }
                ),
            ),
        ],
        append_to_query=ixia_types.Query(
            regex="ipv6", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
    ),
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="^infiniBandBaseTransportHeader$",
            query_type=ixia_types.QueryType.STACK_TYPE_ID,
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="Resv7"),
                attrs_json=json.dumps(
                    {
                        "SingleValue": 64,
                    }
                ),
            ),
        ],
        append_to_query=ixia_types.Query(
            regex="udp", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
    ),
]

LACP_SLOW_TIMER_TRAFFIC_PACKET_HEADERS: t.List[taac_types.PacketHeader] = [
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="^ethernet$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="Ethernet-Type"),
                attrs_json=json.dumps(
                    {"Auto": False, "SingleValue": "8809"}  # Slow Protocols: 0x8809
                ),
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="Destination MAC Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "increment",
                        "StartValue": LACP_DEST_MULTICAST_MAC,
                        "StepValue": "00:00:00:00:00:00",
                        "CountValue": 1,
                    }
                ),
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="Source MAC Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "increment",
                        "StartValue": DEFAULT_SRC_MAC_ADDRESS,
                        "StepValue": "00:00:00:00:00:00",
                        "CountValue": 1,
                    }
                ),
            ),
        ],
    ),
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="^lacp$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        append_to_query=ixia_types.Query(
            regex="^ethernet$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
    ),
]

# ARP Request with Broadcast destination (for CPU queue testing)
# Note: IXIA doesn't have an ARP protocol template available.
# We configure only the Ethernet layer with ARP EtherType (0x0806).
# The ARP payload will be part of the raw frame data.
ARP_REQUEST_TRAFFIC_PACKET_HEADERS: t.List[taac_types.PacketHeader] = [
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="^ethernet$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="Ethernet-Type"),
                attrs_json=json.dumps({"Auto": False, "SingleValue": "0806"}),
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="Destination MAC Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "singleValue",
                        "SingleValue": "ff:ff:ff:ff:ff:ff",  # Broadcast MAC
                    }
                ),
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="Source MAC Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "increment",
                        "StartValue": DEFAULT_SRC_MAC_ADDRESS,  # IXIA MAC
                        "StepValue": "00:00:00:00:00:00",
                        "CountValue": 1,
                    }
                ),
            ),
        ],
    ),
]

# ARP Response with unicast destination (Switch MAC) for CPU queue testing
# Note: IXIA doesn't have an ARP protocol template available.
# We configure only the Ethernet layer with ARP EtherType (0x0806).
# The destination MAC is resolved from the endpoint's MAC address via reference.
ARP_RESPONSE_TRAFFIC_PACKET_HEADERS: t.List[taac_types.PacketHeader] = [
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="^ethernet$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="Ethernet-Type"),
                attrs_json=json.dumps({"Auto": False, "SingleValue": "0806"}),
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="Destination MAC Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "increment",
                        "StepValue": "00:00:00:00:00:00",
                        "CountValue": 1,
                    }
                ),
                references={
                    "StartValue": taac_types.Reference(
                        type=taac_types.ReferenceType.DST_MAC_ADDRESS
                    ),
                },
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="Source MAC Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "increment",
                        "StartValue": DEFAULT_SRC_MAC_ADDRESS,  # IXIA MAC
                        "StepValue": "00:00:00:00:00:00",
                        "CountValue": 1,
                    }
                ),
            ),
        ],
    ),
]

NDP_TRAFFIC_PACKET_HEADERS: t.List[taac_types.PacketHeader] = [
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="^ethernet$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="Destination MAC Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "increment",
                        "StepValue": "00:00:00:00:00:00",
                        "CountValue": 1,
                    }
                ),
                references={
                    "StartValue": taac_types.Reference(
                        type=taac_types.ReferenceType.DST_MAC_ADDRESS
                    ),
                },
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="Source MAC Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "increment",
                        "StartValue": DEFAULT_SRC_MAC_ADDRESS,
                        "StepValue": "00:00:00:00:00:00",
                        "CountValue": 1,
                    }
                ),
            ),
        ],
    ),
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="^ipv6$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        append_to_query=ixia_types.Query(
            regex="^ethernet$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="Source Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "increment",
                        "StepValue": "::1",
                        "CountValue": 1,
                    }
                ),
                references={
                    "StartValue": taac_types.Reference(
                        type=taac_types.ReferenceType.SRC_IPV6_ADDRESS
                    ),
                },
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="Destination Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "valueList",
                    }
                ),
                references={
                    "ValueList": taac_types.Reference(
                        type=taac_types.ReferenceType.DST_GATEWAY_IPV6_ADDRESS,
                        data_type=taac_types.DataType.LIST,
                    ),
                },
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="Traffic Class"),
                attrs_json=json.dumps(
                    {
                        "SingleValue": 192,
                    }
                ),
            ),
        ],
    ),
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="icmpv6", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        append_to_query=ixia_types.Query(
            regex="ipv6", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="Type"),
                attrs_json=json.dumps(
                    {
                        "SingleValue": 135,
                    }
                ),
            ),
        ],
    ),
]

HOP_LIMIT_1_IPV6_TRAFFIC_PACKET_HEADERS: t.List[taac_types.PacketHeader] = [
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="^ethernet$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="Destination MAC Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "increment",
                        "StepValue": "00:00:00:00:00:00",
                        "CountValue": 1,
                    }
                ),
                references={
                    "StartValue": taac_types.Reference(
                        type=taac_types.ReferenceType.DST_MAC_ADDRESS
                    ),
                },
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="Source MAC Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "increment",
                        "StartValue": DEFAULT_SRC_MAC_ADDRESS,
                        "StepValue": "00:00:00:00:00:00",
                        "CountValue": 1,
                    }
                ),
            ),
        ],
    ),
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="^ipv6$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        append_to_query=ixia_types.Query(
            regex="^ethernet$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="Source Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "increment",
                        "StepValue": "::1",
                        "CountValue": 1,
                    }
                ),
                references={
                    "StartValue": taac_types.Reference(
                        type=taac_types.ReferenceType.SRC_IPV6_ADDRESS
                    ),
                },
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="Destination Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "valueList",
                    }
                ),
                references={
                    "ValueList": taac_types.Reference(
                        type=taac_types.ReferenceType.DST_IPV6_ADDRESS,
                        data_type=taac_types.DataType.LIST,
                    ),
                },
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="Hop Limit"),
                attrs_json=json.dumps(
                    {
                        "SingleValue": "1",
                    }
                ),
            ),
        ],
    ),
]

TTL_1_IPV4_TRAFFIC_PACKET_HEADERS: t.List[taac_types.PacketHeader] = [
    # Ethernet Layer
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="^ethernet$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="Destination MAC Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "increment",
                        "StepValue": "00:00:00:00:00:00",
                        "CountValue": 1,
                    }
                ),
                references={
                    "StartValue": taac_types.Reference(
                        type=taac_types.ReferenceType.DST_MAC_ADDRESS
                    ),
                },
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="Source MAC Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "increment",
                        "StartValue": DEFAULT_SRC_MAC_ADDRESS,
                        "StepValue": "00:00:00:00:00:00",
                        "CountValue": 1,
                    }
                ),
            ),
        ],
    ),
    # IPv4 Layer with TTL=1 and DSCP for low queue
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="^ipv4$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        append_to_query=ixia_types.Query(
            regex="^ethernet$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="Source Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "increment",
                        "StepValue": "0.0.0.1",
                        "CountValue": 1,
                    }
                ),
                references={
                    "StartValue": taac_types.Reference(
                        type=taac_types.ReferenceType.SRC_IPV4_ADDRESS,
                        device_group_index=1,
                    ),
                },
            ),
            # DIP: Remote network prefix (not gateway/local address)
            # Using DST_IPV4_ADDRESS instead of DST_GATEWAY_IPV4_ADDRESS
            # to avoid hitting the ip2me ACL rule which routes to mid queue
            taac_types.Field(
                query=ixia_types.Query(regex="Destination Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "valueList",
                    }
                ),
                references={
                    "ValueList": taac_types.Reference(
                        type=taac_types.ReferenceType.DST_IPV4_ADDRESS,
                        device_group_index=1,
                        data_type=taac_types.DataType.LIST,
                    ),
                },
            ),
            # TTL = 1
            taac_types.Field(
                query=ixia_types.Query(regex="TTL \\(Time to live\\)"),
                attrs_json=json.dumps(
                    {
                        "SingleValue": "1",
                    }
                ),
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="Type of Service"),
                attrs_json=json.dumps(
                    {
                        "SingleValue": "0",
                    }
                ),
            ),
        ],
    ),
]

TTL_0_IPV4_TRAFFIC_PACKET_HEADERS: t.List[taac_types.PacketHeader] = [
    # Ethernet Layer
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="^ethernet$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="Destination MAC Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "increment",
                        "StepValue": "00:00:00:00:00:00",
                        "CountValue": 1,
                    }
                ),
                references={
                    "StartValue": taac_types.Reference(
                        type=taac_types.ReferenceType.DST_MAC_ADDRESS
                    ),
                },
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="Source MAC Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "increment",
                        "StartValue": DEFAULT_SRC_MAC_ADDRESS,
                        "StepValue": "00:00:00:00:00:00",
                        "CountValue": 1,
                    }
                ),
            ),
        ],
    ),
    # IPv4 Layer with TTL=1 and DSCP for low queue
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="^ipv4$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        append_to_query=ixia_types.Query(
            regex="^ethernet$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="Source Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "increment",
                        "StepValue": "0.0.0.1",
                        "CountValue": 1,
                    }
                ),
                references={
                    "StartValue": taac_types.Reference(
                        type=taac_types.ReferenceType.SRC_IPV4_ADDRESS,
                        device_group_index=1,
                    ),
                },
            ),
            # DIP: Remote network prefix (not gateway/local address)
            # Using DST_IPV4_ADDRESS instead of DST_GATEWAY_IPV4_ADDRESS
            # to avoid hitting the ip2me ACL rule which routes to mid queue
            taac_types.Field(
                query=ixia_types.Query(regex="Destination Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "valueList",
                    }
                ),
                references={
                    "ValueList": taac_types.Reference(
                        type=taac_types.ReferenceType.DST_IPV4_ADDRESS,
                        device_group_index=1,
                        data_type=taac_types.DataType.LIST,
                    ),
                },
            ),
            # TTL = 1
            taac_types.Field(
                query=ixia_types.Query(regex="TTL \\(Time to live\\)"),
                attrs_json=json.dumps(
                    {
                        "SingleValue": "0",
                    }
                ),
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="Type of Service"),
                attrs_json=json.dumps(
                    {
                        "SingleValue": "0",
                    }
                ),
            ),
        ],
    ),
]

HOP_LIMIT_0_IPV6_TRAFFIC_PACKET_HEADERS: t.List[taac_types.PacketHeader] = [
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="^ethernet$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="Destination MAC Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "increment",
                        "StepValue": "00:00:00:00:00:00",
                        "CountValue": 1,
                    }
                ),
                references={
                    "StartValue": taac_types.Reference(
                        type=taac_types.ReferenceType.DST_MAC_ADDRESS
                    ),
                },
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="Source MAC Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "increment",
                        "StartValue": DEFAULT_SRC_MAC_ADDRESS,
                        "StepValue": "00:00:00:00:00:00",
                        "CountValue": 1,
                    }
                ),
            ),
        ],
    ),
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="^ipv6$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        append_to_query=ixia_types.Query(
            regex="^ethernet$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="Source Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "increment",
                        "StepValue": "::1",
                        "CountValue": 1,
                    }
                ),
                references={
                    "StartValue": taac_types.Reference(
                        type=taac_types.ReferenceType.SRC_IPV6_ADDRESS
                    ),
                },
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="Destination Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "valueList",
                    }
                ),
                references={
                    "ValueList": taac_types.Reference(
                        type=taac_types.ReferenceType.DST_IPV6_ADDRESS,
                        data_type=taac_types.DataType.LIST,
                    ),
                },
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="Hop Limit"),
                attrs_json=json.dumps(
                    {
                        "SingleValue": "0",
                    }
                ),
            ),
        ],
    ),
]
NDP_NS_MULTICAST_TRAFFIC_PACKET_HEADERS: t.List[taac_types.PacketHeader] = [
    # Ethernet Layer: Set source MAC to Ixia, destination to solicited-node multicast
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="^ethernet$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="Destination MAC Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "singleValue",
                        "SingleValue": NDP_SOLICITED_NODE_MULTICAST_MAC,
                    }
                ),
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="Source MAC Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "singleValue",
                        "SingleValue": DEFAULT_SRC_MAC_ADDRESS,
                    }
                ),
            ),
        ],
    ),
    # IPv6 Layer: Use link-local source, multicast destination, DSCP 48
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="^ipv6$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        append_to_query=ixia_types.Query(
            regex="^ethernet$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="Source Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "singleValue",
                        "SingleValue": NDP_IXIA_LINK_LOCAL_IPV6,
                    }
                ),
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="Destination Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "singleValue",
                        "SingleValue": NDP_SOLICITED_NODE_MULTICAST_IPV6,
                    }
                ),
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="Traffic Class"),
                attrs_json=json.dumps(
                    {
                        "SingleValue": NDP_DSCP_48_TRAFFIC_CLASS,
                    }
                ),
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="Hop Limit"),
                attrs_json=json.dumps(
                    {
                        "SingleValue": "255",
                    }
                ),
            ),
        ],
    ),
    # ICMPv6 Layer: Set message type to Neighbor Solicitation (135)
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="icmpv6", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        append_to_query=ixia_types.Query(
            regex="ipv6", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="Type"),
                attrs_json=json.dumps(
                    {
                        "SingleValue": str(ICMPV6_TYPE_NS),
                    }
                ),
            ),
        ],
    ),
]

NDP_NA_MULTICAST_TRAFFIC_PACKET_HEADERS: t.List[taac_types.PacketHeader] = [
    # Ethernet Layer: Set source MAC to Ixia, destination to all-nodes multicast
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="^ethernet$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="Destination MAC Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "singleValue",
                        "SingleValue": NDP_ALL_NODES_MULTICAST_MAC,
                    }
                ),
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="Source MAC Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "singleValue",
                        "SingleValue": DEFAULT_SRC_MAC_ADDRESS,
                    }
                ),
            ),
        ],
    ),
    # IPv6 Layer: Use link-local source, all-nodes multicast destination, DSCP 48
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="^ipv6$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        append_to_query=ixia_types.Query(
            regex="^ethernet$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="Source Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "singleValue",
                        "SingleValue": NDP_IXIA_LINK_LOCAL_IPV6,
                    }
                ),
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="Destination Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "singleValue",
                        "SingleValue": NDP_ALL_NODES_MULTICAST_IPV6,
                    }
                ),
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="Traffic Class"),
                attrs_json=json.dumps(
                    {
                        "SingleValue": NDP_DSCP_48_TRAFFIC_CLASS,
                    }
                ),
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="Hop Limit"),
                attrs_json=json.dumps(
                    {
                        "SingleValue": "255",
                    }
                ),
            ),
        ],
    ),
    # ICMPv6 Layer: Set message type to Neighbor Advertisement (136)
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="icmpv6", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        append_to_query=ixia_types.Query(
            regex="ipv6", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="Type"),
                attrs_json=json.dumps(
                    {
                        "SingleValue": str(ICMPV6_TYPE_NA),
                    }
                ),
            ),
        ],
    ),
]

NDP_RS_MULTICAST_TRAFFIC_PACKET_HEADERS: t.List[taac_types.PacketHeader] = [
    # Ethernet Layer: Set source MAC to Ixia, destination to all-routers multicast
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="^ethernet$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="Destination MAC Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "singleValue",
                        "SingleValue": NDP_ALL_ROUTERS_MULTICAST_MAC,
                    }
                ),
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="Source MAC Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "singleValue",
                        "SingleValue": DEFAULT_SRC_MAC_ADDRESS,
                    }
                ),
            ),
        ],
    ),
    # IPv6 Layer: Use link-local source, all-routers multicast destination, DSCP 48
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="^ipv6$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        append_to_query=ixia_types.Query(
            regex="^ethernet$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="Source Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "singleValue",
                        "SingleValue": NDP_IXIA_LINK_LOCAL_IPV6,
                    }
                ),
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="Destination Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "singleValue",
                        "SingleValue": NDP_ALL_ROUTERS_MULTICAST_IPV6,
                    }
                ),
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="Traffic Class"),
                attrs_json=json.dumps(
                    {
                        "SingleValue": NDP_DSCP_48_TRAFFIC_CLASS,
                    }
                ),
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="Hop Limit"),
                attrs_json=json.dumps(
                    {
                        "SingleValue": "255",
                    }
                ),
            ),
        ],
    ),
    # ICMPv6 Layer: Set message type to Router Solicitation (133)
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="icmpv6", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        append_to_query=ixia_types.Query(
            regex="ipv6", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="Type"),
                attrs_json=json.dumps(
                    {
                        "SingleValue": str(ICMPV6_TYPE_RS),
                    }
                ),
            ),
        ],
    ),
]

NDP_RA_MULTICAST_TRAFFIC_PACKET_HEADERS: t.List[taac_types.PacketHeader] = [
    # Ethernet Layer: Set source MAC to Ixia, destination to all-nodes multicast
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="^ethernet$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="Destination MAC Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "singleValue",
                        "SingleValue": NDP_ALL_NODES_MULTICAST_MAC,
                    }
                ),
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="Source MAC Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "singleValue",
                        "SingleValue": DEFAULT_SRC_MAC_ADDRESS,
                    }
                ),
            ),
        ],
    ),
    # IPv6 Layer: Use link-local source, all-nodes multicast destination, DSCP 48
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="^ipv6$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        append_to_query=ixia_types.Query(
            regex="^ethernet$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="Source Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "singleValue",
                        "SingleValue": NDP_IXIA_LINK_LOCAL_IPV6,
                    }
                ),
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="Destination Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "singleValue",
                        "SingleValue": NDP_ALL_NODES_MULTICAST_IPV6,
                    }
                ),
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="Traffic Class"),
                attrs_json=json.dumps(
                    {
                        "SingleValue": NDP_DSCP_48_TRAFFIC_CLASS,
                    }
                ),
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="Hop Limit"),
                attrs_json=json.dumps(
                    {
                        "SingleValue": "255",
                    }
                ),
            ),
        ],
    ),
    # ICMPv6 Layer: Set message type to Router Advertisement (134)
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="icmpv6", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        append_to_query=ixia_types.Query(
            regex="ipv6", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="Type"),
                attrs_json=json.dumps(
                    {
                        "SingleValue": str(ICMPV6_TYPE_RA),
                    }
                ),
            ),
        ],
    ),
]


#############################################################
#                ICMPv6 NDP Unicast Traffic Headers         #
#############################################################


# NDP Neighbor Solicitation (NS) Unicast Traffic Headers
# SMAC: Ixia MAC, DMAC: Switch MAC, SIP: Ixia link-local, DIP: Switch link-local, DSCP: 48
NDP_NS_UNICAST_TRAFFIC_PACKET_HEADERS: t.List[taac_types.PacketHeader] = [
    # Ethernet Layer: Set source MAC to Ixia, destination to switch MAC (unicast)
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="^ethernet$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="Destination MAC Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "increment",
                        "StepValue": "00:00:00:00:00:00",
                        "CountValue": 1,
                    }
                ),
                references={
                    "StartValue": taac_types.Reference(
                        type=taac_types.ReferenceType.DST_MAC_ADDRESS
                    ),
                },
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="Source MAC Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "singleValue",
                        "SingleValue": DEFAULT_SRC_MAC_ADDRESS,
                    }
                ),
            ),
        ],
    ),
    # IPv6 Layer: Use Ixia link-local source, switch link-local destination, DSCP: 48
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="^ipv6$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        append_to_query=ixia_types.Query(
            regex="^ethernet$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="Source Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "singleValue",
                        "SingleValue": NDP_IXIA_LINK_LOCAL_IPV6,
                    }
                ),
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="Destination Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "valueList",
                    }
                ),
                references={
                    "ValueList": taac_types.Reference(
                        type=taac_types.ReferenceType.DST_LINK_LOCAL_IPV6_ADDRESS,
                        data_type=taac_types.DataType.LIST,
                    ),
                },
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="Traffic Class"),
                attrs_json=json.dumps(
                    {
                        "SingleValue": NDP_DSCP_48_TRAFFIC_CLASS,
                    }
                ),
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="Hop Limit"),
                attrs_json=json.dumps(
                    {
                        "SingleValue": "255",
                    }
                ),
            ),
        ],
    ),
    # ICMPv6 Layer: Set message type to Neighbor Solicitation (135)
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="icmpv6", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        append_to_query=ixia_types.Query(
            regex="ipv6", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="Type"),
                attrs_json=json.dumps(
                    {
                        "SingleValue": str(ICMPV6_TYPE_NS),
                    }
                ),
            ),
        ],
    ),
]

# NDP Neighbor Advertisement (NA) Unicast Traffic Headers
# SMAC: Ixia MAC, DMAC: Switch MAC, SIP: Ixia link-local, DIP: Switch link-local, DSCP: 48
NDP_NA_UNICAST_TRAFFIC_PACKET_HEADERS: t.List[taac_types.PacketHeader] = [
    # Ethernet Layer: Set source MAC to Ixia, destination to switch MAC (unicast)
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="^ethernet$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="Destination MAC Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "increment",
                        "StepValue": "00:00:00:00:00:00",
                        "CountValue": 1,
                    }
                ),
                references={
                    "StartValue": taac_types.Reference(
                        type=taac_types.ReferenceType.DST_MAC_ADDRESS
                    ),
                },
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="Source MAC Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "singleValue",
                        "SingleValue": DEFAULT_SRC_MAC_ADDRESS,
                    }
                ),
            ),
        ],
    ),
    # IPv6 Layer: Use Ixia link-local source, switch link-local destination, DSCP: 48
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="^ipv6$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        append_to_query=ixia_types.Query(
            regex="^ethernet$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="Source Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "singleValue",
                        "SingleValue": NDP_IXIA_LINK_LOCAL_IPV6,
                    }
                ),
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="Destination Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "valueList",
                    }
                ),
                references={
                    "ValueList": taac_types.Reference(
                        type=taac_types.ReferenceType.DST_LINK_LOCAL_IPV6_ADDRESS,
                        data_type=taac_types.DataType.LIST,
                    ),
                },
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="Traffic Class"),
                attrs_json=json.dumps(
                    {
                        "SingleValue": NDP_DSCP_48_TRAFFIC_CLASS,
                    }
                ),
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="Hop Limit"),
                attrs_json=json.dumps(
                    {
                        "SingleValue": "255",
                    }
                ),
            ),
        ],
    ),
    # ICMPv6 Layer: Set message type to Neighbor Advertisement (136)
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="icmpv6", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        append_to_query=ixia_types.Query(
            regex="ipv6", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="Type"),
                attrs_json=json.dumps(
                    {
                        "SingleValue": str(ICMPV6_TYPE_NA),
                    }
                ),
            ),
        ],
    ),
]

# NDP Router Solicitation (RS) Unicast Traffic Headers
# SMAC: Ixia MAC, DMAC: Switch MAC, SIP: Ixia link-local, DIP: Switch link-local, DSCP: 48
NDP_RS_UNICAST_TRAFFIC_PACKET_HEADERS: t.List[taac_types.PacketHeader] = [
    # Ethernet Layer: Set source MAC to Ixia, destination to switch MAC (unicast)
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="^ethernet$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="Destination MAC Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "increment",
                        "StepValue": "00:00:00:00:00:00",
                        "CountValue": 1,
                    }
                ),
                references={
                    "StartValue": taac_types.Reference(
                        type=taac_types.ReferenceType.DST_MAC_ADDRESS
                    ),
                },
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="Source MAC Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "singleValue",
                        "SingleValue": DEFAULT_SRC_MAC_ADDRESS,
                    }
                ),
            ),
        ],
    ),
    # IPv6 Layer: Use Ixia link-local source, switch link-local destination, DSCP: 48
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="^ipv6$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        append_to_query=ixia_types.Query(
            regex="^ethernet$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="Source Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "singleValue",
                        "SingleValue": NDP_IXIA_LINK_LOCAL_IPV6,
                    }
                ),
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="Destination Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "valueList",
                    }
                ),
                references={
                    "ValueList": taac_types.Reference(
                        type=taac_types.ReferenceType.DST_LINK_LOCAL_IPV6_ADDRESS,
                        data_type=taac_types.DataType.LIST,
                    ),
                },
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="Traffic Class"),
                attrs_json=json.dumps(
                    {
                        "SingleValue": NDP_DSCP_48_TRAFFIC_CLASS,
                    }
                ),
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="Hop Limit"),
                attrs_json=json.dumps(
                    {
                        "SingleValue": "255",
                    }
                ),
            ),
        ],
    ),
    # ICMPv6 Layer: Set message type to Router Solicitation (133)
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="icmpv6", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        append_to_query=ixia_types.Query(
            regex="ipv6", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="Type"),
                attrs_json=json.dumps(
                    {
                        "SingleValue": str(ICMPV6_TYPE_RS),
                    }
                ),
            ),
        ],
    ),
]

# NDP Router Advertisement (RA) Unicast Traffic Headers
# SMAC: Ixia MAC, DMAC: Switch MAC, SIP: Ixia link-local, DIP: Switch link-local, DSCP: 48
NDP_RA_UNICAST_TRAFFIC_PACKET_HEADERS: t.List[taac_types.PacketHeader] = [
    # Ethernet Layer: Set source MAC to Ixia, destination to switch MAC (unicast)
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="^ethernet$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="Destination MAC Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "increment",
                        "StepValue": "00:00:00:00:00:00",
                        "CountValue": 1,
                    }
                ),
                references={
                    "StartValue": taac_types.Reference(
                        type=taac_types.ReferenceType.DST_MAC_ADDRESS
                    ),
                },
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="Source MAC Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "singleValue",
                        "SingleValue": DEFAULT_SRC_MAC_ADDRESS,
                    }
                ),
            ),
        ],
    ),
    # IPv6 Layer: Use Ixia link-local source, switch link-local destination, DSCP: 48
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="^ipv6$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        append_to_query=ixia_types.Query(
            regex="^ethernet$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="Source Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "singleValue",
                        "SingleValue": NDP_IXIA_LINK_LOCAL_IPV6,
                    }
                ),
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="Destination Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "valueList",
                    }
                ),
                references={
                    "ValueList": taac_types.Reference(
                        type=taac_types.ReferenceType.DST_LINK_LOCAL_IPV6_ADDRESS,
                        data_type=taac_types.DataType.LIST,
                    ),
                },
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="Traffic Class"),
                attrs_json=json.dumps(
                    {
                        "SingleValue": NDP_DSCP_48_TRAFFIC_CLASS,
                    }
                ),
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="Hop Limit"),
                attrs_json=json.dumps(
                    {
                        "SingleValue": "255",
                    }
                ),
            ),
        ],
    ),
    # ICMPv6 Layer: Set message type to Router Advertisement (134)
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="icmpv6", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        append_to_query=ixia_types.Query(
            regex="ipv6", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="Type"),
                attrs_json=json.dumps(
                    {
                        "SingleValue": str(ICMPV6_TYPE_RA),
                    }
                ),
            ),
        ],
    ),
]


#############################################################
#                ICMPv6 Non-NDP Traffic Headers             #
#############################################################

# ICMPv6 Echo Request with Link-Local Addresses
# SMAC: ixia, DMAC: switch MAC, SIP: link local ixia, DIP: link local switch
ICMP_V6_ECHO_REQUEST_LINK_LOCAL_TRAFFIC_PACKET_HEADERS: t.List[
    taac_types.PacketHeader
] = [
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="^ethernet$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="Destination MAC Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "increment",
                        "StepValue": "00:00:00:00:00:00",
                        "CountValue": 1,
                    }
                ),
                references={
                    "StartValue": taac_types.Reference(
                        type=taac_types.ReferenceType.DST_MAC_ADDRESS
                    ),
                },
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="Source MAC Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "singleValue",
                        "SingleValue": DEFAULT_SRC_MAC_ADDRESS,
                    }
                ),
            ),
        ],
    ),
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="^ipv6$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        append_to_query=ixia_types.Query(
            regex="^ethernet$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="Source Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "singleValue",
                        "SingleValue": NDP_IXIA_LINK_LOCAL_IPV6,
                    }
                ),
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="Destination Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "valueList",
                    }
                ),
                references={
                    "ValueList": taac_types.Reference(
                        type=taac_types.ReferenceType.DST_GATEWAY_IPV6_ADDRESS,
                        data_type=taac_types.DataType.LIST,
                    ),
                },
            ),
        ],
    ),
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="icmpv6", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        append_to_query=ixia_types.Query(
            regex="ipv6", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="Type"),
                attrs_json=json.dumps(
                    {
                        "SingleValue": str(ICMPV6_TYPE_ECHO_REQUEST),
                    }
                ),
            ),
        ],
    ),
]

# ICMPv6 Echo Reply with Link-Local Addresses
ICMP_V6_ECHO_REPLY_LINK_LOCAL_TRAFFIC_PACKET_HEADERS: t.List[
    taac_types.PacketHeader
] = [
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="^ethernet$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="Destination MAC Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "increment",
                        "StepValue": "00:00:00:00:00:00",
                        "CountValue": 1,
                    }
                ),
                references={
                    "StartValue": taac_types.Reference(
                        type=taac_types.ReferenceType.DST_MAC_ADDRESS
                    ),
                },
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="Source MAC Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "singleValue",
                        "SingleValue": DEFAULT_SRC_MAC_ADDRESS,
                    }
                ),
            ),
        ],
    ),
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="^ipv6$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        append_to_query=ixia_types.Query(
            regex="^ethernet$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="Source Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "singleValue",
                        "SingleValue": NDP_IXIA_LINK_LOCAL_IPV6,
                    }
                ),
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="Destination Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "valueList",
                    }
                ),
                references={
                    "ValueList": taac_types.Reference(
                        type=taac_types.ReferenceType.DST_GATEWAY_IPV6_ADDRESS,
                        data_type=taac_types.DataType.LIST,
                    ),
                },
            ),
        ],
    ),
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="icmpv6", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        append_to_query=ixia_types.Query(
            regex="ipv6", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="Type"),
                attrs_json=json.dumps(
                    {
                        "SingleValue": str(ICMPV6_TYPE_ECHO_REPLY),
                    }
                ),
            ),
        ],
    ),
]

# ICMPv6 Destination Unreachable with Link-Local Addresses
ICMP_V6_DEST_UNREACHABLE_LINK_LOCAL_TRAFFIC_PACKET_HEADERS: t.List[
    taac_types.PacketHeader
] = [
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="^ethernet$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="Destination MAC Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "increment",
                        "StepValue": "00:00:00:00:00:00",
                        "CountValue": 1,
                    }
                ),
                references={
                    "StartValue": taac_types.Reference(
                        type=taac_types.ReferenceType.DST_MAC_ADDRESS
                    ),
                },
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="Source MAC Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "singleValue",
                        "SingleValue": DEFAULT_SRC_MAC_ADDRESS,
                    }
                ),
            ),
        ],
    ),
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="^ipv6$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        append_to_query=ixia_types.Query(
            regex="^ethernet$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="Source Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "singleValue",
                        "SingleValue": NDP_IXIA_LINK_LOCAL_IPV6,
                    }
                ),
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="Destination Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "valueList",
                    }
                ),
                references={
                    "ValueList": taac_types.Reference(
                        type=taac_types.ReferenceType.DST_GATEWAY_IPV6_ADDRESS,
                        data_type=taac_types.DataType.LIST,
                    ),
                },
            ),
        ],
    ),
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="icmpv6", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        append_to_query=ixia_types.Query(
            regex="ipv6", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="Type"),
                attrs_json=json.dumps(
                    {
                        "SingleValue": str(ICMPV6_TYPE_DEST_UNREACHABLE),
                    }
                ),
            ),
        ],
    ),
]

# ICMPv6 Packet Too Big with Link-Local Addresses
ICMP_V6_PACKET_TOO_BIG_LINK_LOCAL_TRAFFIC_PACKET_HEADERS: t.List[
    taac_types.PacketHeader
] = [
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="^ethernet$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="Destination MAC Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "increment",
                        "StepValue": "00:00:00:00:00:00",
                        "CountValue": 1,
                    }
                ),
                references={
                    "StartValue": taac_types.Reference(
                        type=taac_types.ReferenceType.DST_MAC_ADDRESS
                    ),
                },
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="Source MAC Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "singleValue",
                        "SingleValue": DEFAULT_SRC_MAC_ADDRESS,
                    }
                ),
            ),
        ],
    ),
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="^ipv6$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        append_to_query=ixia_types.Query(
            regex="^ethernet$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="Source Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "singleValue",
                        "SingleValue": NDP_IXIA_LINK_LOCAL_IPV6,
                    }
                ),
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="Destination Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "valueList",
                    }
                ),
                references={
                    "ValueList": taac_types.Reference(
                        type=taac_types.ReferenceType.DST_GATEWAY_IPV6_ADDRESS,
                        data_type=taac_types.DataType.LIST,
                    ),
                },
            ),
        ],
    ),
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="icmpv6", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        append_to_query=ixia_types.Query(
            regex="ipv6", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="Type"),
                attrs_json=json.dumps(
                    {
                        "SingleValue": str(ICMPV6_TYPE_PACKET_TOO_BIG),
                    }
                ),
            ),
        ],
    ),
]

# ICMPv6 Time Exceeded with Link-Local Addresses
ICMP_V6_TIME_EXCEEDED_LINK_LOCAL_TRAFFIC_PACKET_HEADERS: t.List[
    taac_types.PacketHeader
] = [
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="^ethernet$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="Destination MAC Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "increment",
                        "StepValue": "00:00:00:00:00:00",
                        "CountValue": 1,
                    }
                ),
                references={
                    "StartValue": taac_types.Reference(
                        type=taac_types.ReferenceType.DST_MAC_ADDRESS
                    ),
                },
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="Source MAC Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "singleValue",
                        "SingleValue": DEFAULT_SRC_MAC_ADDRESS,
                    }
                ),
            ),
        ],
    ),
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="^ipv6$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        append_to_query=ixia_types.Query(
            regex="^ethernet$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="Source Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "singleValue",
                        "SingleValue": NDP_IXIA_LINK_LOCAL_IPV6,
                    }
                ),
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="Destination Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "valueList",
                    }
                ),
                references={
                    "ValueList": taac_types.Reference(
                        type=taac_types.ReferenceType.DST_GATEWAY_IPV6_ADDRESS,
                        data_type=taac_types.DataType.LIST,
                    ),
                },
            ),
        ],
    ),
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="icmpv6", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        append_to_query=ixia_types.Query(
            regex="ipv6", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="Type"),
                attrs_json=json.dumps(
                    {
                        "SingleValue": str(ICMPV6_TYPE_TIME_EXCEEDED),
                    }
                ),
            ),
        ],
    ),
]


#############################################################
#         ICMPv6 Non-NDP with Global Addresses + DSCP 48    #
#############################################################

# ICMPv6 Echo Request with Global Addresses and DSCP 48
# SMAC: ixia, DMAC: switch MAC, SIP: global ixia, DIP: global switch, DSCP: 48
ICMP_V6_ECHO_REQUEST_GLOBAL_DSCP48_TRAFFIC_PACKET_HEADERS: t.List[
    taac_types.PacketHeader
] = [
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="^ethernet$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="Destination MAC Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "increment",
                        "StepValue": "00:00:00:00:00:00",
                        "CountValue": 1,
                    }
                ),
                references={
                    "StartValue": taac_types.Reference(
                        type=taac_types.ReferenceType.DST_MAC_ADDRESS
                    ),
                },
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="Source MAC Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "singleValue",
                        "SingleValue": DEFAULT_SRC_MAC_ADDRESS,
                    }
                ),
            ),
        ],
    ),
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="^ipv6$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        append_to_query=ixia_types.Query(
            regex="^ethernet$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="Source Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "increment",
                        "StepValue": "::1",
                        "CountValue": 1,
                    }
                ),
                references={
                    "StartValue": taac_types.Reference(
                        type=taac_types.ReferenceType.SRC_IPV6_ADDRESS
                    ),
                },
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="Destination Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "valueList",
                    }
                ),
                references={
                    "ValueList": taac_types.Reference(
                        type=taac_types.ReferenceType.DST_GATEWAY_IPV6_ADDRESS,
                        data_type=taac_types.DataType.LIST,
                    ),
                },
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="Traffic Class"),
                attrs_json=json.dumps(
                    {
                        "SingleValue": NDP_DSCP_48_TRAFFIC_CLASS,
                    }
                ),
            ),
        ],
    ),
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="icmpv6", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        append_to_query=ixia_types.Query(
            regex="ipv6", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="Type"),
                attrs_json=json.dumps(
                    {
                        "SingleValue": str(ICMPV6_TYPE_ECHO_REQUEST),
                    }
                ),
            ),
        ],
    ),
]

# ICMPv6 Echo Reply with Global Addresses and DSCP 48
ICMP_V6_ECHO_REPLY_GLOBAL_DSCP48_TRAFFIC_PACKET_HEADERS: t.List[
    taac_types.PacketHeader
] = [
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="^ethernet$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="Destination MAC Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "increment",
                        "StepValue": "00:00:00:00:00:00",
                        "CountValue": 1,
                    }
                ),
                references={
                    "StartValue": taac_types.Reference(
                        type=taac_types.ReferenceType.DST_MAC_ADDRESS
                    ),
                },
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="Source MAC Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "singleValue",
                        "SingleValue": DEFAULT_SRC_MAC_ADDRESS,
                    }
                ),
            ),
        ],
    ),
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="^ipv6$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        append_to_query=ixia_types.Query(
            regex="^ethernet$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="Source Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "increment",
                        "StepValue": "::1",
                        "CountValue": 1,
                    }
                ),
                references={
                    "StartValue": taac_types.Reference(
                        type=taac_types.ReferenceType.SRC_IPV6_ADDRESS
                    ),
                },
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="Destination Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "valueList",
                    }
                ),
                references={
                    "ValueList": taac_types.Reference(
                        type=taac_types.ReferenceType.DST_GATEWAY_IPV6_ADDRESS,
                        data_type=taac_types.DataType.LIST,
                    ),
                },
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="Traffic Class"),
                attrs_json=json.dumps(
                    {
                        "SingleValue": NDP_DSCP_48_TRAFFIC_CLASS,
                    }
                ),
            ),
        ],
    ),
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="icmpv6", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        append_to_query=ixia_types.Query(
            regex="ipv6", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="Type"),
                attrs_json=json.dumps(
                    {
                        "SingleValue": str(ICMPV6_TYPE_ECHO_REPLY),
                    }
                ),
            ),
        ],
    ),
]

# ICMPv6 Destination Unreachable with Global Addresses and DSCP 48
ICMP_V6_DEST_UNREACHABLE_GLOBAL_DSCP48_TRAFFIC_PACKET_HEADERS: t.List[
    taac_types.PacketHeader
] = [
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="^ethernet$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="Destination MAC Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "increment",
                        "StepValue": "00:00:00:00:00:00",
                        "CountValue": 1,
                    }
                ),
                references={
                    "StartValue": taac_types.Reference(
                        type=taac_types.ReferenceType.DST_MAC_ADDRESS
                    ),
                },
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="Source MAC Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "singleValue",
                        "SingleValue": DEFAULT_SRC_MAC_ADDRESS,
                    }
                ),
            ),
        ],
    ),
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="^ipv6$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        append_to_query=ixia_types.Query(
            regex="^ethernet$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="Source Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "increment",
                        "StepValue": "::1",
                        "CountValue": 1,
                    }
                ),
                references={
                    "StartValue": taac_types.Reference(
                        type=taac_types.ReferenceType.SRC_IPV6_ADDRESS
                    ),
                },
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="Destination Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "valueList",
                    }
                ),
                references={
                    "ValueList": taac_types.Reference(
                        type=taac_types.ReferenceType.DST_GATEWAY_IPV6_ADDRESS,
                        data_type=taac_types.DataType.LIST,
                    ),
                },
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="Traffic Class"),
                attrs_json=json.dumps(
                    {
                        "SingleValue": NDP_DSCP_48_TRAFFIC_CLASS,
                    }
                ),
            ),
        ],
    ),
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="icmpv6", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        append_to_query=ixia_types.Query(
            regex="ipv6", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="Type"),
                attrs_json=json.dumps(
                    {
                        "SingleValue": str(ICMPV6_TYPE_DEST_UNREACHABLE),
                    }
                ),
            ),
        ],
    ),
]

# ICMPv6 Packet Too Big with Global Addresses and DSCP 48
ICMP_V6_PACKET_TOO_BIG_GLOBAL_DSCP48_TRAFFIC_PACKET_HEADERS: t.List[
    taac_types.PacketHeader
] = [
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="^ethernet$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="Destination MAC Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "increment",
                        "StepValue": "00:00:00:00:00:00",
                        "CountValue": 1,
                    }
                ),
                references={
                    "StartValue": taac_types.Reference(
                        type=taac_types.ReferenceType.DST_MAC_ADDRESS
                    ),
                },
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="Source MAC Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "singleValue",
                        "SingleValue": DEFAULT_SRC_MAC_ADDRESS,
                    }
                ),
            ),
        ],
    ),
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="^ipv6$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        append_to_query=ixia_types.Query(
            regex="^ethernet$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="Source Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "increment",
                        "StepValue": "::1",
                        "CountValue": 1,
                    }
                ),
                references={
                    "StartValue": taac_types.Reference(
                        type=taac_types.ReferenceType.SRC_IPV6_ADDRESS
                    ),
                },
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="Destination Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "valueList",
                    }
                ),
                references={
                    "ValueList": taac_types.Reference(
                        type=taac_types.ReferenceType.DST_GATEWAY_IPV6_ADDRESS,
                        data_type=taac_types.DataType.LIST,
                    ),
                },
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="Traffic Class"),
                attrs_json=json.dumps(
                    {
                        "SingleValue": NDP_DSCP_48_TRAFFIC_CLASS,
                    }
                ),
            ),
        ],
    ),
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="icmpv6", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        append_to_query=ixia_types.Query(
            regex="ipv6", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="Type"),
                attrs_json=json.dumps(
                    {
                        "SingleValue": str(ICMPV6_TYPE_PACKET_TOO_BIG),
                    }
                ),
            ),
        ],
    ),
]

# ICMPv6 Time Exceeded with Global Addresses and DSCP 48
ICMP_V6_TIME_EXCEEDED_GLOBAL_DSCP48_TRAFFIC_PACKET_HEADERS: t.List[
    taac_types.PacketHeader
] = [
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="^ethernet$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="Destination MAC Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "increment",
                        "StepValue": "00:00:00:00:00:00",
                        "CountValue": 1,
                    }
                ),
                references={
                    "StartValue": taac_types.Reference(
                        type=taac_types.ReferenceType.DST_MAC_ADDRESS
                    ),
                },
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="Source MAC Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "singleValue",
                        "SingleValue": DEFAULT_SRC_MAC_ADDRESS,
                    }
                ),
            ),
        ],
    ),
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="^ipv6$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        append_to_query=ixia_types.Query(
            regex="^ethernet$", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="Source Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "increment",
                        "StepValue": "::1",
                        "CountValue": 1,
                    }
                ),
                references={
                    "StartValue": taac_types.Reference(
                        type=taac_types.ReferenceType.SRC_IPV6_ADDRESS
                    ),
                },
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="Destination Address"),
                attrs_json=json.dumps(
                    {
                        "ValueType": "valueList",
                    }
                ),
                references={
                    "ValueList": taac_types.Reference(
                        type=taac_types.ReferenceType.DST_GATEWAY_IPV6_ADDRESS,
                        data_type=taac_types.DataType.LIST,
                    ),
                },
            ),
            taac_types.Field(
                query=ixia_types.Query(regex="Traffic Class"),
                attrs_json=json.dumps(
                    {
                        "SingleValue": NDP_DSCP_48_TRAFFIC_CLASS,
                    }
                ),
            ),
        ],
    ),
    taac_types.PacketHeader(
        query=ixia_types.Query(
            regex="icmpv6", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        append_to_query=ixia_types.Query(
            regex="ipv6", query_type=ixia_types.QueryType.STACK_TYPE_ID
        ),
        fields=[
            taac_types.Field(
                query=ixia_types.Query(regex="Type"),
                attrs_json=json.dumps(
                    {
                        "SingleValue": str(ICMPV6_TYPE_TIME_EXCEEDED),
                    }
                ),
            ),
        ],
    ),
]
