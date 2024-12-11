from pydantic import BaseModel


class Variable(BaseModel):
    pass

class ValuedVariable(BaseModel):
    name: str
    value: float | int
    unit: str = ''


    def to_string(self):
        return f'{self.value}{self.unit}'
