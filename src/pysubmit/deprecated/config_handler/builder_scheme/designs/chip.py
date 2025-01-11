from ansys.aedt.core.hfss import Hfss


from drawing.designs.chip_house_cylinder.config import ChipHouseCylinderConfig, Variable
from drawing.meader.euler import meander_euler
from drawing.export_to_pyaedt.parser import parse_component, ExportConfig



def build(hfss: Hfss, config: ChipHouseCylinderConfig):
    modeler = hfss.modeler

    variables = config.get_variables()
    for v in variables:
        hfss[v.name] = v.to_string()

    # CHIP HOUSE
    chip_house_back_cylinder_a = modeler.create_cylinder(orientation='Z',
                                                         origin=[0, 2.5, f'-{config.chip_house_length.name}'],
                                                         radius=3.5,
                                                         height=f'-{config.spacer_length.name}',
                                                         name='chip_house_back_cylinder_a', material='vacuum')

    chip_house_back_cylinder_b = modeler.create_cylinder(orientation='Z',
                                                         origin=[0, -2.5, f'-{config.chip_house_length.name}'],
                                                         radius=3.5,
                                                         height=f'-{config.spacer_length.name}',
                                                         name='chip_house_back_cylinder_b', material='vacuum')

    chip_house_back_rect = modeler.create_box(origin=[-3.5, -2.5, f'-{config.chip_house_length.name}'],
                                              sizes=[7, 5, f'-{config.spacer_length.name}'],
                                              name='chip_house_back_rect', material='vacuum')

    chip_house_cylinder = modeler.create_cylinder(orientation='Z',
                                                  origin=[0, 0, f'-{config.chip_house_length.name}'],
                                                  radius=config.chip_house_radius.name,
                                                  height=config.chip_house_length.name,
                                                  name='chip_house_waveguide', material='vacuum')

    # # Creating pin wgs

    pin_wg_1 = modeler.create_cylinder(orientation='Y',
                                       origin=[0, 0, f'-{config.pin_a_location.name}'],
                                       radius=config.pin_waveguide_radius.name,
                                       height=f'{config.chip_house_radius.name} + {config.pin_waveguide_length.name}',
                                       name=f'chip_pin_a_waveguide', material='vacuum')

    pin_wg_2 = modeler.create_cylinder(orientation='Y',
                                       origin=[0, 0, f'-{config.pin_b_location.name}'],
                                       radius=config.pin_waveguide_radius.name,
                                       height=f'-{config.chip_house_radius.name} - {config.pin_waveguide_length.name}',
                                       name=f'chip_pin_b_waveguide', material='vacuum')

    pin_wg_3 = modeler.create_cylinder(orientation='Y',
                                       origin=[0, 0, f'-{config.pin_c_location.name}'],
                                       radius=config.pin_waveguide_radius.name,
                                       height=f'{config.chip_house_radius.name} + {config.pin_waveguide_length.name}',
                                       name=f'chip_pin_c_waveguide', material='vacuum')

    pin_wg_4 = modeler.create_cylinder(orientation='Y',
                                       origin=[0, 0, f'-{config.pin_d_location.name}'],
                                       radius=config.pin_waveguide_radius.name,
                                       height=f'-{config.chip_house_radius.name} - {config.pin_waveguide_length.name}',
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
                                            f'{config.chip_house_radius.name} + {config.pin_waveguide_length.name}',
                                            f'-{config.pin_c_location.name}'],
                                    radius=config.pin_conductor_radius.name,
                                    height=f'-{config.pin_c_length.name}',
                                    name=f'pin_3', material='perfect conductor')

    top_face_z = pin_wg_3.bottom_face_z
    boundary_object = modeler.create_object_from_face(top_face_z)
    boundary_arrow_start = top_face_z.center
    boundary_arrow_end = top_face_z.center
    boundary_arrow_end[2] += config.pin_waveguide_radius.value
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
    chip_base = modeler.create_box(origin=[f'-{config.chip_base_width.name} / 2',
                                           f'-{config.chip_base_thickness.name} / 2',
                                           f'-{config.chip_house_length.name} - {config.spacer_length.name}'],
                                   sizes=[config.chip_base_width.name,
                                          config.chip_base_thickness.name,
                                          config.chip_base_length.name],
                                   name='chip_base', material=config.chip_base_material)

    # adding meander
    meander = meander_euler(**config.meander_args)
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
    hfss['readout_e1_y'] = f'{config.chip_base_thickness.name} / 2'
    hfss['readout_e1_z'] = f'-{config.chip_base_length.name} / 2'

    # add a bbox as non model for meshing
    readout_mesh_box = modeler.create_box(origin=['-readout_e1_x - readout_size_x / 2',
                                                  'readout_e1_y - readout_size_y / 2 - 0.5mm',
                                                  'readout_e1_z'],
                                          sizes=['readout_size_x', 'readout_size_y + 1mm', 'readout_size_z'],
                                          name='readout_mesh_box',
                                          non_model=True
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

    hfss.create_setup('Setup1')
    setup = hfss.get_setup('Setup1')
    hfss.save_project()
    setup.props(**basic_eigenmode_properties)

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
    example_config = ChipHouseCylinderConfig(
        type='chip_house_cylinder',
        spacer_length=Variable(name='spacer_length', value=1, unit='mm'),
        chip_house_length=Variable(name='chip_house_length', value=26, unit='mm'),
        chip_house_radius=Variable(name='chip_house_radius', value=2, unit='mm'),

        chip_base_length=Variable(name='chip_base_length', value=22, unit='mm'),
        chip_base_thickness=Variable(name='chip_base_thickness', value=381, unit='um'),
        chip_base_width=Variable(name='chip_base_width', value=2, unit='mm'),
        chip_base_material='silicon',

        pin_waveguide_radius=Variable(name='pin_waveguide_radius', value=0.575, unit='mm'),
        pin_waveguide_length=Variable(name='pin_waveguide_length', value=6, unit='mm'),
        pin_conductor_radius=Variable(name='pin_conductor_radius', value=0.25, unit='mm'),

        pin_a_location=Variable(name='chip_pin_a_location', value=8, unit='mm'),
        pin_b_location=Variable(name='chip_pin_b_location', value=11, unit='mm'),
        pin_c_location=Variable(name='chip_pin_c_location', value=15, unit='mm'),
        pin_c_length=Variable(name='chip_pin_c_length', value=6, unit='mm'),
        pin_d_location=Variable(name='chip_pin_d_location', value=18, unit='mm'),

        meander_type='euler',
        meander_args={
            'wire_width': 100,
            'height': 1500,
            'padding_length': 500,
            'spacing': 200,
            'radius': 50,
            'num_turns': 9
        }

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
