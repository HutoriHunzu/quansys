from typing import Annotated, TypeAlias
from pydantic import Field

from .design_variable_builder import DesignVariableBuilder
from .function_builder import FunctionBuilder
from .module_builder import ModuleBuilder

SUPPORTED_BUILDERS: TypeAlias = Annotated[
    DesignVariableBuilder | FunctionBuilder | ModuleBuilder, Field(discriminator="type")
]

__all__ = [
    "DesignVariableBuilder",
    "FunctionBuilder",
    "ModuleBuilder",
    "SUPPORTED_BUILDERS",
]
