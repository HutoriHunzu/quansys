from typing import Annotated

from .design_variable_builder import DesignVariableBuilder
from .function_builder import FunctionBuilder
from .module_builder import ModuleBuilder

from pydantic import Field

SUPPORTED_BUILDERS = Annotated[DesignVariableBuilder | FunctionBuilder | ModuleBuilder
, Field(discriminator='type')]



