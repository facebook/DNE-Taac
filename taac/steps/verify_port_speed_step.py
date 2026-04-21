# pyre-unsafe
import typing as t

from taac.steps.step import Step
from taac.test_as_a_config import types as taac_types


class VerifyPortSpeedStep(Step[taac_types.BaseInput]):
    STEP_NAME = taac_types.StepName.VERIFY_PORT_SPEED

    async def run(
        self,
        input: taac_types.BaseInput,
        params: t.Dict[str, t.Any],
    ) -> None:
        ports = params["ports"]
        speed_to_verify = params["speed_to_verify"]
        self.logger.info(
            f"Verifying that ports {ports} are running at {speed_to_verify}Gbps"
        )
        port_to_speed = await self.driver.async_get_interfaces_speed_in_Gbps(ports)
        for port, speed_in_gbps in port_to_speed.items():
            if speed_in_gbps != speed_to_verify:
                self.add_failure(
                    f"Speed verification failed for port {self.hostname}:{port}. Expected speed: {speed_to_verify}Gbps, Actual speed: {speed_in_gbps}Gbps"
                )
        self.raise_failure_if_exists()
        self.logger.info(
            f"Successfully verified that ports {ports} are operating at {speed_to_verify}Gbps"
        )
