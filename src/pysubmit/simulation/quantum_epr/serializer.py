from numpy.typing import NDArray
import numpy as np
from dataclasses import is_dataclass, fields, dataclass
from typing import Any


def serialize_ndarray(array: NDArray) -> Any:
    """
    Serialize an ndarray to a JSON-serializable structure.
    If the array contains complex numbers, it converts each element to a dict with real and imaginary parts.
    Otherwise, it converts the array to a nested list.
    """
    is_not_complex = np.isclose(np.sum(np.imag(array)), 0)
    if is_not_complex:
        return array.tolist()
    # Recursively serialize complex arrays of arbitrary dimensions
    def serialize_element(element):
        if isinstance(element, complex):
            return {"real": element.real, "imag": element.imag}
        return element
    return np.vectorize(serialize_element, otypes=[object])(array).tolist()


def deserialize_ndarray(data: Any) -> NDArray:
    """
    Deserialize a JSON-serializable structure back into an ndarray.
    If the data contains dictionaries with "real" and "imag", it reconstructs complex numbers.
    Otherwise, it converts the data to a standard ndarray.
    """

    def deserialize_element(element):
        # If the element is a dictionary with 'real' and 'imag', reconstruct as a complex number
        if isinstance(element, dict) and "real" in element and "imag" in element:
            return complex(element["real"], element["imag"])
        return element

    # Recursively deserialize elements, preserving structure
    def recursive_deserialize(data):
        if isinstance(data, list):
            return [recursive_deserialize(item) for item in data]
        return deserialize_element(data)

    # Apply recursive deserialization
    deserialized = recursive_deserialize(data)

    # Convert to ndarray with appropriate dtype
    return np.array(deserialized)

def dataclass_to_dict(obj: Any) -> Any:
    """
    Recursively convert a dataclass (or nested dataclass) to a JSON-serializable dictionary.
    """
    if is_dataclass(obj):
        result = {}
        for field in fields(obj):
            value = getattr(obj, field.name)
            if isinstance(value, np.ndarray):
                result[field.name] = serialize_ndarray(value)
            elif is_dataclass(value):
                result[field.name] = dataclass_to_dict(value)
            elif isinstance(value, list):
                result[field.name] = [dataclass_to_dict(v) if is_dataclass(v) else v for v in value]
            elif isinstance(value, dict):
                result[field.name] = {
                    k: dataclass_to_dict(v) if is_dataclass(v) else v for k, v in value.items()
                }
            else:
                result[field.name] = value
        return result
    elif isinstance(obj, list):
        return [dataclass_to_dict(v) if is_dataclass(v) else v for v in obj]
    elif isinstance(obj, dict):
        return {k: dataclass_to_dict(v) if is_dataclass(v) else v for k, v in obj.items()}
    return obj

def dict_to_dataclass(cls: Any, data: dict) -> Any:
    """
    Recursively convert a dictionary into a dataclass (or nested dataclass).
    """
    if not is_dataclass(cls):
        raise ValueError("Provided class is not a dataclass")

    kwargs = {}
    for field in fields(cls):
        value = data.get(field.name)
        if value is not None:
            if isinstance(field.type, type) and issubclass(field.type, np.ndarray):
                kwargs[field.name] = deserialize_ndarray(value)
            elif is_dataclass(field.type):
                kwargs[field.name] = dict_to_dataclass(field.type, value)
            elif isinstance(value, list) and is_dataclass(field.type.__args__[0]):
                kwargs[field.name] = [dict_to_dataclass(field.type.__args__[0], v) for v in value]
            else:
                kwargs[field.name] = value
    return cls(**kwargs)



@dataclass
class EprDiagResult:
    chi: NDArray
    frequencies: NDArray

    def to_dict(self):
        return dataclass_to_dict(self)

    @classmethod
    def from_dict(cls, data):
        return dict_to_dataclass(cls, data)


if __name__ == '__main__':
    r = EprDiagResult(
        chi=np.array([1,2,3]),
        frequencies=np.array([[[1,2,3+1j], [2,3,4]], [[2,3,4], [5,3,3]]])
    )
    print(r)
    q = deserialize_ndarray(r.to_dict()['frequencies'])
    print(q)