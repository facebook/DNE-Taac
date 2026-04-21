# pyre-unsafe

import asyncio
import typing as t
from dataclasses import dataclass

from neteng.fboss.switch_config.thrift_mutable_types import PortSpeed
from taac.driver.fboss_switch import FbossSwitch
from taac.steps.step import Step
from taac.utils.driver_factory import async_get_device_driver
from taac.test_as_a_config import types as taac_types

SPEED_FLIP_PATCHER_NAME = "test_speed_flip_patcher"

SUPPORTED_51T_SPEED_COMBINATIONS = {
    (100, 100),
    (200, 400),
    (200, 200),
    (400, 400),
}


PLATFORM_SPEED_PROFILE_MAPPING = {
    "MONTBLANC": {
        PortSpeed.EIGHTHUNDREDG: "PROFILE_800G_8_PAM4_RS544X2N_OPTICAL",
        PortSpeed.FOURHUNDREDG: "PROFILE_400G_4_PAM4_RS544X2N_OPTICAL",
        PortSpeed.TWOHUNDREDG: "PROFILE_200G_4_PAM4_RS544X2N_OPTICAL",
        PortSpeed.HUNDREDG: "PROFILE_100G_4_NRZ_RS528_OPTICAL",
    },
    "MORGAN800CC": {
        PortSpeed.EIGHTHUNDREDG: "PROFILE_800G_8_PAM4_RS544X2N_OPTICAL",
        PortSpeed.FOURHUNDREDG: "PROFILE_400G_4_PAM4_RS544X2N_OPTICAL",
        PortSpeed.TWOHUNDREDG: "PROFILE_200G_4_PAM4_RS544X2N_OPTICAL",
        PortSpeed.HUNDREDG: "PROFILE_100G_4_NRZ_RS528_OPTICAL",
    },
    "WEDGE400C": {
        PortSpeed.FOURHUNDREDG: "PROFILE_400G_8_PAM4_RS544X2N_OPTICAL",
        PortSpeed.HUNDREDG: "PROFILE_100G_4_NRZ_RS528_OPTICAL",
        PortSpeed.TWOHUNDREDG: "PROFILE_200G_4_PAM4_RS544X2N_OPTICAL",
    },
    "WEDGE400": {
        PortSpeed.FOURHUNDREDG: "PROFILE_400G_8_PAM4_RS544X2N_OPTICAL",
        PortSpeed.HUNDREDG: "PROFILE_100G_4_NRZ_RS528_OPTICAL",
        PortSpeed.TWOHUNDREDG: "PROFILE_200G_4_PAM4_RS544X2N_OPTICAL",
    },
    "ELBERT": {
        PortSpeed.FOURHUNDREDG: "PROFILE_400G_8_PAM4_RS544X2N_OPTICAL",
        PortSpeed.HUNDREDG: "PROFILE_100G_4_NRZ_RS528_OPTICAL",
        PortSpeed.TWOHUNDREDG: "PROFILE_200G_4_PAM4_RS544X2N_OPTICAL",
    },
    "FUJI": {
        PortSpeed.FOURHUNDREDG: "PROFILE_400G_8_PAM4_RS544X2N_OPTICAL",
        PortSpeed.HUNDREDG: "PROFILE_100G_4_NRZ_RS528_OPTICAL",
        PortSpeed.TWOHUNDREDG: "PROFILE_200G_4_PAM4_RS544X2N_OPTICAL",
    },
    "DARWIN": {
        PortSpeed.FOURHUNDREDG: "PROFILE_400G_8_PAM4_RS544X2N_OPTICAL",
        PortSpeed.HUNDREDG: "PROFILE_100G_4_NRZ_RS528_OPTICAL",
        PortSpeed.TWOHUNDREDG: "PROFILE_200G_4_PAM4_RS544X2N_OPTICAL",
    },
    "YAMP": {
        PortSpeed.HUNDREDG: "PROFILE_100G_4_NRZ_RS528_OPTICAL",
        PortSpeed.TWOHUNDREDG: "PROFILE_200G_4_PAM4_RS544X2N_OPTICAL",
    },
    "MINIPACK": {
        PortSpeed.HUNDREDG: "PROFILE_100G_4_NRZ_RS528_OPTICAL",
        PortSpeed.TWOHUNDREDG: "PROFILE_200G_4_PAM4_RS544X2N_OPTICAL",
    },
}


class UnsupportedSpeedCombinationError(Exception):
    pass


@dataclass(frozen=True)
class DeviceInfo:
    ports: t.List[str]
    driver: FbossSwitch
    hostname: str
    hardware_type: str


class RegisterSpeedFlipPatcherStep(Step[taac_types.BaseInput]):
    STEP_NAME = taac_types.StepName.REGISTER_SPEED_FLIP_PATCHER
    OPERATING_SYSTEMS = ["FBOSS"]

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.registered_patcher_name: t.Optional[str] = None

    async def run(
        self,
        input: taac_types.BaseInput,
        params: t.Dict[str, t.Any],
    ) -> None:
        register_patcher = params["register_patcher"]
        port_state_change = params["port_state_change"]
        patcher_name = params.get("patcher_name", SPEED_FLIP_PATCHER_NAME)

        # Extract endpoints dict and get ports for THIS device only
        # Format: {"hostname1": ["port1"], "hostname2": ["port2"]}
        endpoints = params["endpoints"]

        # Get device info for all devices
        device_infos = await self._gather_device_infos(endpoints)

        speed_in_gbps = params.get("speed_in_gbps", 0)

        if port_state_change:
            await self._disable_device_ports(device_infos)

        # Register/unregister patchers for all devices
        if register_patcher:
            await self._register_speed_flip_patchers(
                device_infos=device_infos,
                speed_in_gbps=speed_in_gbps,
                patcher_name=patcher_name,
            )
        else:
            await self._unregister_speed_flip_patchers(
                patcher_name=patcher_name,
                device_infos=device_infos,
            )

        # Warmboot agent
        await self._warmboot_agent(device_infos=device_infos)

    async def _gather_device_infos(
        self, endpoints: t.Dict[str, t.List[str]]
    ) -> t.List[DeviceInfo]:
        device_infos = []
        for hostname, ports in endpoints.items():
            if not ports:
                self.logger.warning(
                    f"No ports specified for {hostname} in endpoints. Skipping speed flip patcher."
                )
                continue
            # Get device driver
            device_driver = await async_get_device_driver(hostname)
            await device_driver.async_wait_for_agent_configured()
            # Get hardware type from device attributes (populated by test bed chunker)
            hardware_type = self.device.attributes.hardware

            device_infos.append(
                DeviceInfo(
                    ports=ports,
                    # pyre-fixme[6]: For 2nd argument expected `FbossSwitch` but got
                    #  `AbstractSwitch`.
                    driver=device_driver,
                    hostname=hostname,
                    hardware_type=hardware_type,
                )
            )
        return device_infos

    async def _disable_device_ports(self, device_infos: t.List[DeviceInfo]) -> None:
        await asyncio.gather(
            *[
                device_info.driver.async_thrift_disable_enable_interfaces(
                    interface_names=device_info.ports, is_enable_port=False
                )
                for device_info in device_infos
            ]
        )

    async def _warmboot_agent(self, device_infos: t.List[DeviceInfo]) -> None:
        await asyncio.gather(
            *[
                # pyre-fixme[16]: `FbossSwitch` has no attribute `async_apply_patchers`.
                device_info.driver.async_apply_patchers(
                    taac_types.ApplyPatcherMethod.AGENT_WARMBOOT
                )
                for device_info in device_infos
            ]
        )
        await asyncio.gather(
            *[
                device_info.driver.async_wait_for_agent_configured()
                for device_info in device_infos
            ]
        )

    async def _register_speed_flip_patchers(
        self,
        device_infos: t.List[DeviceInfo],
        speed_in_gbps: int,
        patcher_name: str,
    ) -> None:
        """Register speed flip patcher"""
        speed_in_mbps = speed_in_gbps * 1000
        coros = []
        for device_info in device_infos:
            profile_id = PLATFORM_SPEED_PROFILE_MAPPING.get(
                device_info.hardware_type, {}
            )[speed_in_mbps]
            coros.append(
                # pyre-fixme[16]: `FbossSwitch` has no attribute
                #  `async_change_speed_patcher`.
                device_info.driver.async_change_speed_patcher(
                    device_info.ports,
                    desired_speed=PortSpeed(speed_in_mbps).name,
                    profile_id=profile_id,
                    patcher_name=patcher_name,
                )
            )
        await asyncio.gather(*coros)

    async def _unregister_speed_flip_patchers(
        self,
        patcher_name: str,
        device_infos: t.List[DeviceInfo],
    ) -> None:
        """Unregister speed flip patcher"""
        await asyncio.gather(
            *[
                device_info.driver.async_coop_unregister_patchers(patcher_name)
                for device_info in device_infos
            ]
        )

    async def validate_speed_flip_ports(
        self, device_info: DeviceInfo, speed: int
    ) -> None:
        """
        Validates that the requested speed flip is supported for 51T platforms.
        Raises UnsupportedSpeedCombinationError if unsupported speed combinations are detected.
        """
        # Only validate for supported hardware types
        SUPPORTED_HARDWARE = {
            "MONTBLANC",
            "MORGAN800CC",
        }
        if device_info.hardware_type not in SUPPORTED_HARDWARE:
            return
        # Map each port to its adjacent port
        port_to_adjacent = {
            port: self._get_51t_adjacent_port(port) for port in device_info.ports
        }
        # Get speeds for all adjacent ports
        adjacent_ports = list(port_to_adjacent.values())
        adjacent_speeds = await device_info.driver.async_get_interfaces_speed_in_Gbps(
            adjacent_ports
        )
        # Check for unsupported speed combinations
        violations = []
        for port, adjacent_port in port_to_adjacent.items():
            adjacent_speed = adjacent_speeds[adjacent_port]
            if (speed, adjacent_speed) not in SUPPORTED_51T_SPEED_COMBINATIONS and (
                adjacent_speed,
                speed,
            ) not in SUPPORTED_51T_SPEED_COMBINATIONS:
                violations.append(
                    f"Speed flip not supported for {port} <-> {adjacent_port} "
                    f"with speeds {speed} and {adjacent_speed}"
                )
        if violations:
            raise UnsupportedSpeedCombinationError(
                "Speed flip is not supported due to the following violations:\n"
                + "\n".join(violations)
            )

    def _get_51t_adjacent_port(self, port: str) -> str:
        pim, slot, num = port.split("/")
        if num == "1":
            return f"{pim}/{slot}/5"
        return f"{pim}/{slot}/1"
