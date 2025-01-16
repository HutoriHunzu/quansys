import json
from dataclasses import asdict, is_dataclass, dataclass, fields
import numpy as np
from typing import Any, Dict, Type
import importlib
from pathlib import Path
from pydantic import BaseModel


# Custom JSON Encoder
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj: Any) -> Any:
        if is_dataclass(obj):
            # Convert dataclass to dict and include class information
            obj_dict = asdict(obj)
            obj_dict["__class__"] = f"{obj.__class__.__module__}.{obj.__class__.__qualname__}"
            return obj_dict
        elif isinstance(obj, BaseModel):
            # Convert Pydantic BaseModel to dict and include class information
            obj_dict = obj.model_dump()
            obj_dict["__class__"] = f"{obj.__class__.__module__}.{obj.__class__.__qualname__}"
            return obj_dict
        elif isinstance(obj, np.ndarray):
            # Check if the ndarray contains complex numbers
            if np.any(np.iscomplex(obj)):
                # For complex arrays, store only non-zero imaginary parts
                return {
                    "__ndarray__": True,
                    "data": [
                        {"real": float(val.real), "imag": float(val.imag) if val.imag != 0 else None}
                        for val in obj.flatten()
                    ],
                    "dtype": str(obj.dtype),
                    "shape": obj.shape
                }
            else:
                # For non-complex arrays, store as usual
                return {
                    "__ndarray__": True,
                    "data": obj.real.tolist(),
                    "dtype": str(obj.dtype),
                    "shape": obj.shape
                }

        return super().default(obj)


# Utility function to dynamically import a class from its fully qualified name
def get_class_by_name(class_path: str) -> type:
    """
    Dynamically imports a class from a string.

    Args:
        class_path (str): The full path to the class, e.g., 'module.submodule.ClassName'.

    Returns:
        type: The class type.
    """
    module_path, _, class_name = class_path.rpartition(".")
    if not module_path:
        raise ValueError(f"Invalid class path: {class_path}")
    module = importlib.import_module(module_path)
    cls = getattr(module, class_name)
    return cls


# Custom Decoder Function
def custom_json_decoder(dct: dict) -> Any:
    if "__ndarray__" in dct:
        # Reconstruct the ndarray
        data = dct["data"]
        dtype = dct["dtype"]
        shape = dct["shape"]

        # Handle complex numbers if applicable
        if np.complex in np.dtype(dtype).subdtype:
            data = np.array([val["real"] + (val["imag"] if val["imag"] is not None else 0) * 1j for val in data])
        else:
            data = np.array(data, dtype=dtype)

        return data.reshape(shape)
    elif "__class__" in dct:
        # Reconstruct the Pydantic/BaseModel or dataclass instance
        class_path = dct.pop("__class__")
        cls = get_class_by_name(class_path)

        # Pydantic models are initialized with the dictionary as keyword arguments
        if issubclass(cls, BaseModel):
            return cls.model_validate(dct)

        # Handle dataclasses (if needed, this could be expanded further)
        if is_dataclass(cls):
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


def json_write(path, obj, use_unique: bool = True):
    # first dumps
    data = json.dumps(obj, cls=CustomJSONEncoder, indent=4)

    write(path, data, use_unique)


def unique_name_by_counter(path: Path):
    base_name = path.stem
    counter = 0
    while path.exists():
        path = path.with_stem(f'{base_name}_{counter}')
        counter += 1

    return path


def write(path, data: str, use_unique: bool = True):
    if use_unique:
        path = unique_name_by_counter(Path(path))

    with open(path, 'w') as f:
        f.write(data)


def read(path):
    with open(path, 'r') as f:
        return f.read()
