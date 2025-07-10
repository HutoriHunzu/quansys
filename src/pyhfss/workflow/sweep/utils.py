from typing import Any, Annotated
from collections import defaultdict
from pydantic import TypeAdapter, ValidationError

def _tree():
    """Creates a recursive defaultdict."""
    return defaultdict(_tree)


def _dictify(d):
    """Recursively convert a defaultdict to a regular dict."""
    if isinstance(d, defaultdict):
        return {k: _dictify(v) for k, v in d.items()}
    return d


def apply_adapter(value: Any, adapter: TypeAdapter = None):
    if not adapter:
        return value
    try:
        value = adapter.validate_python(value)
    except ValidationError:
        pass
    return value


def flatten(d: dict, parent_key=(), adapter: TypeAdapter = None) -> dict[tuple, Any]:
    items = {}
    for k, v in d.items():
        new_key = parent_key + (k,)  # Always treat keys as tuples
        v = apply_adapter(v, adapter)
        if isinstance(v, dict):
            items.update(flatten(v, new_key, adapter=adapter))
        else:
            items[new_key] = v
    return items


def unflatten(flat_dict):
    """
    Convert a flat dictionary with tuple keys into a nested dictionary
    using defaultdict for automatic sub-dictionary creation.

    Example:
        flat_dict = {(1, 2, 3): 4, (1, 2, 5): 6, (7,): 8}
        returns {1: {2: {3: 4, 5: 6}}, 7: 8}
    """
    nested = _tree()  # This is our recursive defaultdict.

    for key, value in flat_dict.items():
        # Normalize the key: if it's not a tuple, wrap it in one.
        if not isinstance(key, tuple):
            key = (key,)

        current = nested
        # Traverse the tree for all key parts except the last one.
        for part in key[:-1]:
            current = current[part]
        # Set the value at the final key part.
        current[key[-1]] = value

    # Optionally, convert the defaultdict tree into a standard dict.
    return _dictify(nested)


def merge_by_update(*args: dict) -> dict:
    result = {}
    for flat_dict in args:
        result.update(flat_dict)
    return result


def merge_dicts(*args: dict) -> dict:
    return unflatten(merge_by_update(*map(flatten, args)))




def split_dict_by_adapter(d: dict, adapter: TypeAdapter) -> tuple[dict, dict]:

    matching: dict = {}
    non_matching: dict = {}
    for key, value in d.items():
        try:
            adapter.validate_python(value)
        except ValidationError:
            non_matching[key] = value
        else:
            matching[key] = value

    return matching, non_matching


    # correct_type_dict = dict(filter(lambda x: isinstance(x[1], t), d.items()))
    # other_type_dict = dict(filter(lambda x: not isinstance(x[1], t), d.items()))

    # return correct_type_dict, other_type_dict




