# (c) Meta Platforms, Inc. and affiliates. Confidential and proprietary.
# pyre-unsafe
import asyncio
import time
import typing as t

from taac.steps.step import Step
from taac.utils.flap_timing_utils import (
    apply_flap_timing,
    pick_flap_timing,
)
from taac.utils.oss_taac_lib_utils import none_throws
from taac.test_as_a_config import types as taac_types


class ChronosNode(Step[taac_types.BaseInput]):
    STEP_NAME = taac_types.StepName.TOGGLE_IXIA_PREFIX_SESSION_FLAP

    def get_bgp_peer_regex(self, tag_names: t.List[str]) -> str:
        ixia = none_throws(self.ixia)
        bgp_peer_name = []
        device_group_objs = self.get_device_group_obj_from_tags(tag_names=tag_names)
        for device_group in device_group_objs:
            for ethernet in device_group.Ethernet.find():
                for ipv6 in ethernet.Ipv6.find():
                    bgp_peer = ipv6.BgpIpv6Peer.find()
                    if not bgp_peer:
                        continue
                    bgp_peer_name.append(bgp_peer.Name)
                for ipv4 in ethernet.Ipv4.find():
                    bgp_peer = ipv4.BgpIpv4Peer.find()
                    if not bgp_peer:
                        continue
                    bgp_peer_name.append(bgp_peer.Name)
        ixia.logger.info(f"BGP peer names under purview: {bgp_peer_name}")
        return "|".join(bgp_peer_name)

    def _collect_all_device_groups(self, device_group, all_dgs):
        """Recursively collect all device groups including chained/nested ones."""
        all_dgs.append(device_group)
        for child_dg in device_group.DeviceGroup.find():
            self._collect_all_device_groups(child_dg, all_dgs)

    def get_device_group_obj_from_tags(self, tag_names: t.List[str]):
        # Ignore device groups  with the below names when all device groups are under purview
        ignored_golden_tag_names = ["NO_V6_PACKET_LOSS_EXPECTED"]
        ixia = none_throws(self.ixia)
        topologies = ixia.ixnetwork.Topology.find()
        device_group_objs = []
        for topology in topologies:
            all_dgs = []
            for device_group in topology.DeviceGroup.find():
                self._collect_all_device_groups(device_group, all_dgs)
            if not tag_names:
                ixia.logger.info(
                    f"No tag names provided. Flapping all device groups except with tag_name {ignored_golden_tag_names}"
                )
                for device_group in all_dgs:
                    ignored = False
                    for ignored_golden_tag_name in ignored_golden_tag_names:
                        if ignored_golden_tag_name in device_group.Name:
                            ixia.logger.info(
                                f"Ignoring device group {device_group.Name} with tag {ignored_golden_tag_name}"
                            )
                            ignored = True
                            break
                    if not ignored:
                        device_group_objs.append(device_group)
            else:
                for tag_name in tag_names:
                    for device_group in all_dgs:
                        if tag_name in device_group.Name:
                            ixia.logger.info(
                                f"For tag {tag_name} found {device_group.Name}"
                            )
                            device_group_objs.append(device_group)
        return device_group_objs

    def _collect_network_groups_from_dg(self, device_group, network_groups):
        """Recursively collect network groups from device group and its children."""
        for network_group in device_group.NetworkGroup.find():
            network_groups.append(network_group)
        for child_dg in device_group.DeviceGroup.find():
            self._collect_network_groups_from_dg(child_dg, network_groups)

    def get_network_group_name_regex(self, tag_names: t.List[str]):
        network_group_names = []
        ixia = none_throws(self.ixia)
        device_group_objs = self.get_device_group_obj_from_tags(tag_names=tag_names)
        for device_group_obj in device_group_objs:
            network_groups = []
            self._collect_network_groups_from_dg(device_group_obj, network_groups)
            for network_group in network_groups:
                network_group_names.append(network_group.Name)
        ixia.logger.info(f"Network group names: {network_group_names}")
        return "|".join(network_group_names)

    def _resolve_prefix_regex(
        self,
        prefix_flap_tag_names: t.Optional[t.List[str]],
        is_all_prefix_groups: bool,
    ) -> str:
        regex = ""
        if prefix_flap_tag_names:
            regex += self.get_network_group_name_regex(tag_names=prefix_flap_tag_names)
        elif is_all_prefix_groups:
            regex = self.get_network_group_name_regex(tag_names=[])
        if not regex:
            raise ValueError(
                "No network groups found for prefix flap. "
                f"prefix_flap_tag_names={prefix_flap_tag_names}, "
                f"is_all_prefix_groups={is_all_prefix_groups}"
            )
        return regex

    def _resolve_session_regex(
        self,
        session_flap_tag_names: t.Optional[t.List[str]],
        is_all_session_groups: bool,
    ) -> str:
        regex = ""
        if session_flap_tag_names:
            regex += self.get_bgp_peer_regex(tag_names=session_flap_tag_names)
        if is_all_session_groups is True:
            regex += self.get_bgp_peer_regex(tag_names=[])
        if not regex:
            raise ValueError(
                "No BGP peers found for session flap. "
                f"session_flap_tag_names={session_flap_tag_names}, "
                f"is_all_session_groups={is_all_session_groups}"
            )
        return regex

    async def run(
        self,
        input: taac_types.BaseInput,
        params: t.Dict[str, t.Any],
    ) -> None:
        ixia = none_throws(self.ixia)
        churn_mode = params["churn_mode"]
        enable_prefix_flap = params.get("enable_prefix_flap", False)
        enable_session_flap = params.get("enable_session_flap", False)
        is_all_prefix_groups = params.get("is_all_prefix_groups", False)
        is_all_session_groups = params.get("is_all_session_groups", False)
        session_flap_tag_names = params.get("session_flap_tag_names", None)
        prefix_flap_tag_names = params.get("prefix_flap_tag_names", None)
        churn_duration_s = params["churn_duration_s"]
        uptime_min_sec = params.get("uptime_min_sec", 15)
        uptime_max_sec = params.get("uptime_max_sec", 15)
        downtime_min_sec = params.get("downtime_min_sec", 15)
        downtime_max_sec = params.get("downtime_max_sec", 15)
        rerandomize_interval_s = params.get("rerandomize_interval_s", 0)
        uptime_sec, downtime_sec = pick_flap_timing(
            uptime_min_sec, uptime_max_sec, downtime_min_sec, downtime_max_sec
        )
        self.logger.info(
            f"Flap timing: uptime={uptime_sec}s, downtime={downtime_sec}s "
            f"(range [{uptime_min_sec}-{uptime_max_sec}] / [{downtime_min_sec}-{downtime_max_sec}])"
        )
        # Resolve regexes once before the flap loop
        prefix_flap_network_group_regex = None
        session_flap_bgp_peer_regex_resolved = None
        # todo (pavan) Add these as Enums
        if "prefix" in churn_mode:
            prefix_flap_network_group_regex = self._resolve_prefix_regex(
                prefix_flap_tag_names, is_all_prefix_groups
            )
        # todo (pavan) Add these as Enums
        if "session" in churn_mode:
            session_flap_bgp_peer_regex_resolved = self._resolve_session_regex(
                session_flap_tag_names, is_all_session_groups
            )
        # Apply initial flap timing
        apply_flap_timing(
            ixia=ixia,
            churn_mode=churn_mode,
            uptime_sec=uptime_sec,
            downtime_sec=downtime_sec,
            enable_prefix_flap=enable_prefix_flap,
            prefix_flap_network_group_regex=prefix_flap_network_group_regex,
            enable_session_flap=enable_session_flap,
            session_flap_bgp_peer_regex=session_flap_bgp_peer_regex_resolved,
        )
        # Re-randomize periodically during the churn duration
        if churn_duration_s > 0 and rerandomize_interval_s > 0:
            start = time.time()
            while (time.time() - start) < churn_duration_s:
                sleep_time = min(
                    rerandomize_interval_s, churn_duration_s - (time.time() - start)
                )
                if sleep_time <= 0:
                    break
                await asyncio.sleep(sleep_time)
                uptime_sec, downtime_sec = pick_flap_timing(
                    uptime_min_sec,
                    uptime_max_sec,
                    downtime_min_sec,
                    downtime_max_sec,
                )
                self.logger.info(
                    f"Re-randomizing flap timing: uptime={uptime_sec}s, downtime={downtime_sec}s"
                )
                apply_flap_timing(
                    ixia=ixia,
                    churn_mode=churn_mode,
                    uptime_sec=uptime_sec,
                    downtime_sec=downtime_sec,
                    enable_prefix_flap=enable_prefix_flap,
                    prefix_flap_network_group_regex=prefix_flap_network_group_regex,
                    enable_session_flap=enable_session_flap,
                    session_flap_bgp_peer_regex=session_flap_bgp_peer_regex_resolved,
                )
        elif churn_duration_s > 0:
            self.logger.info(
                f"Flap operation completed. Sleeping for {churn_duration_s} seconds"
            )
            await asyncio.sleep(churn_duration_s)
        else:
            self.logger.info("Flap operation completed (non-blocking).")
