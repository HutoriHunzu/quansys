import qutip as qt

class Space:
    """
    Implemented the size of the Space and its Name.
    All other functionality comes from qt
    """

    def __init__(self, size, name):
        self.size = size
        self.name = name

    def create(self) -> qt.Qobj:
        return qt.create(self.size)

    def destroy(self) -> qt.Qobj:
        return qt.destroy(self.size)

    def basis(self, n):
        return qt.basis(self.size, n)

    def coherent(self, alpha):
        return qt.coherent(self.size, alpha)

    def eye(self):
        return qt.qeye(self.size)

    def basis_proj(self, n) -> qt.Qobj:
        return qt.basis(self.size, n) @ qt.basis(self.size, n).dag()

    def num_op(self) -> qt.Qobj:
        return self.create() @ self.destroy()

    def field_op(self) -> qt.Qobj:
        return self.create() + self.destroy()