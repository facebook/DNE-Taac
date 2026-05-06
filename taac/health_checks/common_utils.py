# pyre-unsafe
import sys
import typing as t

from taac.health_checks.constants import COMPARISON_OPERATORS
from taac.utils.common import async_everpaste_str, async_get_fburl
from taac.health_check.health_check import types as hc_types


def evaluate_comparison(
    val1: float,
    comparison_type: hc_types.ComparisonType,
    val2: t.Union[str, float],
    lower_bound_str: t.Optional[str] = None,
    upper_bound_str: t.Optional[str] = None,
) -> bool:
    if comparison_type == hc_types.ComparisonType.BETWEEN:
        lower_bound = float(lower_bound_str) if lower_bound_str else 0
        upper_bound = float(upper_bound_str) if upper_bound_str else sys.maxsize
        return COMPARISON_OPERATORS[comparison_type](val1, lower_bound, upper_bound)
    return COMPARISON_OPERATORS[comparison_type](val1, float(val2))


async def async_get_everpaste_fburl_if_needed(
    str_val: t.Optional[str], min_chars: int = 100
) -> t.Optional[str]:
    if not str_val:
        return None
    return (
        await async_get_fburl(await async_everpaste_str(str_val))
        if len(str_val) > min_chars
        else str_val
    )
