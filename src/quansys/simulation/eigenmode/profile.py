import re
from typing import Any, Callable, Iterable, Mapping, Optional, Sequence

from pykit.dict_utils import flatten as flatten_dict
from pykit.convert import parse_quantity

# Strict number + single-letter SI unit (K/M/G/T/P/E) where appending 'B' is appropriate.
_NEEDS_B = re.compile(
    r"""
    ^
    \s*
    (?P<val>[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)
    \s*
    (?P<u>[KMGTPE])
    \s*
    $
    """,
    re.VERBOSE,
)

def normalise_mem_unit(s: str) -> str:
    """
    '128 M' -> '128 MB'
    '1.02e+03 m' -> '1.02e+03 MB'
    Leaves '88.1 GB', '512 MiB' untouched.
    Trims surrounding whitespace. Case-insensitive on the single-letter unit.
    """
    if not isinstance(s, str):
        return s  # non-strings handled upstream
    s = s.strip()
    m = _NEEDS_B.match(s)
    if m:
        return f"{m.group('val')} {m.group('u').upper()}B"
    return s

def _tokens_lower(path: tuple[str | int, ...]) -> tuple[str, ...]:
    # Convert ints to str and lower-case all tokens
    return tuple(str(p).lower() for p in path)

def _matches_path(
    path_lower: tuple[str, ...],
    required_words: Sequence[str],
    avoided_words: Sequence[str],
    require_last_key_equals: Optional[str],
) -> bool:
    if require_last_key_equals is not None:
        if path_lower[-1] != require_last_key_equals.lower():
            return False

    if required_words:
        req = tuple(r.lower() for r in required_words)
        # Each required word must appear in at least one token of the path
        for r in req:
            if not any(r in tok for tok in path_lower):
                return False

    if avoided_words:
        exc = tuple(e.lower() for e in avoided_words)
        for e in exc:
            if any(e in tok for tok in path_lower):
                return False

    return True

def _to_gb(value: Any, default_unit_for_numbers: Optional[str]) -> Optional[float]:
    """
    Convert an arbitrary value to GB.
    - If value is numeric and default_unit_for_numbers is provided, apply it.
    - If value is numeric and no default unit is provided, interpret as GB.
    - If value is str, normalise units and parse as GB.
    Returns None on parse failure.
    """
    if isinstance(value, (int, float)):
        s = f"{value} {default_unit_for_numbers}" if default_unit_for_numbers else f"{value} GB"
    else:
        s = str(value)
    s = normalise_mem_unit(s)
    try:
        gb, _ = parse_quantity(s, "GB")
        gb = float(gb)
        if gb < 0:
            return None
        return gb
    except Exception:
        return None

def extract_memory_gb(
    profile: Optional[Mapping[str, Any]],
    *,
    required_words: Sequence[str] = ("memory",),        # words that must appear somewhere in the key path
    avoided_words: Sequence[str] = ("hpc group",),      # words that must not appear anywhere in the key path
    require_last_key_equals: Optional[str] = "memory",  # enforce last token == 'memory'; set to None to disable
    aggregator: Callable[[Iterable[float]], float] = max,
    default_unit_for_numbers: Optional[str] = None,     # e.g., "MB" for bare numbers; None => treat bare numbers as GB
    return_source_of_best: bool = False,
) -> dict[str, Any]:
    """
    Flatten `profile`, select memory-like keys by path, parse/convert to GB, aggregate.

    Raises:
      - TypeError / ValueError on unexpected input shapes.
      - Any errors from `flatten_dict` as-is.

    Returns:
      {'Memory [GB]': float, 'Source key': tuple[str|int, ...]?}
      If no matching keys or no parseable values, returns 0.0 (not an error).
    """
    if profile is None:
        return {"Memory [GB]": 0.0}

    flat = flatten_dict(profile)  # expected to yield keys: tuple[str|int, ...]
    if not isinstance(flat, Mapping):
        raise TypeError("flatten_dict(profile) did not return a Mapping.")

    paths_and_values: list[tuple[tuple[str | int, ...], float]] = []

    for k, raw in flat.items():
        if not isinstance(k, tuple):
            raise TypeError(f"Flattened key is not a tuple: {k!r}")

        if not all(isinstance(p, (str, int)) for p in k):
            raise TypeError(f"Flattened key contains non-(str|int) parts: {k!r}")

        path_lower = _tokens_lower(k)
        if not _matches_path(path_lower, required_words, avoided_words, require_last_key_equals):
            continue

        gb = _to_gb(raw, default_unit_for_numbers)
        if gb is not None:
            paths_and_values.append((k, gb))

    if not paths_and_values:
        # No matches or nothing parseable is not a hard error; signal with 0.0
        return {"Memory [GB]": 0.0}

    values = [v for _, v in paths_and_values]
    try:
        agg = float(aggregator(values))
    except Exception as e:
        # Aggregator should be pure; if it fails, that *is* exceptional.
        raise ValueError(f"Aggregator failed on values {values!r}") from e

    result: dict[str, Any] = {"Memory [GB]": agg}
    if return_source_of_best and aggregator is max:
        best_idx = values.index(agg)
        result["Source key"] = paths_and_values[best_idx][0]
    return result

def safe_extract_memory_gb(
    profile: Optional[Mapping[str, Any]],
    *,
    required_words: Sequence[str] = ("memory",),
    avoided_words: Sequence[str] = ("hpc group",),
    require_last_key_equals: Optional[str] = "memory",
    aggregator: Callable[[Iterable[float]], float] = max,
    default_unit_for_numbers: Optional[str] = None,
    return_source_of_best: bool = False,
    on_error_return: float = -1.0,
    printer: Callable[[str], None] = print,
) -> dict[str, Any]:
    """
    Fail-safe wrapper: never raises. Prints the error and returns a sentinel value.
    """
    try:
        return extract_memory_gb(
            profile,
            required_words=required_words,
            avoided_words=avoided_words,
            require_last_key_equals=require_last_key_equals,
            aggregator=aggregator,
            default_unit_for_numbers=default_unit_for_numbers,
            return_source_of_best=return_source_of_best,
        )
    except Exception as e:
        printer(f"[extract_memory_gb] error: {e}")
        return {"Memory [GB]": float(on_error_return)}


if __name__ == '__main__':

    import json

    with open('eigenmode_1.json', 'r') as f:
        data = json.load(f)

    print(safe_extract_memory_gb(data['profile']))
