from ansys.aedt.core.hfss import Hfss
from ansys.aedt.core.application.analysis import Setup


def _validate_design(hfss: Hfss, design_name: str):
    lst_of_designs = hfss.design_list
    if not design_name in lst_of_designs:
        raise ValueError(f'{design_name} does not appear in design list: {lst_of_designs}')


def _set_design(hfss: Hfss, design_name: str):
    hfss.set_active_design(design_name)


def validate_and_set_deisgn(hfss: Hfss, design_name: str):
    _validate_design(hfss, design_name)
    _set_design(hfss, design_name)


def _validate_setup(hfss: Hfss, setup_name: str):
    lst_of_setups = hfss.setup_names
    if not setup_name in lst_of_setups:
        raise ValueError(f'{setup_name} does not appear in setup list: {lst_of_setups}')


def _get_setup(hfss: Hfss, setup_name: str):
    return hfss.get_setup(setup_name)


def set_design_and_get_setup(hfss: Hfss, design_name: str, setup_name: str) -> Setup:
    # design validation and activation
    validate_and_set_deisgn(hfss, design_name)

    # setup validation and returning the setup object
    _validate_setup(hfss, setup_name)
    return _get_setup(hfss, setup_name)


def update_setup_parameters(setup: Setup, parameters: dict):
    for k, v in parameters.items():
        setup.props[k] = v
    setup.update()


