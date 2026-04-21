# (c) Meta Platforms, Inc. and affiliates. Confidential and proprietary.

# pyre-unsafe

"""
EOS-specific tasks for TAAC.

Tasks in this module operate on Arista EOS devices using the AristaSwitch driver
directly (EOS CLI via FCR), rather than COOP patchers used by FBOSS tasks.
"""

import ipaddress
import typing as t

from taac.tasks.base_task import BaseTask
from taac.utils import arista_utils


class ConfigureEosParallelBgpPeers(BaseTask):
    """
    Configure parallel BGP peers on an Arista EOS device.

    This is the EOS equivalent of ConfigureParallelBgpPeers (which uses COOP
    patchers for FBOSS devices). It directly configures the Arista switch by:
    1. Assigning IP addresses to the specified interfaces
    2. Creating BGP neighbor configurations for each peer

    Supports multiple sessions with multiple IPs on the same interface.

    Example params:
        {
            "hostname": "bag002.snc1",
            "config_json": {
                "Ethernet3/25/1": [
                    {
                        "starting_ip": "2401:db00:e50d:11:8::10",
                        "increment_ip": "::2",
                        "gateway_starting_ip": "2401:db00:e50d:11:8::11",
                        "gateway_increment_ip": "::2",
                        "num_sessions": 100,
                        "remote_as_4_byte": 65000,
                        "remote_as_4_byte_step": 0,
                        "peer_group_name": "PEERGROUP_EBGP_V6",
                        "prefix_length": 127,
                        "description": "IXIA eBGP peer",
                        "ipv4_unicast": false,
                        "ipv6_unicast": true,
                        "all_secondary": false,                 # Required only in case of IPv4 addresses
                        "clear_existing": false,
                        "use_peer_group_syntax": false,         # TODO: Remove this once we have a way to detect peer group syntax, True by default
                    }
                ]
            }
        }
    """

    NAME = "configure_eos_parallel_bgp_peers"

    async def run(self, params: t.Dict[str, t.Any]) -> None:
        from taac.internal.driver.arista_switch import (
            AristaSwitch,
        )

        hostname = params["hostname"]
        config_json = self.merge_config(params)

        driver = AristaSwitch(hostname, logger=self.logger)

        for interface, configs in config_json.items():
            all_ipv4_ips: t.List[str] = []
            all_ipv6_ips: t.List[str] = []
            bgp_neighbor_args = []

            for config in configs:
                num_sessions = config["num_sessions"]
                starting_ip = config["starting_ip"]
                increment_ip = config["increment_ip"]
                gateway_starting_ip = config["gateway_starting_ip"]
                gateway_increment_ip = config["gateway_increment_ip"]
                prefix_length = config["prefix_length"]
                remote_as_4_byte = config["remote_as_4_byte"]
                remote_as_4_byte_step = config.get("remote_as_4_byte_step", 0)

                local_addresses = self.create_ip_addresses(
                    starting_ip, increment_ip, num_sessions
                )
                peer_addresses = self.create_ip_addresses(
                    gateway_starting_ip, gateway_increment_ip, num_sessions
                )

                # Collect local IPs for interface assignment, separated by family
                for addr in local_addresses:
                    ip_with_prefix = f"{addr}/{prefix_length}"
                    if isinstance(ipaddress.ip_address(addr), ipaddress.IPv4Address):
                        all_ipv4_ips.append(ip_with_prefix)
                    else:
                        all_ipv6_ips.append(ip_with_prefix)

                # Collect BGP neighbor configs
                config_only_interface_ip = config.get("config_only_interface_ip", False)
                if not config_only_interface_ip:
                    for i, peer_addr in enumerate(peer_addresses):
                        remote_asn = remote_as_4_byte + i * remote_as_4_byte_step
                        bgp_neighbor_args.append(
                            self._build_bgp_neighbor_kwargs(
                                config, peer_addr, remote_asn, interface
                            )
                        )

            # Step 1: Assign IPs to the interface
            total_ips = len(all_ipv4_ips) + len(all_ipv6_ips)
            self.logger.info(f"Configuring {total_ips} IP addresses on {interface}")
            await arista_utils.configure_interface_secondary_ips(
                driver,
                interface,
                ipv4_addresses=all_ipv4_ips or None,
                ipv6_addresses=all_ipv6_ips or None,
                clear_existing=configs[0].get("clear_existing", False),
                all_secondary=configs[0].get("all_secondary", False),
                logger_instance=self.logger,
            )

            # Step 2: Create BGP neighbors
            if bgp_neighbor_args:
                self.logger.info(
                    f"Creating {len(bgp_neighbor_args)} BGP neighbors on {interface}"
                )
                for kwargs in bgp_neighbor_args:
                    await driver.async_create_bgp_neighbor(**kwargs)

        self.logger.info(f"Finished configuring EOS parallel BGP peers on {hostname}")

    def merge_config(
        self, params: t.Dict[str, t.Any]
    ) -> t.Dict[str, t.List[t.Dict[str, t.Any]]]:
        """Merge config_json from peer_configs list or parse single config_json."""
        import json

        if "peer_configs" in params and params["peer_configs"]:
            config_json: t.Dict[str, t.List[t.Dict[str, t.Any]]] = {}
            for peer_config in params["peer_configs"]:
                peer_config_json = json.loads(peer_config["config_json"])
                for interface, configs in peer_config_json.items():
                    if interface in config_json:
                        config_json[interface].extend(configs)
                    else:
                        config_json[interface] = configs
            return config_json
        else:
            return json.loads(params["config_json"])

    def create_ip_addresses(
        self,
        starting_ip: str,
        increment_ip: str,
        count: int,
    ) -> t.List[str]:
        starting_ip_int = int(ipaddress.ip_address(starting_ip))
        increment_ip_int = int(ipaddress.ip_address(increment_ip))
        ip_addresses = []
        for i in range(count):
            new_address = str(
                ipaddress.ip_address(starting_ip_int + increment_ip_int * i)
            )
            ip_addresses.append(new_address)
        return ip_addresses

    def _build_bgp_neighbor_kwargs(
        self,
        config: t.Dict[str, t.Any],
        peer_addr: str,
        remote_asn: int,
        interface: str,
    ) -> t.Dict[str, t.Any]:
        """Build keyword arguments for async_create_bgp_neighbor from config dict."""
        kwargs: t.Dict[str, t.Any] = {
            "peer_ip_addr": ipaddress.ip_address(peer_addr),
            "remote_as": remote_asn,
            "update_source": interface,
        }
        if config.get("description"):
            kwargs["description"] = config["description"]
        if config.get("peer_group_name"):
            kwargs["peer_group"] = config["peer_group_name"]

        kwargs["use_peer_group_syntax"] = config.get("use_peer_group_syntax", True)

        kwargs["ipv4_unicast"] = config.get("ipv4_unicast", True)
        kwargs["ipv6_unicast"] = config.get("ipv6_unicast", False)
        kwargs["activate"] = config.get("activate", True)

        if config.get("route_map_in"):
            kwargs["route_map_in"] = config["route_map_in"]
        if config.get("route_map_out"):
            kwargs["route_map_out"] = config["route_map_out"]
        if config.get("next_hop_self"):
            kwargs["next_hop_self"] = True
        if config.get("send_community"):
            kwargs["send_community"] = True
        if config.get("maximum_routes") is not None:
            kwargs["maximum_routes"] = config["maximum_routes"]
            if config.get("maximum_routes_warning_limit") is not None:
                kwargs["maximum_routes_warning_limit"] = config[
                    "maximum_routes_warning_limit"
                ]
            if config.get("maximum_routes_warning_only"):
                kwargs["maximum_routes_warning_only"] = True
        if config.get("out_delay") is not None:
            kwargs["out_delay"] = config["out_delay"]
        if config.get("timers_keepalive") is not None:
            kwargs["timers_keepalive"] = config["timers_keepalive"]
        if config.get("timers_holdtime") is not None:
            kwargs["timers_holdtime"] = config["timers_holdtime"]
        if config.get("local_as") is not None:
            kwargs["local_as"] = config["local_as"]
            kwargs["local_as_no_prepend"] = config.get("local_as_no_prepend", False)
            kwargs["local_as_replace_as"] = config.get("local_as_replace_as", False)
            kwargs["local_as_fallback"] = config.get("local_as_fallback", False)
        if config.get("graceful_restart_helper"):
            kwargs["graceful_restart_helper"] = True

        return kwargs
