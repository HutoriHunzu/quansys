from ansys.aedt.core.hfss import Hfss

# from pysubmit.shared.variables import ValuedVariable

from drawing.meader.euler import meander_euler
from drawing.export_to_pyaedt.parser import parse_component, ExportConfig

from pydantic import BaseModel, Field
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


class MeanderArgs(BaseModel):
    wire_width: int = 100
    height: int = 1500
    padding_length: int = 500
    spacing: int = 200
    radius: int = 50
    num_turns: int = 9


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
    pin_c_length: Value = Value(value=6)
    pin_d_location: Value = Value(value=18)

    meander_type: str = 'euler'
    meander_args: MeanderArgs = MeanderArgs()


def build(hfss: Hfss,
          design_name: str = 'my_design',
          setup_name: str = 'Setup1',
          **kwargs):
    # creating design

    hfss.set_active_design('temp')

    if design_name in hfss.design_list:
        hfss.delete_design(design_name)

    hfss.save_project()

    hfss.insert_design(design_name, 'Eigenmode')
    hfss.set_active_design(design_name)

    # parameters = parameters or {}

    parameters = ChipHouseCylinderParameters(**kwargs)

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

    # BUILD CHIP
    chip_base = modeler.create_box(origin=[f'-{VarsNames.chip_base_width} / 2',
                                           f'-{VarsNames.chip_base_thickness} / 2',
                                           f'-{VarsNames.chip_house_length} - {VarsNames.spacer_length}'],
                                   sizes=[VarsNames.chip_base_width,
                                          VarsNames.chip_base_thickness,
                                          VarsNames.chip_base_length],
                                   name='chip_base', material=parameters.chip_base_material)

    # adding meander
    meander = meander_euler(**dict(parameters.meander_args))
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

    # add a bbox as non model for meshing
    readout_mesh_box = modeler.create_box(origin=['-readout_e1_x - readout_size_x / 2',
                                                  'readout_e1_y - readout_size_y / 2 - 0.5mm',
                                                  'readout_e1_z'],
                                          sizes=['readout_size_x', 'readout_size_y + 1mm', 'readout_size_z'],
                                          name='readout_mesh_box',
                                          model=False
                                          )

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
