# utils.py
from typing import Any
from pydantic import TypeAdapter
from pyhfss.workflow.sweep.utils import apply_adapter, flatten
from pathlib import Path


def flat_data_from_json(data: dict, adapter: TypeAdapter = None) -> dict[str, Any]:
    """
    Transforms nested JSON data into a flat dictionary.

    Optionally applies the provided adapter (via `apply_adapter`) to convert the JSON data
    into a simulation output object. The object is then flattened using the `flatten` function.
    Final keys are joined by a double underscore ('__').

    Args:
        data (dict): The JSON data representing a simulation output.
        adapter (TypeAdapter, optional): An optional adapter for converting the JSON data.

    Returns:
        dict[str, Any]: The flattened dictionary.
    """
    # If an adapter is provided, transform the data first.
    if adapter:
        data = apply_adapter(data, adapter)

    # If the resulting data is a dictionary, flatten it.
    if isinstance(data, dict):
        flat_data = flatten(data)
        return {'__'.join(k): v for k, v in flat_data.items()}

    # Otherwise, assume the object has its own flatten() method.
    return data.flatten()



def unique_name_by_counter(path: Path):
    base_name = path.stem
    counter = 0
    while path.exists():
        path = path.with_stem(f'{base_name}_{counter}')
        counter += 1

    return path
