# from pydantic import BaseModel, BeforeValidator
# from .design_builders import SUPPORTED_BUILDERS, BuildInterface
# from .sweep import SUPPORTED_SWEEPS
# from .design_variables_handler import set_variables
# from copy import deepcopy
#
# from typing_extensions import Annotated, Iterable
#
# from itertools import chain, product
#
# from ..variables import ValuedVariable
#
#
# def ensure_list(value):
#     if value is None:
#         return None
#     if not isinstance(value, list):
#         return [value]
#     return value
#
#
# # sweep does not need any input but it should get one to pass forward information?
# # builder need to be able to get parameters as iterable of valued_variables
# # variable setting need parameters as iterable of valued variables
# # constraint on chain has to be only one builder interface, that is it cannot be changed?
#
# def chain_sweeps(lst_of_sweep: list[SUPPORTED_SWEEPS]):
#     iter_lst = [sweep.gen() for sweep in lst_of_sweep]
#     for elem in product(*iter_lst):
#         yield chain(*elem)
#
#
# class Pipeline(BaseModel):
#     builder: SUPPORTED_BUILDERS | None = None
#     builder_sweep: Annotated[list[SUPPORTED_SWEEPS] | None, BeforeValidator(ensure_list)] = None
#     variable_sweep: Annotated[list[SUPPORTED_SWEEPS] | None, BeforeValidator(ensure_list)] = None
#
#     def gen(self, hfss, data_handler=None):
#         # building pre sweep
#         for build_interface in self.run_builder(hfss, data_handler):
#             for additional_tag in self.run_variable_setter(hfss):
#                 build_interface.update_tag(additional_tag)
#                 yield build_interface
#
#     def run_variable_setter(self, hfss) -> dict:
#         if self.variable_sweep is None:
#             yield [{}]
#
#         for parameters in chain_sweeps(self.variable_sweep):
#             set_variables(hfss, parameters)
#             yield ValuedVariable.iterable_to_dict(parameters)
#
#     def run_builder(self, hfss, data_handler):
#         if self.builder_sweep is None:
#             yield from self.builder.build(hfss,
#                                           data_handler=data_handler)
#
#         for parameters in chain_sweeps(self.builder_sweep):
#             yield from self.builder.build(hfss,
#                                           data_handler=data_handler,
#                                           parameters=parameters)
