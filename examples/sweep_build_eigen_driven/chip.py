from ansys.aedt.core.hfss import Hfss

# from pysubmit.shared.variables import ValuedVariable

from drawing.meader.euler import meander_euler
from drawing.export_to_pyaedt.parser import parse_component, ExportConfig

from pydantic import BaseModel, Field, BeforeValidator
from typing_extensions import Annotated

from enum import StrEnum, auto
from typing import Literal


class Value(BaseModel):
    value: float
    unit: str = 'mm'

    def to_str(self):
        return f'{self.value}{self.unit}'


# class ChipVars(StrEnum):
#     pass

class VarsNames(StrEnum):
    spacer_length = auto()
    chip_house_length = auto()
    chip_house_radius = auto()

    chip_base_length = auto()
    chip_base_thickness = auto()
    chip_base_width = auto()

    pin_waveguide_radius = auto()
    pin_waveguide_length = auto()
    pin_conductor_radius = auto()

    pin_a_location = auto()
    pin_b_location = auto()
    pin_c_location = auto()
    pin_c_length = auto()
    pin_d_location = auto()

    purcell_readout_gap = auto()

# FORCED_INT = Annotated

class MeanderArgs(BaseModel):
    wire_width: int = 100
    height: int = 1500
    padding_length: int = 500
    spacing: int = 200
    radius: int = 50
    num_turns: int = 9


def unite_vacuum_and_set_mesh(hfss, mesh_size: str):
    vacuum_objects = list(filter(lambda x: x.material_name == 'vacuum', hfss.modeler.object_list))

    vacuum_united_obj = hfss.modeler.unite(vacuum_objects)
    hfss.mesh.assign_length_mesh(vacuum_united_obj, maximum_length=mesh_size, name='vacuum_mesh')

    return vacuum_united_obj


class ChipHouseCylinderParameters(BaseModel):
    ## type: Literal['chip_house_cylinder'] = 'chip_house_cylinder'

    spacer_length: Value = Value(value=1)
    chip_house_length: Value = Value(value=26)
    chip_house_radius: Value = Value(value=2)

    chip_base_length: Value = Value(value=22)
    chip_base_thickness: Value = Value(value=381, unit='um')
    chip_base_width: Value = Value(value=2)
    chip_base_material: str = 'silicon'

    pin_waveguide_radius: Value = Value(value=0.575)
    pin_waveguide_length: Value = Value(value=6)
    pin_conductor_radius: Value = Value(value=0.25)

    pin_a_location: Value = Value(value=8)
    pin_b_location: Value = Value(value=11)
    pin_c_location: Value = Value(value=15)
    pin_c_length: Value = Value(value=6.75)
    pin_d_location: Value = Value(value=18)

    purcell_readout_gap: Value = Value(value=2)

    # meander_type: str = 'euler'
    # meander_args: MeanderArgs = MeanderArgs()


def load_relevant_parameters(parameters: dict, cls: type(BaseModel), with_prefix: str = None):
    if with_prefix:
        parameters = {k[len(with_prefix):]: v
                      for k, v in filter(lambda x: x[0].startswith(with_prefix), parameters.items())}

    relevant_parameters_names = set(cls.model_fields.keys()) & set(parameters.keys())
    relevant_parameters = {k: parameters[k] for k in relevant_parameters_names}
    return cls(**relevant_parameters)


def build(hfss: Hfss,
          design_name: str = 'eigenmode_design',
          setup_name: str = 'Setup1',
          # driven_modal_design_name: str = 'driven_modal',
          # driven_modal_setup_name: str = 'Setup1',
          **kwargs):
    parameters = load_relevant_parameters(kwargs, ChipHouseCylinderParameters)
    readout_meander_args = load_relevant_parameters(kwargs, MeanderArgs, with_prefix='readout_')
    purcell_meander_args = load_relevant_parameters(kwargs, MeanderArgs, with_prefix='purcell_')

    hfss.set_active_design('temp')

    # # clearing all designs
    # for design_name in (eigenmode_design_name, driven_modal_design_name):

    if design_name in hfss.design_list:
        hfss.delete_design(design_name)

    hfss.save_project()

    # creating design
    hfss.insert_design(design_name, 'Eigenmode')
    hfss.set_active_design(design_name)

    # parameters = parameters or {}

    modeler = hfss.modeler

    variables_names = list(
        map(lambda x: x[0],
            filter(lambda x: x[1].annotation == Value, ChipHouseCylinderParameters.model_fields.items())
            )
    )

    for name in variables_names:
        v = getattr(parameters, name)
        hfss[name] = v.to_str()

    # CHIP HOUSE
    chip_house_back_cylinder_a = modeler.create_cylinder(orientation='Z',
                                                         origin=[0, 2.5, f'-{VarsNames.chip_house_length}'],
                                                         radius=3.5,
                                                         height=f'-{VarsNames.spacer_length}',
                                                         name='chip_house_back_cylinder_a', material='vacuum')

    chip_house_back_cylinder_b = modeler.create_cylinder(orientation='Z',
                                                         origin=[0, -2.5, f'-{VarsNames.chip_house_length}'],
                                                         radius=3.5,
                                                         height=f'-{VarsNames.spacer_length}',
                                                         name='chip_house_back_cylinder_b', material='vacuum')

    chip_house_back_rect = modeler.create_box(origin=[-3.5, -2.5, f'-{VarsNames.chip_house_length}'],
                                              sizes=[7, 5, f'-{VarsNames.spacer_length}'],
                                              name='chip_house_back_rect', material='vacuum')

    chip_house_cylinder = modeler.create_cylinder(orientation='Z',
                                                  origin=[0, 0, f'-{VarsNames.chip_house_length}'],
                                                  radius=VarsNames.chip_house_radius,
                                                  height=VarsNames.chip_house_length,
                                                  name='chip_house_waveguide', material='vacuum')

    # # Creating pin wgs

    pin_wg_1 = modeler.create_cylinder(orientation='Y',
                                       origin=[0, 0, f'-{VarsNames.pin_a_location}'],
                                       radius=VarsNames.pin_waveguide_radius,
                                       height=f'{VarsNames.chip_house_radius} + {VarsNames.pin_waveguide_length}',
                                       name=f'chip_pin_a_waveguide', material='vacuum')

    pin_wg_2 = modeler.create_cylinder(orientation='Y',
                                       origin=[0, 0, f'-{VarsNames.pin_b_location}'],
                                       radius=VarsNames.pin_waveguide_radius,
                                       height=f'-{VarsNames.chip_house_radius} - {VarsNames.pin_waveguide_length}',
                                       name=f'chip_pin_b_waveguide', material='vacuum')

    pin_wg_3 = modeler.create_cylinder(orientation='Y',
                                       origin=[0, 0, f'-{VarsNames.pin_c_location}'],
                                       radius=VarsNames.pin_waveguide_radius,
                                       height=f'{VarsNames.chip_house_radius} + {VarsNames.pin_waveguide_length}',
                                       name=f'chip_pin_c_waveguide', material='vacuum')

    pin_wg_4 = modeler.create_cylinder(orientation='Y',
                                       origin=[0, 0, f'-{VarsNames.pin_d_location}'],
                                       radius=VarsNames.pin_waveguide_radius,
                                       height=f'-{VarsNames.chip_house_radius} - {VarsNames.pin_waveguide_length}',
                                       name=f'chip_pin_d_waveguide', material='vacuum')

    # adding pins
    # Creating pins
    # pin_1 = modeler.create_cylinder(cs_axis='Y',
    #                                 position=[0, f'transmon_wg_radius + sapphire_house_pins_waveguide_length',
    #                                           f'-{self.parameters.pin_1_location}'],
    #                                 radius='sapphire_house_pins_diameter/2',
    #                                 height=f'-pin_1_length',
    #                                 name=f'transmon_pin', matname='perfect conductor')
    # #
    #
    pin_3 = modeler.create_cylinder(orientation='Y',
                                    origin=[0,
                                            f'{VarsNames.chip_house_radius} + {VarsNames.pin_waveguide_length}',
                                            f'-{VarsNames.pin_c_location}'],
                                    radius=VarsNames.pin_conductor_radius,
                                    height=f'-{VarsNames.pin_c_length}',
                                    name=f'pin_3', material='perfect conductor')

    # BUILD CHIP
    chip_base = modeler.create_box(origin=[f'-{VarsNames.chip_base_width} / 2',
                                           f'-{VarsNames.chip_base_thickness} / 2',
                                           f'-{VarsNames.chip_house_length} - {VarsNames.spacer_length}'],
                                   sizes=[VarsNames.chip_base_width,
                                          VarsNames.chip_base_thickness,
                                          VarsNames.chip_base_length],
                                   name='chip_base', material=parameters.chip_base_material)

    # adding meander
    meander = meander_euler(**dict(readout_meander_args))
    export_config = ExportConfig(
        name='readout',
        unit="um",
        # align_by='port',
        tolerance=0.6,
        port='e1'
    )

    points, independent_variables, dependent_variables = parse_component(meander, export_config)
    for variables in [independent_variables, dependent_variables]:
        for k, v in variables.items():
            hfss[k] = v

    readout = modeler.create_polyline(points,
                                      cover_surface=True,
                                      close_surface=True,
                                      name='readout')

    hfss.assign_perfecte_to_sheets(readout.name)

    hfss['readout_e1_x'] = '0'
    hfss['readout_e1_y'] = f'{VarsNames.chip_base_thickness} / 2'
    hfss['readout_e1_z'] = f'-{VarsNames.chip_base_length} / 2'

    # add a bbox as non-model for meshing
    readout_mesh_box = modeler.create_box(origin=['-readout_e1_x - readout_size_x / 2',
                                                  'readout_e1_y - readout_size_y / 2 - 0.5mm',
                                                  'readout_e1_z'],
                                          sizes=['readout_size_x', 'readout_size_y + 1mm', 'readout_size_z'],
                                          name='readout_mesh_box',
                                          model=False
                                          )

    hfss.mesh.assign_length_mesh(readout_mesh_box, maximum_length='100um', name='readout_mesh_box')

    # purcell
    meander = meander_euler(**dict(purcell_meander_args))
    export_config = ExportConfig(
        name='purcell',
        unit="um",
        # align_by='port',
        tolerance=0.6,
        port='e1'
    )

    points, independent_variables, dependent_variables = parse_component(meander, export_config)
    for variables in [independent_variables, dependent_variables]:
        for k, v in variables.items():
            hfss[k] = v

    purcell = modeler.create_polyline(points,
                                      cover_surface=True,
                                      close_surface=True,
                                      name='purcell')

    hfss.assign_perfecte_to_sheets(purcell.name)



    hfss['purcell_e1_x'] = 'readout_e1_x'
    hfss['purcell_e1_y'] = f'readout_e1_y'
    hfss['purcell_e1_z'] = f'readout_e1_z - purcell_size_z - {VarsNames.purcell_readout_gap}'

    # add a bbox as non-model for meshing
    purcell_mesh_box = modeler.create_box(origin=['-purcell_e1_x - purcell_size_x / 2',
                                                  'purcell_e1_y - purcell_size_y / 2 - 0.5mm',
                                                  'purcell_e1_z'],
                                          sizes=['purcell_size_x', 'purcell_size_y + 1mm', 'purcell_size_z'],
                                          name='purcell_mesh_box',
                                          model=False
                                          )

    hfss.mesh.assign_length_mesh(purcell_mesh_box, maximum_length='100um', name='purcell_mesh_box')


    # adding boundary
    top_face_z = pin_wg_3.bottom_face_z
    boundary_object = modeler.create_object_from_face(top_face_z)
    boundary_arrow_start = top_face_z.center
    boundary_arrow_end = top_face_z.center
    boundary_arrow_end[2] += parameters.pin_waveguide_radius.value
    hfss.assign_lumped_rlc_to_sheet(boundary_object.name,
                                    name='pin_c_bound',
                                    start_direction=[boundary_arrow_start, boundary_arrow_end],
                                    rlc_type='Parallel',
                                    resistance=50, inductance=None, capacitance=None)

    # combining all vacuum objects
    vacuum_objects = [
        chip_house_back_cylinder_a,
        chip_house_back_cylinder_b,
        chip_house_back_rect,
        chip_house_cylinder,
        pin_wg_1,
        pin_wg_2,
        pin_wg_3,
        pin_wg_4
    ]

    modeler.unite(vacuum_objects)

    basic_eigenmode_properties = {
        'SetupType': 'HfssEigen',
        'MinimumFrequency': '2GHz',
        'NumModes': 1,
        'MaxDeltaFreq': 0.2,
        'ConvergeOnRealFreq': True,
        'MaximumPasses': 3,
        'MinimumPasses': 1,
        'MinimumConvergedPasses': 1,
        'PercentRefinement': 30,
        'IsEnabled': True,
        'MeshLink': {'ImportMesh': False},
        'BasisOrder': -1,
        'DoLambdaRefine': True,
        'DoMaterialLambda': True,
        'SetLambdaTarget': False,
        'Target': 0.4,
        'UseMaxTetIncrease': False
    }

    hfss.create_setup(setup_name)
    setup = hfss.get_setup(setup_name)
    hfss.save_project()
    setup.update(basic_eigenmode_properties)
    hfss.save_project()

    ######################################


def add_driven_modal(modeler, eigenmode_design_name,
                     driven_modal_design_name, driven_modal_setup_name,
                     parameters):
    # adding a copy design for driven model
    hfss.set_active_design(eigenmode_design_name)
    hfss.duplicate_design(driven_modal_design_name)

    hfss.set_active_design(driven_modal_design_name)
    hfss.solution_type = 'Modal'

    # adding setup
    hfss.create_setup(driven_modal_setup_name, setup_type='HFSSDrivenAuto')
    setup = hfss.get_setup(driven_modal_setup_name)

    # adding excitation
    pin_wg_3 = modeler['chip_pin_c_waveguide']
    top_face_z = pin_wg_3.bottom_face_z
    boundary_object = modeler.create_object_from_face(top_face_z)
    boundary_arrow_start = top_face_z.center
    boundary_arrow_end = top_face_z.center
    boundary_arrow_end[2] += parameters.pin_waveguide_radius.value
    hfss.wave_port(boundary_object,
                   integration_line=[boundary_arrow_start, boundary_arrow_end])

    # adding mesh
    unite_vacuum_and_set_mesh(hfss, mesh_size='2mm')

    driven_modal_properties = {
        'Enabled': True,
        'Auto Solver Setting': 'Balanced',
        'Auto Solver Setting/Choices': ['Higher Speed',
                                        'Balanced',
                                        'Higher Accuracy'],
        'Type': 'Discrete',
        'Start': '7GHz',
        'Stop': '9GHz',
        'Step Size': '20MHz'}

    setup.update(driven_modal_properties)
    hfss.save_project()
    print(1)

    top_face_z = pin_wg_3.bottom_face_z
    boundary_object = modeler.create_object_from_face(top_face_z)
    boundary_arrow_start = top_face_z.center
    boundary_arrow_end = top_face_z.center
    boundary_arrow_end[2] += parameters.pin_waveguide_radius.value
    hfss.wave_port(boundary_object.name,
                   name='excitation_waveport',
                   integration_line=[boundary_arrow_start, boundary_arrow_end],
                   rlc_type='Parallel',
                   resistance=50, inductance=None, capacitance=None)

    print(1)

    # copying from eigenmode all components
    # obj_lst_names =  list(map(lambda x: x.name, modeler.object_list))
    # copied_obj_lst_names = hfss.modeler.copy(obj_lst_names)  # Copy the object by its name
    # modeler.paste()

    # adding to the driven_model excitation
    # uniting vacuum and creating setup

    # going back to eigenmode design:
    # adding boundaries
    # uniting vacuum and creating setup

    # going back to eigenmode designa

    # adding boundaries and uniting vacuum

    top_face_z = pin_wg_3.bottom_face_z
    boundary_object = modeler.create_object_from_face(top_face_z)
    boundary_arrow_start = top_face_z.center
    boundary_arrow_end = top_face_z.center
    boundary_arrow_end[2] += parameters.pin_waveguide_radius.value
    hfss.assign_lumped_rlc_to_sheet(boundary_object.name,
                                    name='pin_c_bound',
                                    start_direction=[boundary_arrow_start, boundary_arrow_end],
                                    rlc_type='Parallel',
                                    resistance=50, inductance=None, capacitance=None)

    # combining all vacuum objects
    vacuum_objects = [
        chip_house_back_cylinder_a,
        chip_house_back_cylinder_b,
        chip_house_back_rect,
        chip_house_cylinder,
        pin_wg_1,
        pin_wg_2,
        pin_wg_3,
        pin_wg_4
    ]

    modeler.unite(vacuum_objects)

    basic_eigenmode_properties = {
        'SetupType': 'HfssEigen',
        'MinimumFrequency': '2GHz',
        'NumModes': 1,
        'MaxDeltaFreq': 0.2,
        'ConvergeOnRealFreq': True,
        'MaximumPasses': 3,
        'MinimumPasses': 1,
        'MinimumConvergedPasses': 1,
        'PercentRefinement': 30,
        'IsEnabled': True,
        'MeshLink': {'ImportMesh': False},
        'BasisOrder': -1,
        'DoLambdaRefine': True,
        'DoMaterialLambda': True,
        'SetLambdaTarget': False,
        'Target': 0.4,
        'UseMaxTetIncrease': False
    }

    hfss.create_setup(setup_name)
    setup = hfss.get_setup(setup_name)
    hfss.save_project()
    setup.update(basic_eigenmode_properties)
    hfss.save_project()

    # setup.props(**basic_eigenmode_properties)

    driven_setup = {'Name': 'Setup1',
                    'Enabled': True,
                    'Auto Solver Setting': 'Balanced',
                    'Auto Solver Setting/Choices': ['Higher Speed',
                                                    'Balanced',
                                                    'Higher Accuracy'],
                    'Type': 'Interpolating',
                    'Start': '6GHz',
                    'Stop': '10GHz',
                    'Count': 501}

    print(1)

    #
    # # Creating pins
    # pin_1 = modeler.create_cylinder(cs_axis='Y',
    #                                 position=[0, f'transmon_wg_radius + sapphire_house_pins_waveguide_length',
    #                                           f'-{self.parameters.pin_1_location}'],
    #                                 radius='sapphire_house_pins_diameter/2',
    #                                 height=f'-pin_1_length',
    #                                 name=f'transmon_pin', matname='perfect conductor')
    # #
    # # pin_2 = modeler.create_cylinder(cs_axis='Y',
    # #                                 position=[0, f'-transmon_wg_radius - sapphire_house_pins_waveguide_length',
    # #                                           f'-{self.parameters.pin_2_location}'],
    # #                                 radius='sapphire_house_pins_diameter/2',
    # #                                 height=f'pin_2_length',
    # #                                 name=f'readout_pin', matname='perfect conductor')
    #
    # pin_3 = modeler.create_cylinder(cs_axis='Y',
    #                                 position=[0, f'transmon_wg_radius + sapphire_house_pins_waveguide_length',
    #                                           f'-{self.parameters.pin_3_location}'],
    #                                 radius='sapphire_house_pins_diameter/2',
    #                                 height=f'-pin_3_length',
    #                                 name=f'pin_3', matname='perfect conductor')
    #
    # # pin_4 = modeler.create_cylinder(cs_axis='Y',
    # #                                 position=[0, f'-transmon_wg_radius - sapphire_house_pins_waveguide_length',
    # #                                           f'-{self.parameters.pin_4_location}'],
    # #                                 radius='sapphire_house_pins_diameter/2',
    # #                                 height=f'pin_4_length',
    # #                                 name=f'pin_4', matname='perfect conductor')
    # return top_face_z


if __name__ == '__main__':
    example_config = ChipHouseCylinderParameters(

        # sapphire_house_pins_diameter: float = 0.5
        # sapphire_house_pins_waveguide_diameter: float = 1.15
        # sapphire_house_pins_waveguide_length: float = 6
        # pin_1_length: float = 6
        # pin_2_length: float = 0
        # pin_3_length: float = 6.75
        # pin_4_length: float = 0
        #
        # # Simulation Boundaris
        # maximum_mesh_size_mm: float = 2
        #
        # make_bounmdaries_and_mesh: bool = True

    )

    with Hfss(version='2024.2', new_desktop=True,
              design='stam', project='stam.aedt',
              solution_type='Eigenmode',
              close_on_exit=True, remove_lock=True, non_graphical=False) as hfss:
        build(hfss, example_config)

        print(1)
