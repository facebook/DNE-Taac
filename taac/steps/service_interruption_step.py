# (c) Meta Platforms, Inc. and affiliates. Confidential and proprietary.

# pyre-unsafe

import typing as t

from taac.driver.driver_constants import (
    AristaCriticalAgents,
    FbossSystemctlServiceName,
    OtherSystemctlServiceName,
    Service,
)
from taac.steps.step import Step
from taac.test_as_a_config import types as taac_types


class ServiceInterruptionStep(Step[taac_types.ServiceInterruptionInput]):
    STEP_NAME = taac_types.StepName.SERVICE_INTERRUPTION_STEP

    def service_factory(self, service: taac_types.Service) -> Service:
        service_value = taac_types.SERVICE_NAME_MAP[service]
        arista_service_names = {
            member.value: member.name for member in AristaCriticalAgents
        }
        other_systemctl_service_names = {
            member.value: member.name for member in OtherSystemctlServiceName
        }
        fboss_systemctl_service_names = {
            member.value: member.name for member in FbossSystemctlServiceName
        }
        if service_value in fboss_systemctl_service_names:
            return FbossSystemctlServiceName[
                fboss_systemctl_service_names[service_value]
            ]
        elif service_value in other_systemctl_service_names:
            return OtherSystemctlServiceName[
                other_systemctl_service_names[service_value]
            ]
        elif service_value in arista_service_names:
            return AristaCriticalAgents[arista_service_names[service_value]]
        raise

    async def run(
        self,
        input: taac_types.ServiceInterruptionInput,
        params: t.Dict[str, t.Any],
    ) -> None:
        # For Arista EOS based devices:
        # If you want to perform actions on specific agents, set Service to ARISTA_CUSTOM_AGENTS
        # and pass a list of specific agents in the 'agents' field.

        service = self.service_factory(input.name)
        agents = list(input.agents) if input.agents is not None else None

        if input.create_cold_boot_file and self.is_fboss:
            await self.driver.async_run_cmd_on_shell(
                "touch /dev/shm/fboss/warm_boot/cold_boot_once_0"
            )
        match input.trigger:
            case taac_types.ServiceInterruptionTrigger.SYSTEMCTL_STOP:
                await self.driver.async_stop_service(service, agents)
            case taac_types.ServiceInterruptionTrigger.SYSTEMCTL_START:
                await self.driver.async_start_service(service, agents)
            case taac_types.ServiceInterruptionTrigger.SYSTEMCTL_RESTART:
                await self.driver.async_restart_service(service, agents)
            case taac_types.ServiceInterruptionTrigger.CRASH:
                await self.driver.async_crash_service(service, agents)
