import qutip as qt
from .space import Space


class CompositeSpace:
    """
    A structure for which we incorporate all the spaces in our system
    Keep the order for tensor products
    """

    def __init__(self, *args: Space):
        self.spaces_ordered = args
        self.spaces: dict[str | int, Space] = {space.name: space for space in self.spaces_ordered}

    def tensor(self, name_op_dict: dict[str | int, qt.Qobj]) -> qt.Qobj:
        """Tensor product of operators. Uses identity for unspecified spaces."""
        op_lst = []
        for space in self.spaces_ordered:
            if space.name in name_op_dict:
                op_lst.append(name_op_dict[space.name])
            else:
                op_lst.append(space.eye())
        return qt.tensor(*op_lst)

    def get_operator(self, name: str | int, op_type: str, **kwargs) -> qt.Qobj:
        """Create and expand operator from specific space."""
        op = getattr(self.spaces[name], op_type)(**kwargs)
        return self.tensor({name: op})

    def expand_operator(self, name: str | int, operator: qt.Qobj) -> qt.Qobj:
        """Expand operator from specific space with identities for other spaces."""
        return self.tensor({name: operator})