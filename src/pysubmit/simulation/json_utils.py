import json
from dataclasses import asdict, is_dataclass, dataclass, fields
import numpy as np
from typing import Any, Dict, Type
import importlib


## Custom JSON Encoder
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj: Any) -> Any:
        if is_dataclass(obj):
            # Convert dataclass to dict and include class information
            obj_dict = asdict(obj)
            obj_dict["__class__"] = f"{obj.__class__.__module__}.{obj.__class__.__qualname__}"
            return obj_dict
        elif isinstance(obj, np.ndarray):
            # Convert ndarray to a serializable format
            return {
                "__ndarray__": True,
                "data": obj.tolist(),
                "dtype": str(obj.dtype),
                "shape": obj.shape
            }
        return super().default(obj)


# Utility function to dynamically import a class from its fully qualified name
def get_class_by_name(class_path: str) -> Type:
    """
    Dynamically imports a class from a string.

    Args:
        class_path (str): The full path to the class, e.g., 'module.submodule.ClassName'.

    Returns:
        Type: The class type.
    """
    module_path, _, class_name = class_path.rpartition(".")
    if not module_path:
        raise ValueError(f"Invalid class path: {class_path}")
    module = importlib.import_module(module_path)
    cls = getattr(module, class_name)
    return cls


# Custom Decoder Function
def custom_json_decoder(dct: Dict) -> Any:
    if "__ndarray__" in dct:
        # Reconstruct the ndarray
        data = dct["data"]
        dtype = dct["dtype"]
        shape = dct["shape"]
        return np.array(data, dtype=dtype).reshape(shape)
    elif "__class__" in dct:
        # Reconstruct the dataclass instance
        class_path = dct.pop("__class__")
        cls = get_class_by_name(class_path)
        # Assuming the class is a dataclass, recursively decode fields
        field_types = {f.name: f.type for f in fields(cls)}
        for key, value in dct.items():
            if key in field_types and is_dataclass(field_types[key]):
                dct[key] = custom_json_decoder(value)
        return cls(**dct)
    return dct


def json_read(path, cls=None):
    with open(path) as f:
        data = json.load(f, object_hook=custom_json_decoder)
    if cls:
        data = cls(**data)
    return data


def json_write(path, obj):
    # first dumps
    ser_data = json.dumps(obj, cls=CustomJSONEncoder, indent=4)
    with open(path, 'w') as f:
        f.write(ser_data)
