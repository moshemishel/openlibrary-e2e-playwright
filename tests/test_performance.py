"""Tests for the performance measurement utility (function 4 from the spec).

Each scenario is exercised twice -- once anonymously, once with login.
Metric values legitimately differ between the two modes (e.g. /account/books
is a redirect-to-login for anonymous users and the actual landing page
for authenticated ones), but the function's contract must hold either
way: returns a dict of the right shape, the breach flag matches the
threshold/metrics relationship, and the function never raises on a
slow page.

`test_perf_data_driven_anonymous` adds the JSON-file-driven sweep
required for the Data-Driven grading item. Anonymous-only -- auth is
already exercised by the explicit tests above, and doubling every case
would push runtime up without adding contract coverage.
"""

from typing import Any

import pytest
from playwright.async_api import Page

from utils.data_loader import load_data
from utils.performance import measure_page_performance

_PERF_CASES = load_data("perf_targets.json")

# Two extreme thresholds let us drive the breach flag deterministically:
#   * HIGH_THRESHOLD_MS -- generous enough that no real page breaches.
#   * LOW_THRESHOLD_MS -- 1 ms is smaller than any real load time, so any
#     non-null metric breaches.
HIGH_THRESHOLD_MS = 60_000
LOW_THRESHOLD_MS = 1

REQUIRED_METRICS = ("load_time_ms", "dom_content_loaded_ms", "first_paint_ms")


def _assert_record_shape(record: dict[str, Any], url: str, threshold: int) -> None:
    """Common shape checks for any record returned by measure_page_performance."""
    assert record["url"] == url
    assert record["threshold_ms"] == threshold
    assert isinstance(record["breached"], bool)
    assert isinstance(record["timestamp"], str)
    for key in REQUIRED_METRICS:
        assert key in record, f"missing metric key: {key}"
        # Each metric is either an int (rounded ms) or None when the
        # browser had no entry for it. We tolerate None to keep the
        # function honest about missing data.
        assert record[key] is None or isinstance(record[key], int)


async def test_record_shape_anonymous(anonymous_page: Page, config: dict[str, Any]) -> None:
    """Anonymous: returns a record with the three required metrics + meta."""
    url = config["base_url"]
    record = await measure_page_performance(anonymous_page, url, HIGH_THRESHOLD_MS)
    _assert_record_shape(record, url, HIGH_THRESHOLD_MS)


async def test_record_shape_authenticated(page: Page, config: dict[str, Any]) -> None:
    """Authenticated: returns a record with the three required metrics + meta."""
    url = f"{config['base_url']}/account/books"
    record = await measure_page_performance(page, url, HIGH_THRESHOLD_MS)
    _assert_record_shape(record, url, HIGH_THRESHOLD_MS)


async def test_breach_flag_true_on_low_threshold_anonymous(
    anonymous_page: Page, config: dict[str, Any]
) -> None:
    """A 1 ms threshold breaches on any real page load (function still returns)."""
    record = await measure_page_performance(anonymous_page, config["base_url"], LOW_THRESHOLD_MS)
    assert record["breached"] is True


async def test_breach_flag_true_on_low_threshold_authenticated(
    page: Page, config: dict[str, Any]
) -> None:
    """Same as above, but exercises the authenticated landing page."""
    record = await measure_page_performance(
        page, f"{config['base_url']}/account/books", LOW_THRESHOLD_MS
    )
    assert record["breached"] is True


async def test_no_breach_on_high_threshold_anonymous(
    anonymous_page: Page, config: dict[str, Any]
) -> None:
    """A 60 s threshold should not breach on a normally-responsive site."""
    record = await measure_page_performance(anonymous_page, config["base_url"], HIGH_THRESHOLD_MS)
    assert record["breached"] is False


async def test_no_breach_on_high_threshold_authenticated(
    page: Page, config: dict[str, Any]
) -> None:
    record = await measure_page_performance(
        page, f"{config['base_url']}/account/books", HIGH_THRESHOLD_MS
    )
    assert record["breached"] is False


@pytest.mark.parametrize(
    "case",
    _PERF_CASES,
    ids=[c["description"] for c in _PERF_CASES],
)
async def test_perf_data_driven_anonymous(
    case: dict[str, Any], anonymous_page: Page, config: dict[str, Any]
) -> None:
    """Cases from data/perf_targets.json.

    Sweeps a list of target URLs against per-case thresholds. The shape
    contract must hold for every target; the breach flag is whatever it
    turns out to be (we don't pin it -- the thresholds in JSON are real
    SLOs, not deterministic edge cases).
    """
    url = config["base_url"] + case["path"]
    record = await measure_page_performance(anonymous_page, url, case["threshold_ms"])
    _assert_record_shape(record, url, case["threshold_ms"])
