# pyre-unsafe
import os
import typing as t

from taac.internal.steps.custom_step import CustomStep
from taac.internal.steps.system_reboot_step import (
    SystemRebootStep,
)
from taac.internal.steps.validation_step import ValidationStep
from taac.steps.allocate_cgroup_slice_memory_step import (
    AllocateCgroupSliceMemory,
)
from taac.steps.drain_undrain_step import DrainUndrainStep
from taac.steps.dummy_step import DummyStep
from taac.steps.ecmp_member_static_route_step import (
    EcmpMemberStaticRouteStep,
)
from taac.steps.interface_flap_step import InterfaceFlapStep
from taac.steps.invoke_ixia_api_step import InvokeIxiaApiStep
from taac.steps.longevity_step import LongevityStep
from taac.steps.mass_bgp_peer_toggle import MassBgpPeerToggle
from taac.steps.module_power_toggle_step import (
    ModulePowerToggleStep,
)
from taac.steps.register_patcher_step import RegisterPatcherStep
from taac.steps.register_port_channel_min_link_percentage_patchers import (
    RegisterPortChannelMinLinkPercentagePatchers,
)
from taac.steps.register_speed_flip_patcher_step import (
    RegisterSpeedFlipPatcherStep,
)
from taac.steps.run_ssh_cmd_step import RunSSHCmdStep
from taac.steps.run_task_step import RunTaskStep
from taac.steps.service_convergence_step import (
    ServiceConvergenceStep,
)
from taac.steps.service_interruption_step import (
    ServiceInterruptionStep,
)
from taac.steps.stable_state_chronos_node import ChronosNode
from taac.steps.step import Step
from taac.steps.verify_file_modification_time_step import (
    VerifyFileModificationTimeStep,
)
from taac.steps.verify_port_operational_state import (
    VerifyPortOperationalStateStep,
)
from taac.steps.verify_port_speed_step import VerifyPortSpeedStep
from taac.test_as_a_config import types as taac_types

TAAC_OSS = os.environ.get("TAAC_OSS", "").lower() in ("1", "true", "yes")

OSS_STEPS: t.List[t.Type[Step]] = [
    DummyStep,
    ServiceInterruptionStep,
    ServiceConvergenceStep,
    DrainUndrainStep,
    InterfaceFlapStep,
    LongevityStep,
    RunSSHCmdStep,
    SystemRebootStep,
    ValidationStep,
    CustomStep,
    RegisterPatcherStep,
    InvokeIxiaApiStep,
    AllocateCgroupSliceMemory,
    RunTaskStep,
    ChronosNode,
    MassBgpPeerToggle,
    EcmpMemberStaticRouteStep,
    RegisterPortChannelMinLinkPercentagePatchers,
    VerifyPortOperationalStateStep,
    ModulePowerToggleStep,
    VerifyPortSpeedStep,
    VerifyFileModificationTimeStep,
    RegisterSpeedFlipPatcherStep,
]

if not TAAC_OSS:
    from taac.internal.steps.internal_steps import INTERNAL_STEPS
else:
    INTERNAL_STEPS = []

ALL_STEPS: t.List[t.Type[Step]] = OSS_STEPS + INTERNAL_STEPS


STEP_NAME_TO_INPUT = {
    # pyre-ignore
    step.STEP_NAME: t.get_args(step.__orig_bases__[0])[0]
    for step in ALL_STEPS
}


NAME_TO_STEP: t.Dict[taac_types.StepName, t.Type[Step]] = {
    step.STEP_NAME: step for step in ALL_STEPS
}
