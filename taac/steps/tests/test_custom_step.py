# pyre-unsafe
import ipaddress
import time
import unittest
from dataclasses import dataclass
from typing import Any
from unittest.mock import AsyncMock, MagicMock, Mock, patch

from facebook.network.Address.thrift_types import BinaryAddress
from neteng.fboss.ctrl.thrift_types import NdpEntryThrift
from taac.constants import (
    TestCaseFailure,
    TestDevice,
    TestTopology,
)
from taac.internal.steps.custom_step import CustomStep
from taac.libs.parameter_evaluator import ParameterEvaluator
from taac.test_as_a_config.thrift_types import CustomStepInput, Step, TestConfig

BASE_PATH = "neteng.test_infra.dne.taac.internal.steps.custom_step"


class TestNdpClear(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        # Create mock objects for all required parameters
        self.name = "test_step"
        self.device = MagicMock(spec=TestDevice)
        self.device.name = "test_device"

        # Create mock structure for attributes with flat fields
        attributes_mock = MagicMock()
        attributes_mock.operating_system = "FBOSS"
        attributes_mock.role = ""
        attributes_mock.device_name = "test_device"
        attributes_mock.hardware = ""
        attributes_mock.ai_zone = ""
        self.device.attributes = attributes_mock

        self.topology = MagicMock(spec=TestTopology)
        self.test_case_results = []
        self.test_config = MagicMock(spec=TestConfig)
        self.test_case_name = "test_case"
        self.test_case_start_time = time.time()
        self.parameter_evaluator = MagicMock(spec=ParameterEvaluator)
        self.step = MagicMock(spec=Step)

        # Initialize CustomStep with all required parameters
        self.custom_step = CustomStep(
            name=self.name,
            device=self.device,
            topology=self.topology,
            test_case_results=self.test_case_results,
            test_config=self.test_config,
            test_case_name=self.test_case_name,
            test_case_start_time=self.test_case_start_time,
            parameter_evaluator=self.parameter_evaluator,
            step=self.step,
        )

        # Mock the driver since it is not initialized in tests
        self.driver_mock = AsyncMock()
        self.custom_step.driver = self.driver_mock

        # Mock the ixia since it is now required in test_ndp_clear
        self.ixia_mock = MagicMock()
        self.custom_step.ixia = self.ixia_mock

    @patch(f"{BASE_PATH}.CustomStep.test_ndp_clear")
    async def test_run_method(self, mock_test_ndp_clear):
        """Test the run method of CustomStep."""
        # Mock the input and params
        input_mock = MagicMock(spec=CustomStepInput)
        params = {"custom_step_name": "test_ndp_clear"}

        # Call the run method
        await self.custom_step.run(input_mock, params)

        # Verify that test_ndp_clear was called with the correct parameters
        mock_test_ndp_clear.assert_called_once_with(params)

    @patch("asyncio.sleep")
    async def test_ndp_clear_success(self, _):
        """Test successful NDP table clearing and restoration."""
        # Create mock NDP entries
        mock_ndp_entries = [
            NdpEntryThrift(
                ip=BinaryAddress(
                    addr=b"\x20\x01\x0d\xb8\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01"
                ),
                state="REACHABLE",
                port=1,
                mac="00:11:22:33:44:55",
            ),
            NdpEntryThrift(
                ip=BinaryAddress(
                    addr=b"\x20\x01\x0d\xb8\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02"
                ),
                state="REACHABLE",
                port=2,
                mac="00:11:22:33:44:66",
            ),
            NdpEntryThrift(
                ip=BinaryAddress(
                    addr=b"\x20\x01\x0d\xb8\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x03"
                ),
                state="STALE",
                port=3,
                mac="00:11:22:33:44:77",
            ),
        ]

        # Mock the initial NDP table
        self.custom_step.driver.async_get_ndp_table.side_effect = [
            # First call: return initial NDP table with reachable entries
            mock_ndp_entries,
            # Second call: return empty NDP table after clearing
            [],
            # Third call: return NDP table after pinging (with reachable entries restored)
            mock_ndp_entries,
        ]

        # Execute the test_ndp_clear function
        await self.custom_step.test_ndp_clear({})

        # Verify that the driver methods were called correctly
        self.custom_step.driver.async_get_ndp_table.assert_called()
        self.custom_step.driver.async_run_cmd_on_shell.assert_any_call(
            "fboss2 clear ndp"
        )

        # Verify that ping commands were executed for the reachable addresses
        expected_ping_cmd = "ping -c 1 2001:db8::1; ping -c 1 2001:db8::2"
        self.custom_step.driver.async_run_cmd_on_shell.assert_any_call(
            expected_ping_cmd
        )

        # Verify that IXIA traffic control methods were called
        self.ixia_mock.stop_traffic.assert_called_once()
        self.ixia_mock.start_traffic.assert_called_once()

    @patch("asyncio.sleep")
    async def test_ndp_clear_entries_not_cleared(self, _):
        """Test failure when NDP entries are not cleared properly."""
        # Create mock NDP entries
        mock_ndp_entries = [
            NdpEntryThrift(
                ip=BinaryAddress(
                    addr=b"\x20\x01\x0d\xb8\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01"
                ),
                state="REACHABLE",
                port=1,
                mac="00:11:22:33:44:55",
            ),
        ]

        # Mock the NDP table that still has reachable entries after clearing
        self.custom_step.driver.async_get_ndp_table.side_effect = [
            # First call: return initial NDP table with reachable entries
            mock_ndp_entries,
            # Second call: return NDP table that still has reachable entries (not cleared)
            mock_ndp_entries,
        ]

        # Mock async_everpaste_if_needed to return a simple string
        with patch(
            f"{BASE_PATH}.async_everpaste_if_needed",
            AsyncMock(return_value="Error: NDP table not cleared"),
        ):
            # Execute the test_ndp_clear function and expect it to raise TestCaseFailure
            with self.assertRaises(TestCaseFailure):
                await self.custom_step.test_ndp_clear({})

        # Verify that the driver methods were called correctly
        self.custom_step.driver.async_get_ndp_table.assert_called()
        self.custom_step.driver.async_run_cmd_on_shell.assert_called_once_with(
            "fboss2 clear ndp"
        )

    @patch("asyncio.sleep")
    async def test_ndp_clear_entries_not_restored(self, _):
        """Test failure when NDP entries are not restored after pinging."""
        # Create mock NDP entries for initial state
        initial_ndp_entries = [
            NdpEntryThrift(
                ip=BinaryAddress(
                    addr=b"\x20\x01\x0d\xb8\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01"
                ),
                state="REACHABLE",
                port=1,
                mac="00:11:22:33:44:55",
            ),
        ]

        # Create mock NDP entries for after pinging (with different address)
        after_ping_entries = [
            NdpEntryThrift(
                ip=BinaryAddress(
                    addr=b"\x20\x01\x0d\xb8\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02"
                ),
                state="REACHABLE",
                port=2,
                mac="00:11:22:33:44:66",
            ),
        ]

        # Mock the NDP table responses
        self.custom_step.driver.async_get_ndp_table.side_effect = [
            # First call: return initial NDP table with reachable entries
            initial_ndp_entries,
            # Second call: return empty NDP table after clearing
            [],
            # Third call: return NDP table after pinging with different entries
            after_ping_entries,
        ]

        # Mock async_everpaste_if_needed to return a simple string
        with patch(
            f"{BASE_PATH}.async_everpaste_if_needed",
            AsyncMock(return_value="Error: NDP entries not restored"),
        ):
            # Execute the test_ndp_clear function and expect it to raise TestCaseFailure
            with self.assertRaises(TestCaseFailure):
                await self.custom_step.test_ndp_clear({})

        # Verify that the driver methods were called correctly
        self.custom_step.driver.async_get_ndp_table.assert_called()
        self.custom_step.driver.async_run_cmd_on_shell.assert_any_call(
            "fboss2 clear ndp"
        )

        # Verify that IXIA traffic control methods were called
        self.ixia_mock.stop_traffic.assert_called_once()
        self.ixia_mock.start_traffic.assert_called_once()


class TestNdpConfigChange(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.name = "test_step"
        self.device = MagicMock()
        self.device.name = "test_device"
        self.topology = MagicMock()
        self.test_case_results = []
        self.test_config = MagicMock()
        self.test_case_name = "test_case"
        self.test_case_start_time = time.time()
        self.parameter_evaluator = MagicMock()
        self.step = MagicMock()

        self.custom_step = CustomStep(
            name=self.name,
            device=self.device,
            topology=self.topology,
            test_case_results=self.test_case_results,
            test_config=self.test_config,
            test_case_name=self.test_case_name,
            test_case_start_time=self.test_case_start_time,
            parameter_evaluator=self.parameter_evaluator,
            step=self.step,
        )

        self.driver_mock = AsyncMock()
        self.custom_step.driver = self.driver_mock

    @patch("asyncio.sleep", new_callable=AsyncMock)
    async def test_ndp_config_change(self, mock_sleep):
        # Mock IXIA and its methods
        ixia_mock = MagicMock()
        self.custom_step.ixia = ixia_mock

        @dataclass
        class TAddress:
            Values: list[str]
            _properties: dict[str, Any]

            def __init__(self, Values: list[str], **kwargs):
                self.Values = Values
                self._properties = {"counter": {"step": 0}}

            def Increment(self, start_value: str, step_value: int):
                self.Values = [ipaddress.IPv6Address(start_value) + step_value]

        @dataclass
        class IPv6:
            Name: str
            Address: TAddress
            Prefix: int

        # Mock the IXIA find_ipv6s method
        ixia_mock.find_ipv6s.return_value = [
            IPv6(
                Name="IPV6_D0_RDSW001.U000.C083.SNC1:ETH1/1/1",
                Address=TAddress(Values=["2401:db00:11a:8000:0:0:0:1"]),
                Prefix=Mock(Pattern="64"),
            ),
            IPv6(
                Name="IPV6_D0_RDSW001.U000.C083.SNC1:ETH1/2/1",
                Address=TAddress(Values=["2401:db00:11a:8001:0:0:0:1"]),
                Prefix=Mock(Pattern="64"),
            ),
        ]

        # Mock the initial NDP table (before config change)
        initial_ndp_entries = [
            NdpEntryThrift(
                ip=BinaryAddress(
                    addr=ipaddress.IPv6Address("2401:db00:11a:8000:0:0:0:1").packed
                ),
                state="REACHABLE",
            ),
            NdpEntryThrift(
                ip=BinaryAddress(
                    addr=ipaddress.IPv6Address("2401:db00:11a:8001:0:0:0:1").packed
                ),
                state="REACHABLE",
            ),
        ]

        # Mock the NDP table after config change with new addresses as REACHABLE
        after_config_change_entries = [
            NdpEntryThrift(
                ip=BinaryAddress(
                    addr=ipaddress.IPv6Address("2401:db00:11a:8000:0:0:0:2").packed
                ),
                state="REACHABLE",
            ),
            NdpEntryThrift(
                ip=BinaryAddress(
                    addr=ipaddress.IPv6Address("2401:db00:11a:8001:0:0:0:2").packed
                ),
                state="REACHABLE",
            ),
        ]

        # Mock the NDP table after 60s with old addresses in PROBE state
        probe_state_entries = [
            # New addresses still REACHABLE
            NdpEntryThrift(
                ip=BinaryAddress(
                    addr=ipaddress.IPv6Address("2401:db00:11a:8000:0:0:0:2").packed
                ),
                state="REACHABLE",
            ),
            NdpEntryThrift(
                ip=BinaryAddress(
                    addr=ipaddress.IPv6Address("2401:db00:11a:8001:0:0:0:2").packed
                ),
                state="REACHABLE",
            ),
            # Old addresses now in PROBE state
            NdpEntryThrift(
                ip=BinaryAddress(
                    addr=ipaddress.IPv6Address("2401:db00:11a:8000:0:0:0:1").packed
                ),
                state="PROBE",
            ),
            NdpEntryThrift(
                ip=BinaryAddress(
                    addr=ipaddress.IPv6Address("2401:db00:11a:8001:0:0:0:1").packed
                ),
                state="PROBE",
            ),
        ]

        # Mock the NDP table after 4.5 min with old addresses gone
        final_entries = [
            NdpEntryThrift(
                ip=BinaryAddress(
                    addr=ipaddress.IPv6Address("2401:db00:11a:8000:0:0:0:2").packed
                ),
                state="REACHABLE",
            ),
            NdpEntryThrift(
                ip=BinaryAddress(
                    addr=ipaddress.IPv6Address("2401:db00:11a:8001:0:0:0:2").packed
                ),
                state="REACHABLE",
            ),
        ]

        # Configure the sequence of NDP table calls
        self.custom_step.driver.async_get_ndp_table.side_effect = [
            initial_ndp_entries,  # Initial call to get original addresses
            after_config_change_entries,  # After config change - new addresses REACHABLE
            probe_state_entries,  # After 60s - old addresses in PROBE state
            final_entries,  # After 4.5 min - old addresses gone
        ]

        # Mock IXIA apply_changes
        ixia_mock.apply_changes = MagicMock()

        # Execute the test_ndp_config_change function
        await self.custom_step.test_ndp_config_change({})

        # Verify that IXIA methods were called
        ixia_mock.find_ipv6s.assert_called_once()
        ixia_mock.apply_changes.assert_called_once()

        # Verify that the driver methods were called correctly
        self.assertEqual(self.custom_step.driver.async_get_ndp_table.call_count, 4)

        # Verify that asyncio.sleep was called with the correct durations
        expected_sleep_calls = [
            unittest.mock.call(30),  # Wait for new addresses to be REACHABLE
            unittest.mock.call(60),  # Wait for old addresses to go to PROBE
            unittest.mock.call(5.5 * 60),  # Wait for old addresses to be flushed
        ]
        mock_sleep.assert_has_calls(expected_sleep_calls)
