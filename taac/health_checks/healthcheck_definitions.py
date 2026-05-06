# (c) Meta Platforms, Inc. and affiliates. Confidential and proprietary.

# pyre-unsafe
"""Canonical health check factory functions.

Every PointInTimeHealthCheck / SnapshotHealthCheck construction in TAAC
should use a factory from this module.  Gate test
``test_no_inline_healthcheck_construction`` enforces this.

Migration: as inline HC construction in test configs is replaced, the
corresponding factory is added here and the old call site is removed
from the gate-test allowlist.
"""
