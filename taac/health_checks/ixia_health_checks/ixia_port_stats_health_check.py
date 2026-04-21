# pyre-unsafe
import typing as t

from ixnetwork_restpy.assistants.statistics.statviewassistant import StatViewAssistant
from taac.health_checks.abstract_health_check import (
    AbstractIxiaHealthCheck,
)
from neteng.test_infra.dne.taac.ixia.taac_ixia import TaacIxia as Ixia
from neteng.test_infra.dne.taac.utils.common import async_everpaste_str, async_get_fburl
from taac.utils.oss_taac_lib_utils import retryable
from taac.health_check.health_check import types as hc_types
from tabulate import tabulate


class IxiaPortStatsHealthCheck(AbstractIxiaHealthCheck[hc_types.BaseHealthCheckIn]):
    CHECK_NAME = hc_types.CheckName.IXIA_PORT_STATS_CHECK

    async def _run(
        self,
        obj: Ixia,
        input: hc_types.BaseHealthCheckIn,
        check_params: t.Dict[str, t.Any],
    ) -> hc_types.HealthCheckResult:
        self.enable_fault_statistics(obj)
        port_statistics_view = StatViewAssistant(obj.ixnetwork, "Port Statistics")
        latest_stats = self.get_port_statistics(port_statistics_view)
        exceeded_thresholds = self.verify_port_stats_threshold(latest_stats)

        if exceeded_thresholds:
            everpaste_url = await async_everpaste_str(
                tabulate(exceeded_thresholds, headers="keys", tablefmt="simple_grid")
            )
            everpaste_fburl = await async_get_fburl(everpaste_url)
            inline_summary = [
                f"{t['identifier']}: CRC={t['CRC Errors']}, LocalFaults={t['Local Faults']}, RemoteFaults={t['Remote Faults']}"
                for t in exceeded_thresholds[:5]
            ]
            suffix = (
                f" (+{len(exceeded_thresholds) - 5} more)"
                if len(exceeded_thresholds) > 5
                else ""
            )
            return hc_types.HealthCheckResult(
                status=hc_types.HealthCheckStatus.FAIL,
                message=f"Packet loss exceeded the defined threshold(s): "
                f"{inline_summary}{suffix}. Full details: {everpaste_fburl}",
            )
        return hc_types.HealthCheckResult(
            status=hc_types.HealthCheckStatus.PASS,
        )

    def enable_fault_statistics(self, ixia: Ixia) -> None:
        port_statistics = ixia.ixnetwork.Globals.Statistics.StatFilter.PortStatistics
        port_statistics.LinkFaultState = "True"
        port_statistics.LocalFaults = "True"
        port_statistics.RemoteFaults = "True"

    @retryable(num_tries=3, sleep_time=2)
    def get_port_statistics(
        self,
        view: StatViewAssistant,
    ) -> t.List:
        stats = []
        view_name = view._ViewName
        for row in view.Rows:
            stat = {
                "identifier": row["Port Name"],
                "CRC Errors": float(row["CRC Errors"]),
                "Local Faults": float(row["Local Faults"]),
                "Remote Faults": float(row["Remote Faults"]),
                "view": view_name,
            }
            stats.append(stat)
        return stats

    def verify_port_stats_threshold(
        self,
        latest_stats: t.List[t.Dict[str, t.Any]],
        threshold: float = 0.0,
    ) -> t.List[t.Dict[str, t.Any]]:
        """
        Verify if the port stats exceed the given threshold.

        Args:
            latest_stats: A list of port statistics.
            threshold: The threshold value to compare against (default is 0.0).

        Returns:
            A list of dictionaries containing the ports that exceeded the threshold.
        """
        exceeded_thresholds = []

        for stat in latest_stats:
            identifier = stat["identifier"]
            crc_errors = stat["CRC Errors"]
            local_faults = stat["Local Faults"]
            remote_faults = stat["Remote Faults"]

            if (
                crc_errors > threshold
                or local_faults > threshold
                or remote_faults > threshold
            ):
                exceeded_thresholds.append(
                    {
                        "identifier": identifier,
                        "CRC Errors": crc_errors,
                        "Local Faults": local_faults,
                        "Remote Faults": remote_faults,
                    }
                )

        return exceeded_thresholds
