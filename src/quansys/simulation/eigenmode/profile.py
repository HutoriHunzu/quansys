import re
from typing import Any, Callable, Sequence, TypeVar

from pycaddy.dict_utils import flatten as flatten_dict
from pycaddy.convert import parse_quantity
from functools import partial
from datetime import timedelta

T = TypeVar("T")


# -------------------------
# Small, readable utilities
# -------------------------

_SINGLE_LETTER_SI = re.compile(
    r"""
    ^\s*
    (?P<val>[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)
    \s*
    (?P<u>[KMGTPEkmgtpe])         # strict single-letter SI
    \s*$
    """,
    re.VERBOSE,
)


def _normalise_mem(s: str, unit: str = 'GB') -> float:
    """
    Turn '128 M' -> '128 MB'. Leave '512 MiB', '88.1 GB' untouched.
    Non-strings should be handled upstream.
    """
    s = s.strip()
    m = _SINGLE_LETTER_SI.match(s)
    if m:
        s = f"{m.group('val')} {m.group('u').upper()}B"

    # call for parse unit
    v, _ = parse_quantity(s, unit=unit)
    return v


def timedelta_to_str(td: timedelta) -> str:
    total_seconds = int(td.total_seconds())
    h = total_seconds // 3600
    m = (total_seconds % 3600) // 60
    s = total_seconds % 60
    return f"{h:02}:{m:02}:{s:02}"


def time_str_to_timedelta(s: str) -> timedelta:
    h, m, s = map(int, s.split(":"))
    return timedelta(hours=h, minutes=m, seconds=s)


def _normalise_time(s: str) -> timedelta:
    pass


def _tokens_lower(path: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(str(p).lower() for p in path)


def _path_matches(
        path: tuple[str, ...],
        *,
        include: Sequence[str] = (),
        exclude: Sequence[str] = (),
        last: str | None = None,
) -> bool:
    """
    include: every word must appear at least once across tokens (substring match).
    exclude: none of the words may appear in any token.
    last:   if given, last token must equal this (case-insensitive).
    """
    toks = _tokens_lower(path)
    if not toks:
        return False

    if last is not None and toks[-1] != last.lower():
        return False

    if include:
        need = set(w.lower() for w in include)
        if not need <= set(toks):
            return False

    if exclude:
        bad = set(w.lower() for w in exclude)
        if not set(toks) & bad == set():
            return False

    return True


def _convert_via_parse_quantity(
        raw: Any,
        *,
        target_unit: str,
        default_unit_for_numbers: str | None = None,
        normalise: Callable[[str], str] | None = None,
) -> float | None:
    """
    Convert `raw` to the target unit using your `parse_quantity`.
    - Numbers: interpreted as `default_unit_for_numbers` (or as `target_unit` if None).
    - Strings: optionally normalised, then parsed via `parse_quantity`.
    Returns None if parsing fails or the result is negative.
    """
    if raw is None:
        return None

    try:
        if isinstance(raw, (int, float)):
            unit = default_unit_for_numbers or target_unit
            val, _ = parse_quantity(f"{raw} {unit}", target_unit)
        else:
            s = str(raw)
            if normalise:
                s = normalise(s)
            val, _ = parse_quantity(s, target_unit)

        val = float(val)
        return val if val >= 0 else None
    except Exception:
        return None


# -------------------------
# Generic metric extractor
# -------------------------

def extract_metric(
        profile: dict[str, Any] | None,
        *,
        metric_name: str,
        include: Sequence[str],
        exclude: Sequence[str] = (),
        last: str | None = None,
        aggregator: Callable[[list[float]], float] = max,
        normaliser: Callable[[str], Any] | None = None,
        formatter: Callable[[Any], str] | None = str
) -> dict[str, Any]:
    """
    Flatten the profile (with your flatten_dict), select matching paths, convert via parse_quantity,
    aggregate, and return a simple result dict.

    Returns:
      {f"{metric_name} [{target_unit}]": float, "Source key": path?}
      If no matches/parseable values, returns 0.0 (not an error).
    """

    default = {metric_name: 0.0}

    if not profile:
        return default

    # Use your flattener: expects dict[Path, Any] where Path is a tuple
    flat = flatten_dict(profile)
    values: list = []

    for path, raw in flat.items():

        if not _path_matches(path, include=include, exclude=exclude, last=last):
            continue

        val = raw
        if normaliser:
            val = normaliser(val)

        values.append(val)

    if not values:
        return default

    result = aggregator(values)
    if formatter:
        result = formatter(result)

    return {metric_name: result}


# -------------------------
# Ready-to-use wrappers
# -------------------------

def extract_memory_gb(
        profile: dict[str, Any] | None,
        *,
        include: Sequence[str] = ("memory",),
        exclude: Sequence[str] = ("hpc group",),
        last: str | None = "memory",
        aggregator: Callable[[list[float]], float] = max,
        unit: str = 'GB'
) -> dict[str, Any]:
    """
    Memory extractor using your dependencies.
    """
    return extract_metric(
        profile,
        metric_name=f"Memory [{unit}]",
        include=include,
        exclude=exclude,
        last=last,
        aggregator=aggregator,
        normaliser=partial(_normalise_mem, unit=unit)
    )


def extract_elapsed_seconds(
        profile: dict[str, Any] | None,
        *,
        include: Sequence[str] = ("elapsed time",),  # add ("duration",) if needed
        exclude: Sequence[str] = (),
        last: str | None = "elapsed time",
        aggregator: Callable[[list[float]], float] = max,
) -> dict[str, Any]:
    """
    Elapsed-time extractor, same engine, parsed to seconds.
    """
    return extract_metric(
        profile,
        metric_name="Elapsed Time",
        include=include,
        exclude=exclude,
        last=last,
        aggregator=aggregator,
        normaliser=time_str_to_timedelta,  # no special unit normalization needed for time
        formatter=timedelta_to_str,  # no special unit normalization needed for time
    )


def flat_profile(profile):
    memory_dict = extract_memory_gb(profile)
    eta_dict = extract_elapsed_seconds(profile)

    return {**memory_dict, **eta_dict}

if __name__ == '__main__':
    import json

    with open('eigenmode_1.json', 'r') as f:
        data = json.load(f)

    memory = extract_memory_gb(data['profile'])
    print(memory)

    eta = extract_elapsed_seconds(data['profile'])
    print(eta)
