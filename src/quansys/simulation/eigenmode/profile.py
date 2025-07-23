from pykit.dict_utils import flatten as flatten_dict
from pykit.convert import parse_quantity

import re

# Pre‑compiled regex:  “number  optional‑space  K/M/G/T/P/E  end‑of‑string”
_NEEDS_B = re.compile(
    r"""
    ^
    \s*                # leading space
    [-+]?[\d.]+        # number (int/float/scientific)
    (?:e[+-]?\d+)?     # optional exponent
    \s*                # whitespace
    (?P<u>[KMGTPE])    # unit letter we care about
    \s*$               # nothing after it
    """,
    re.IGNORECASE | re.VERBOSE,
)

def normalise_mem_unit(s: str) -> str:
    """
    Turn `'128 M'` → `'128 MB'`, `'1.02e+03 m'` → `'1.02e+03 MB'`, leave
    already‑valid things (`'88.1 GB'`, `'512 MiB'`) untouched.
    """
    m = _NEEDS_B.match(s)
    if m:
        return _NEEDS_B.sub(r"\g<0>B", s)
    return s


def flatten_profile(profile: dict) -> dict:
    if profile is None:
        return {}

    flat_profile = flatten_dict(profile)
    # filtering all the memory parts
    memory_keys = filter(lambda x: 'memory' in x[-1].lower(), flat_profile.keys())
    # converting to list of strings
    max_memory = 0
    for k in memory_keys:
        try:
            cleaned_string = normalise_mem_unit(flat_profile[k])
            value, unit = parse_quantity(cleaned_string, 'GB')
            max_memory = max(max_memory, value)
        except Exception as e:
            raise e
    # retuning the maximum of the memory values
    return {'Memory [GB]': max_memory}



