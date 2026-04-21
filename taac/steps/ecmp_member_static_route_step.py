# pyre-unsafe
import asyncio
import ipaddress
import itertools
import typing as t

from taac.steps.step import Step
from taac.utils.health_check_utils import (
    generate_prefix_nh_list_map,
)
from taac.test_as_a_config import types as taac_types

PERCENT_ECMP_MEMBERS_VALID_BGP = 0.25
ECMP_GROUP_USAGE_FOR_MEMBER_STRESS = 1300


class EcmpMemberStaticRouteStep(Step[taac_types.BaseInput]):
    STEP_NAME = taac_types.StepName.ECMP_MEMBER_STATIC_ROUTE

    async def run(
        self,
        input: taac_types.BaseInput,
        params: t.Dict[str, t.Any],
    ) -> None:
        static_route_patcher_name = "ecmp_nh_stressor_patcher"
        dut_driver_class = self.driver
        delete_patcher_and_exit_step = params.get("delete_patcher_and_exit_step", False)
        # Cleaning up existing patchers related to ECMP before adding the current one
        await dut_driver_class.async_coop_unregister_patchers(static_route_patcher_name)
        if delete_patcher_and_exit_step:
            return

        nh_common_last_hextet = "a000"
        max_ecmp_group = params["max_ecmp_group"]
        max_ecmp_members = params["max_ecmp_members"]
        nh_prefix_1 = params["nh_prefix_1"]
        lb_prefix_agg = params["lb_prefix_agg"]
        device_group_count = params["device_group_count"]
        sleep_time_route_add_s = params.get("sleep_time_route_add_s", 60)
        dut_driver_class = self.driver

        # Identifying the current offset numbers after removing the patcher stress
        current_ecmp_member = (
            await dut_driver_class.async_verify_ecmp_nexthop_group_member_count()
        )
        self.driver.logger.info(
            f"Intended ECMP member with current + static routes: {max_ecmp_members}"
        )
        self.driver.logger.info(f"Current ECMP member: {current_ecmp_member}")
        current_ecmp_group = len(
            await dut_driver_class.async_get_ecmp_groups_snapshot()
        )
        self.driver.logger.info(f"Current ECMP group: {current_ecmp_group}")
        static_based_ecmp_group = max_ecmp_group - current_ecmp_group
        self.driver.logger.info(
            f"Applying static route to additionally add {static_based_ecmp_group=} groups"
        )
        static_based_ecmp_member = max_ecmp_members - current_ecmp_member
        self.driver.logger.info(
            f"Applying static route to additionally add {static_based_ecmp_member=} members"
        )

        # Createst the list of Nexthops from infra ip address and list of loadbearing prefixes
        network_1 = ipaddress.IPv6Network(nh_prefix_1, strict=False)
        base_increment = int(nh_common_last_hextet, 16)
        nh_list = [
            str(network_1.network_address + base_increment + i)
            for i in range(device_group_count)
        ]
        lb_network = ipaddress.IPv6Network(lb_prefix_agg, strict=False)
        lb_prefix_len = 128
        lb_subnets_iterator = lb_network.subnets(new_prefix=lb_prefix_len)
        lb_subnets = list(
            itertools.islice(lb_subnets_iterator, static_based_ecmp_group)
        )
        lb_prefix_list = [
            f"{subnet.network_address}/{lb_prefix_len}" for subnet in lb_subnets
        ]
        ecmp_combinations_list = generate_prefix_nh_list_map(
            nh_list, static_based_ecmp_member, static_based_ecmp_group
        )
        prefix_to_nexthops = {
            prefix: list(combination)
            for prefix, combination in zip(lb_prefix_list, ecmp_combinations_list)
        }
        self.driver.logger.info(
            f"Number of unique ecmp combinations: {len(ecmp_combinations_list)}"
        )
        expected_ecmp_member_count = sum(
            len(nh_set) for nh_set in ecmp_combinations_list
        )
        self.driver.logger.info(f"Total ECMP members: {expected_ecmp_member_count}")
        # self.driver.logger.info(prefix_to_nexthops)

        await dut_driver_class.async_add_static_route_patcher(
            prefix_to_nexthops,
            static_route_patcher_name,
            is_patcher_name_uuid_needed=False,
        )
        self.driver.logger.info(
            f"Sleeping {sleep_time_route_add_s}s after addition of new static route patcher"
        )
        await asyncio.sleep(sleep_time_route_add_s)
        self.driver.logger.info(
            f"Current member count: {await dut_driver_class.async_verify_ecmp_nexthop_group_member_count()} "
            f"Current Group  count: {len(await dut_driver_class.async_get_ecmp_groups_snapshot())}"
        )
