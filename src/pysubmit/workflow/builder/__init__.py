from typing import Annotated, TypeAlias

from .design_variable_builder import DesignVariableBuilder
from .function_builder import FunctionBuilder
from .module_builder import ModuleBuilder

from pydantic import Field

SUPPORTED_BUILDERS: TypeAlias = Annotated[DesignVariableBuilder | FunctionBuilder | ModuleBuilder,
Field(discriminator="type")]
