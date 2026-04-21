# pyre-unsafe
import os
import threading
import time
import typing as t
from collections import defaultdict
from threading import Thread

TAAC_OSS = os.environ.get("TAAC_OSS", "").lower() in ("1", "true", "yes")

from ixia.ixia import types as ixia_types
from ixnetwork_restpy.assistants.statistics.statviewassistant import (
    StatViewAssistant as IxnStatViewAssistant,
)
from taac.ixia.ixia import Ixia
from neteng.test_infra.dne.taac.utils.oss_taac_lib_utils import none_throws, retryable
from uhd_restpy.assistants.statistics.statviewassistant import (
    StatViewAssistant as UhdStatViewAssistant,
)

StatViewAssistant = t.Union[IxnStatViewAssistant, UhdStatViewAssistant]

DEFAULT_SAMPLE_RATE = 2  # seconds

VIEW_TO_IDENTIFIER: t.Dict[str, str] = {
    "Traffic Item Statistics": "Traffic Item",
}

TRAFFIC_ITEM_VIEW = "Traffic Item Statistics"

PTP_DRILL_DOWN_VIEW = "PTP Drill Down"


PTP_CONFIGURED_ROLE = "Configured Role"
PTP_STATE = "PTP State"
PTP_PROTOCOL = "Protocol"
PTP_DEVICE_NUM = "Device#"
PTP_OFFSET_NS = "Offset [ns]"


class TaacIxia(Ixia, Thread):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        Thread.__init__(self)
        self.capturing: bool = False
        self.captured_stats = defaultdict(dict)
        self.captured_stats_traffic = defaultdict(dict)
        self.captured_ptp_drill_down_stats = defaultdict(dict)
        self.sample_time: int = DEFAULT_SAMPLE_RATE
        self.test_case_uuid: t.Optional[str] = None
        self.paused = False
        self._in_flight = False
        self.saved_configs = {}
        self._snapshot_lock = threading.Lock()

        self.traffic_item_view_assistant = None
        self.ptp_drill_down_view_assistant = None

    @retryable(sleep_time=2, num_tries=100, print_ex=True)
    def start_capturing(self, sample_time: int):
        """
        Start capturing statistics.
        Args:
            sample_time (int): Time interval between samples.
        """

        while self.capturing:
            try:
                if not self.paused:
                    self._in_flight = True
                    timestamp = int(time.time())
                    uuid = none_throws(self.test_case_uuid)
                    with self._snapshot_lock:
                        # Capture traffic rate statistics
                        self._capture_traffic_rate_stats(
                            self.traffic_item_view_assistant, uuid, timestamp
                        )
                        # Capture packet loss statistics
                        self._capture_packet_loss_stats(
                            self.traffic_item_view_assistant, uuid, timestamp
                        )
                        # Capture PTP drill down statistics
                        self._capture_ptp_drill_down_stats(
                            self.ptp_drill_down_view_assistant, uuid, timestamp
                        )
            finally:
                self._in_flight = False
            time.sleep(sample_time)

    def _capture_traffic_rate_stats(
        self,
        view_assistant: t.Optional[StatViewAssistant],
        uuid: str,
        timestamp: float,
    ):
        """
        Capture traffic rate statistics.
        """
        if not view_assistant:
            return
        try:
            latest_stats_traffic = self.get_traffic_rate_statistics(view_assistant)
            self.captured_stats_traffic[uuid][timestamp] = latest_stats_traffic
            self.captured_stats_traffic[uuid]["latest"] = latest_stats_traffic
        except Exception as e:
            self.logger.debug(
                f"Encountered error when capturing traffic rate statistics: {e}"
            )

    def _capture_packet_loss_stats(
        self,
        view_assistant: t.Optional[StatViewAssistant],
        uuid: str,
        timestamp: float,
    ):
        """
        Capture packet loss statistics
        """
        if not view_assistant:
            return
        try:
            latest_stats = self.get_packet_loss_statistics(view_assistant)
            self.captured_stats[uuid][timestamp] = latest_stats
            self.captured_stats[uuid]["latest"] = latest_stats
        except Exception as e:
            self.logger.debug(
                f"Encountered error when capturing packet loss statistics: {e}"
            )

    def _capture_ptp_drill_down_stats(
        self,
        ptp_drill_down_view_assistant: t.Optional[StatViewAssistant],
        uuid: str,
        timestamp: float,
    ):
        """
        Capture PTP drill down statistics.
        """
        if not ptp_drill_down_view_assistant:
            return
        try:
            latest_ptp_drill_down_stats = self.get_ptp_drill_down_statistics(
                ptp_drill_down_view_assistant
            )
            self.captured_ptp_drill_down_stats[uuid][timestamp] = (
                latest_ptp_drill_down_stats
            )
        except Exception as e:
            self.logger.debug(
                f"Encountered error when capturing PTP drill down statistics: {e}"
            )

    @retryable(sleep_time=2, num_tries=100)
    def get_packet_loss_statistics(
        self,
        view: StatViewAssistant,
    ) -> t.List:
        stats = []
        view_name = view._ViewName
        for row in view.Rows:
            stat = {}
            stat["identifier"] = row[VIEW_TO_IDENTIFIER[view_name]]
            if "Packet Loss Duration (ms)" in row.Columns:
                raw = row["Packet Loss Duration (ms)"]
                stat["packet_loss_duration"] = float(raw) if raw != "" else 0.0
            if "Loss %" in row.Columns:
                raw = row["Loss %"]
                stat["packet_loss_percentage"] = float(raw) if raw != "" else 0.0
            if "Frames Delta" in row.Columns:
                raw = row["Frames Delta"]
                stat["frame_delta"] = float(raw) if raw != "" else 0.0
            stat["view"] = view_name
            stats.append(stat)
        return stats

    @retryable(sleep_time=2, num_tries=100)
    def get_traffic_rate_statistics(
        self,
        view: StatViewAssistant,
    ) -> t.List:
        stats = []
        view_name = view._ViewName
        for row in view.Rows:
            stat = {}
            stat["identifier"] = row[VIEW_TO_IDENTIFIER[view_name]]
            if "Tx Rate (Mbps)" in row.Columns:
                stat["Tx Rate"] = float(row["Tx Rate (Mbps)"])
            if "Rx Rate (Mbps)" in row.Columns:
                stat["Rx Rate"] = float(row["Rx Rate (Mbps)"])
            stat["view"] = view_name
            stats.append(stat)
        return stats

    @retryable(sleep_time=2, num_tries=100)
    def get_ptp_drill_down_statistics(
        self, ptp_drill_down_view: StatViewAssistant
    ) -> t.Dict:
        ptp_stats = {}
        for row in ptp_drill_down_view.Rows:
            id = f"{row[PTP_PROTOCOL]}_{row[PTP_DEVICE_NUM]}"
            stat = {
                "clock_role": row[PTP_CONFIGURED_ROLE],
                "offset_ns": int(row[PTP_OFFSET_NS]),
                "ptp_state": row[PTP_STATE],
            }
            ptp_stats[id] = stat
        return ptp_stats

    def log_to_scuba_ixia_packet_loss(self, test_case_uuid: str) -> None:
        if TAAC_OSS:
            self.logger.info(
                f"OSS mode: Skipping Scuba logging for test case {test_case_uuid}. "
                "Packet loss stats available via get_packet_loss_stats()."
            )
            return

        from rfe.scubadata.scubadata_py3 import Sample, ScubaData

        samples = []
        while self._in_flight:
            time.sleep(0.1)
        for timestamp, stats in self.captured_stats[test_case_uuid].items():
            if timestamp == "latest":
                continue
            for stat in stats:
                sample = Sample()
                sample.addTimestamp(ScubaData.TIME_COLUMN, timestamp)
                sample.addNormalValue("identifier", stat["identifier"])
                sample.addNormalValue("view", stat["view"])
                sample.addNormalValue("test_case_uuid", test_case_uuid)
                if "packet_loss_duration" in stats:
                    sample.addDoubleValue(
                        "packet_loss_duration", stat["packet_loss_duration"]
                    )
                if "packet_loss_percentage" in stat:
                    sample.addDoubleValue(
                        "packet_loss_percentage", stat["packet_loss_percentage"]
                    )
                if "frame_delta" in stat:
                    sample.addDoubleValue("frame_delta", stat["frame_delta"])
                samples.append(sample)
        self.logger.info(f"Logging {len(samples)} samples to scuba")
        with ScubaData("ixia_packet_loss") as scubadata:
            try:
                for sample in samples:
                    scubadata.add_sample(sample)
            except Exception as ex:
                self.logger.error(f"Error logging result to scuba: {ex}")

    @retryable(sleep_time=2, num_tries=3)
    def get_latest_stats(
        self,
        max_timeout_sec: int = 180,
        since_time: float = 0,
    ) -> t.List:
        """
        Get the latest packet loss stats
        Args:
            max_timeout_sec (int, optional): Maximum timeout in seconds. Defaults to 120.
            since_time (float, optional): If provided, only return stats with a timestamp >= since_time.
        """
        timeout_time = time.time() + max_timeout_sec
        packet_loss_stats = self.captured_stats[self.test_case_uuid]
        try:
            while not (
                packet_loss_stats and next(reversed(packet_loss_stats)) > since_time
            ):
                if time.time() > timeout_time:
                    raise Exception("Timeout waiting for stats")
                time.sleep(0.1)
            return packet_loss_stats["latest"]
        except Exception:
            # Acquire lock to serialize with the background capture thread's
            # TakeCsvSnapshot calls. The IXIA chassis only allows one snapshot
            # at a time ("Snapshot DefaultSnapshotSettings already in progress").
            # Use a timeout to avoid blocking the asyncio event loop indefinitely.
            if not self._snapshot_lock.acquire(timeout=600):
                self.logger.warning(
                    "Timed out waiting for IXIA snapshot lock, proceeding without lock"
                )
                return self.get_packet_loss_statistics(self.traffic_item_view_assistant)
            try:
                return self.get_packet_loss_statistics(self.traffic_item_view_assistant)
            finally:
                self._snapshot_lock.release()

    def get_latest_stats_traffic(
        self,
        max_timeout_sec: int = 120,
        since_time: float = 0,
    ) -> t.List:
        """
        Get the latest traffic rate stats.
        Args:
            max_timeout_sec (int, optional): Maximum timeout in seconds. Defaults to 120.
            since_time (float, optional): If provided, only return stats with a timestamp >= since_time.
        """
        timeout_time = time.time() + max_timeout_sec
        traffic_rate_stats = self.captured_stats_traffic[self.test_case_uuid]
        while not (
            traffic_rate_stats and next(reversed(traffic_rate_stats)) > since_time
        ):
            if time.time() > timeout_time:
                raise Exception("Timeout waiting for stats")
            time.sleep(0.1)
        return self.captured_stats_traffic[self.test_case_uuid]["latest"]

    def run(self):
        self.capturing = True
        self.start_capturing(self.sample_time)

    def export_json_config(self) -> str:
        json_config = self.session.Ixnetwork.ResourceManager.ExportConfig(
            ["/descendant-or-self::*"],
            False,
            "json",
        )
        return json_config

    def export_and_save_config(self) -> None:
        self.logger.info(f"Saving ixia config for {self.test_case_uuid}")
        json_config = self.export_json_config()
        self.saved_configs[self.test_case_uuid] = json_config

    def import_json_config(self, json_config: str) -> None:
        self.session.Ixnetwork.ResourceManager.ImportConfig(json_config, False)
        self.start_and_verify_protocols()
        self.enable_traffic()
        self.start_traffic(regenerate_traffic_items=True)
        time.sleep(5)
        self.stop_traffic()
        self.enable_traffic(enable=False)

    def import_saved_config(self) -> None:
        self.logger.info(f"Importing saved ixia config for {self.test_case_uuid}")
        self.import_json_config(self.saved_configs[self.test_case_uuid])

    # =========================================================================
    # .ixncfg file-based caching methods (for chassis persistence)
    # =========================================================================

    def save_config_to_chassis(self, config_path: str) -> bool:
        """
        Save current IXIA configuration to chassis as .ixncfg file.

        This allows the configuration to be reloaded on subsequent test runs,
        significantly reducing IXIA setup time.

        Args:
            config_path: Full path on chassis where to save the config
                         (e.g., "/root/taac_configs/bag002_snc1.ixncfg")

        Returns:
            True if save was successful, False otherwise
        """
        try:
            self.logger.info(f"Saving IXIA config to chassis: {config_path}")
            self.session.Ixnetwork.SaveConfig(config_path)
            self.logger.info(f"Successfully saved IXIA config: {config_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to save IXIA config to chassis: {e}")
            return False

    def load_config_from_chassis(self, config_path: str) -> bool:
        """
        Load IXIA configuration from chassis .ixncfg file.

        If the config file exists and can be loaded, this is much faster than
        setting up IXIA from scratch (~1-2 min vs ~10-15 min).

        Args:
            config_path: Full path on chassis to load config from
                         (e.g., "/root/taac_configs/bag002_snc1.ixncfg")

        Returns:
            True if load was successful, False otherwise (fallback to full setup)
        """
        try:
            self.logger.info(
                f"Attempting to load IXIA config from chassis: {config_path}"
            )
            self.session.Ixnetwork.LoadConfig(config_path)
            self.logger.info(f"Successfully loaded IXIA config: {config_path}")

            # After loading, start protocols and verify
            self.start_and_verify_protocols()
            return True
        except Exception as e:
            self.logger.info(
                f"Could not load IXIA config from {config_path}: {e}. "
                "Will fall back to full setup."
            )
            return False

    def enable_protocol(self, enable: bool = True) -> None:
        if enable:
            self.logger.info("Enabling protocols")
            self.start_protocols()
        else:
            self.logger.info("Disabling protocols")
            self.stop_protocols()

    def wait_for_view_assistants_ready(self):
        self.traffic_item_view_assistant = self._get_traffic_item_view()
        self.ptp_drill_down_view_assistant = self._get_ptp_drill_down_view()

    @retryable(sleep_time=5, num_tries=2)
    def _get_ptp_drill_down_view(
        self,
    ) -> t.Optional[StatViewAssistant]:
        StatViewAssistant = (
            UhdStatViewAssistant if self.is_uhd_chassis else IxnStatViewAssistant
        )
        ptp_enabled = False
        protocols_summary = StatViewAssistant(self.ixnetwork, "Protocols Summary")
        for row in protocols_summary.Rows:
            if row["Protocol Type"] == "PTP":
                self.logger.info("PTP is enabled in the ixia setup")
                ptp_enabled = True
                break
        if not ptp_enabled:
            self.logger.debug("PTP is not enabled in the ixia setup")
            return
        try:
            _view = self.ixnetwork.Statistics.View.find(Caption=PTP_DRILL_DOWN_VIEW)
            _view.Refresh()
            view = StatViewAssistant(self.ixnetwork, PTP_DRILL_DOWN_VIEW, Timeout=60)
            return view
        except Exception as e:
            if "has no data available" in str(e):
                raise e
            self.logger.error(f"Error getting PTP drill down view: {e}")

    @retryable(sleep_time=5, num_tries=2)
    def _get_traffic_item_view(self) -> t.Optional[StatViewAssistant]:
        StatViewAssistant = (
            UhdStatViewAssistant if self.is_uhd_chassis else IxnStatViewAssistant
        )
        all_traffic_items = self.get_traffic_items()
        enabled_traffic_items = [
            traffic_item for traffic_item in all_traffic_items if traffic_item.Enabled
        ]
        traffic_item_tracking_enabled = False
        for traffic_item in enabled_traffic_items:
            if (
                ixia_types.TRAFFIC_STATS_TRACKING_TYPE_MAP[
                    ixia_types.TrafficStatsTrackingType.TRAFFIC_ITEM
                ]
                in traffic_item.Tracking.find().TrackBy
            ):
                self.logger.debug(
                    f"Traffic item tracking is enabled for {traffic_item}"
                )
                traffic_item_tracking_enabled = True
                break
        if not traffic_item_tracking_enabled:
            self.logger.debug(
                f"Traffic item tracking is not enabled for {enabled_traffic_items}"
            )
            return
        try:
            traffic_item_view = StatViewAssistant(
                self.ixnetwork, TRAFFIC_ITEM_VIEW, Timeout=60
            )
            return traffic_item_view
        except Exception as e:
            self.logger.error(f"Error getting traffic item views: {e}")
            raise e
