from typing import Any
from pydantic import TypeAdapter
from pysubmit.workflow.sweep.utils import apply_adapter, flatten




def flat_data_from_json(data: dict, adapter: TypeAdapter = None) -> dict[str, Any]:
    if adapter:
        data = apply_adapter(data, adapter)

    if isinstance(data, dict):
        flat_data = flatten(data)
        return {'__'.join(k): v for k, v in flat_data.items()}

    return data.flatten()
