from scipy.optimize import fsolve
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
from dataclasses import dataclass, field, replace, asdict, fields
import pandas as pd
from abc import ABC, abstractmethod
from ansys.aedt.core.hfss import Hfss
from pathlib import Path


@dataclass
class Ellipse:
    name: str
    rx: float
    x0: float
    ry: float
    y0: float
    start_angle: float = 0
    stop_angle: float = 2 * np.pi
    num_points: int = 30

    def get_coordinates(self):
        thetas = np.linspace(
            self.start_angle, self.stop_angle, self.num_points)
        xs = self.rx * np.cos(thetas) + self.x0
        ys = self.ry * np.sin(thetas) + self.y0
        return xs, ys

    def to_dict(self):
        return {self.name: {
            "x0": self.x0,
            "y0": self.y0,
            "rx": self.rx,
            "ry": self.ry,
            "start angle": self.start_angle,
            "stop angle": self.stop_angle}}


@dataclass
class Line:
    name: str
    start_point: list
    end_point: list
    num_points: int = 10

    def get_coordinates(self):
        xs = np.linspace(self.start_point[0],
                         self.end_point[0], self.num_points)
        ys = np.linspace(self.start_point[1],
                         self.end_point[1], self.num_points)
        return xs, ys

    def to_dict(self):
        return {}


def half_cell_length(Rc: float, Lc: float, a: float, b: float, RI: float, decimal_precision: int = 6):
    """calculate the length of the cell for smooth connecting between coupler ellipse and cavity ellipse,
    The length is the distance between the center of the cavity ellipse to the center of the link ellipse on the x axis
    by equating gradints of the cavity elipse and coupler elipse we get conntection between the two parameters of the curves.
    by solving y=y' we get eqution for the spcific parameter, from x=x we get the length of the cell (x coordinate for the coupler ellipse)

    Args:
        Rc (float): Cell radius
        Lc (float): Cell length - cavity axis
        a (float): Iris ellipse axis perpendicular radius
        b (float): Iris ellipse axis parallel radius
        RI (float): Iris radius
    """

    def length_from_phi(phi: float):
        # solves for cell length for the given parameter
        return Lc * np.cos(np.arctan(np.tan(phi) * Rc * b / (Lc * a))) - b * np.cos(phi)

    def coupler_parameter_equation(phi):
        # equation to extract numerically the parameter that both elipse has the same gradinet and location
        return Rc * np.sin(np.arctan(np.tan(phi) * Rc * b / (Lc * a))) - a * np.sin(phi) - RI - a

    coupler_parameter = fsolve(coupler_parameter_equation, x0=np.pi)[0]
    cavity_parameter = np.arctan(np.tan(coupler_parameter) * Rc * b / (Lc * a))
    length = length_from_phi(coupler_parameter)

    return np.round(length, decimal_precision), np.round(cavity_parameter, decimal_precision), np.round(
        coupler_parameter, decimal_precision)


def fillet_circle_location(Rc: float, Lc: float, r_fillet: float):
    """create fillet circle for half cell.
    this function cacalate the angle paraemter for the fillet circle and the half cell,
    and for the fillet circle y0

    Args:
        Rc (float): half cell radius
        Lc (float): half cell length
        r_fillet (float): fillet radius
    """

    def theta(phi):
        """ from fillet circle parameter to cavity parmeter"""
        return np.arctan(np.tan(phi) * Rc / Lc)

    def parameter_equation(phi):
        # equation to extract numerically the parameter that both fillet circle and cell ellipse has the same gradinet and location
        return Lc * np.cos(theta(phi)) - r_fillet * np.cos(phi) - r_fillet

    def height_from_phi(phi):
        return Rc * np.sin(theta(phi)) - r_fillet * np.sin(phi)

    fillet_circle_parameter = fsolve(parameter_equation, x0=np.pi / 3)[0]
    cavity_parameter = theta(fillet_circle_parameter)
    for parameter in (fillet_circle_parameter, cavity_parameter):
        assert parameter < (
                np.pi / 2) or parameter > 0, f'parameter out of range'

    y0 = height_from_phi(fillet_circle_parameter)

    return y0, cavity_parameter, fillet_circle_parameter


@dataclass
class TwoModeCavityParameters:
    # Transmon wavguide coupler
    transmon_coupler_a: float = 1
    transmon_coupler_b: float = 0.5
    transmon_wg_radius: float = 2
    # transmon half cell
    half_cell_Rc: float = 31
    half_cell_Lc: float = 21
    # fillet
    half_cell_fillet_radius: float = 4

    # Coupler
    coupler_a: float = 2
    coupler_b: float = 1
    Iris_radius: float = 14

    # Full cell
    full_cell_Rc: float = 30.14
    full_cell_Lc: float = 21

    # Cavity drive wavguide coupler
    cavity_drive_wg_radius: float = 8
    cavity_drive_wg_length: float = 18

    # Misc
    # for building HFSS model, used by coupler module to create cxavcity pin
    cavity_z_end: float = field(default_factory=float)
    cavity_z_midpoint: float = field(default_factory=float)


@dataclass
class TwoModeCavityCurveParameters(TwoModeCavityParameters):
    # Transmon wavguide coupler

    # transmon half cell

    half_cell_parameter_start: float = field(default_factory=float)
    half_cell_parameter_stop: float = field(default_factory=float)
    half_cell_length: float = field(default_factory=float)
    # fillet
    half_cell_fillet_circle_parameter: float = field(default_factory=float)
    half_cell_fillet_circle_y0: float = field(default_factory=float)

    # Coupler

    coupler_parameter_start: float = field(default_factory=float)
    coupler_parameter_stop: float = field(default_factory=float)

    # Full cell
    full_cell_coupler_side_length: float = field(default_factory=float)
    full_cell_wg_side_length: float = field(default_factory=float)
    full_cell_coupler_side_parameter: float = field(default_factory=float)
    full_cell_wg_side_parameter: float = field(default_factory=float)

    # Cavity drive wavguide coupler
    cavity_drive_wg_parameter: float = field(default_factory=float)

    # Misc
    points_per_segment: int = 50
    decimal_precision: int = 6

    def __post_init__(self):
        """
        getting the cells length and parameters for creatign amooth connections between componenets
        """
        self.half_cell_fillet_circle_y0, self.half_cell_parameter_start, self.half_cell_fillet_circle_parameter = fillet_circle_location(
            self.half_cell_Rc,
            self.half_cell_Lc,
            self.half_cell_fillet_radius)
        self.half_cell_length, self.half_cell_parameter_stop, self.coupler_parameter_start = half_cell_length(
            self.half_cell_Rc,
            self.half_cell_Lc,
            self.coupler_a,
            self.coupler_b,
            self.Iris_radius,
            self.decimal_precision)

        self.full_cell_coupler_side_length, self.full_cell_coupler_side_parameter, coupler_parameter_stop = half_cell_length(
            self.full_cell_Rc,
            self.full_cell_Lc,
            self.coupler_a,
            self.coupler_b,
            self.Iris_radius,
            decimal_precision=self.decimal_precision)

        self.coupler_parameter_stop = np.round(
            3 * np.pi - coupler_parameter_stop, self.decimal_precision)  # adjusting for proper quarter

        self.full_cell_wg_side_length, self.full_cell_wg_side_parameter, self.cavity_drive_wg_parameter = half_cell_length(
            self.full_cell_Rc,
            self.full_cell_Lc,
            self.coupler_a,
            self.coupler_b,
            self.cavity_drive_wg_radius,
            decimal_precision=self.decimal_precision)
        cavity_z_end = self.half_cell_length + self.full_cell_coupler_side_length + \
                       self.full_cell_wg_side_length + self.cavity_drive_wg_length
        self.cavity_z_end = np.round(cavity_z_end, self.decimal_precision)


class Cavity(ABC):
    def __init__(self, curve_parameters):
        self.curve_parameters = curve_parameters
        self.structure = self._define_structure()
        self.x_coordinates, self.y_coordinates = self._make_coordinate_list()
        self.xy_coordinates = list(zip(self.x_coordinates, self.y_coordinates))
        self.structure_dict = self.to_dict()

    @abstractmethod
    def _define_structure(self):
        pass

    def to_dict(self):
        structure_dict = {}
        for segment in self.structure:
            structure_dict.update(segment.to_dict())

        return structure_dict

    def save_parameters(self, path_name):
        df = pd.DataFrame(self.structure_dict)
        path_name = Path(path_name).with_suffix(".csv")
        df.to_csv(path_name)
        np.isclose

    @staticmethod
    def _filter_close_coordinates(coordinates, tolerance=1.e-6):
        """Filtering coordinates by proximity,
            resolving errors in Hfss 2024.2 when creating a polyline

        Args:
            coordiante_list (_type_): _description_
        """
        dist_norm = np.linalg.norm(np.diff(coordinates, axis=0), axis=1)
        boolian_index = np.isclose(dist_norm, 0, atol=tolerance)
        boolian_index = np.concatenate(((False,), boolian_index))
        filtered_coordinates = coordinates[np.logical_not(boolian_index)]
        return filtered_coordinates[:, 0].tolist(), filtered_coordinates[:, 1].tolist()

    def _make_coordinate_list(self):
        coordinates = [segment.get_coordinates() for segment in self.structure]
        x = [x for c in coordinates for x in c[0]]
        y = [y for c in coordinates for y in c[1]]
        coordinates = np.stack([x, y], axis=-1)
        x, y = self._filter_close_coordinates(coordinates=coordinates)
        return x, y

    def build_hfss_model(self, hfss: Hfss):

        modeler = hfss.modeler
        points = [[0, self.y_coordinates[i], self.x_coordinates[i]]
                  for i in range(len(self.x_coordinates))]  # Choosing Z as cavity axis

        """ MODEL"""

        # CAVITY
        # , xsection_bend_type='curved', cover_surface=True)
        cavity = modeler.create_polyline(points, name='cavity',
                                         segment_type='Spline',
                                         material='vacuum')

        cavity.insert_segment([[0, 0, points[0][2]], points[0]])
        cavity.insert_segment([points[-1], [0, 0, points[-1][-1]]])
        cavity.insert_segment([cavity.points[0], cavity.points[-1]])
        assert modeler.cover_lines(cavity)
        cavity.sweep_around_axis('z')

        self._post_hfss_build(hfss)

    def _post_hfss_build(self, hfss: Hfss):
        pass

    def plot(self, plot_double_side=True):
        fig, ax = plt.subplots()
        ax.plot(self.x_coordinates, self.y_coordinates, color='tab:blue')
        ax.set_xlabel('distance mm')
        ax.set_ylabel('distance mm')
        ax.set_title('Cavity Line')
        ax.set_aspect('equal', adjustable='datalim')
        if plot_double_side:
            ax.plot(self.x_coordinates,
                    [-y for y in self.y_coordinates], color='tab:blue')
            ax.set_ylim([-1.1 * np.max(self.y_coordinates),
                         1.1 * np.max(self.y_coordinates)])

        return fig, ax

    def plot_structure(self):
        # colormap = matplotlib.colormaps['tab10']
        def angles_mapping(segment):
            if 'half_cell' in segment.name:
                start = np.pi / 2
                stop = 0
            elif 'full_cell' in segment.name:
                start = np.pi
                stop = 0
            else:
                start = 0
                stop = 2 * np.pi
            return start, stop

        fig, ax = plt.subplots()
        for i, segment_ in enumerate(self.structure):
            if isinstance(segment_, Ellipse):
                start, stop = angles_mapping(segment_)
                segment = replace(segment_, start_angle=start, stop_angle=stop)
                coordinates = segment.get_coordinates()
                # , color=colormap(i))
                ax.plot(coordinates[0], coordinates[1],
                        '--', label=segment.name, linewidth=2.75)
                # ax.text(segment.x0, segment.y0 + segment.ry, segment.name )
        ax.scatter(self.x_coordinates, self.y_coordinates, color='black', alpha=1)
        # ax.set_xlim([-5, 100])
        ax.set_xlabel('distance mm')
        ax.set_ylabel('distance mm')
        ax.set_title('Cavity Structure')
        ax.set_aspect('equal', adjustable='datalim')
        # ,bbox_to_anchor=(0.5, 1))
        ax.legend(loc='best', ncol=1, fancybox=True, shadow=True)


class TwoModeCavity(Cavity):
    def __init__(self, parameters: TwoModeCavityParameters):
        self._parameters: TwoModeCavityParameters = parameters
        curve_parameters: TwoModeCavityCurveParameters = TwoModeCavityCurveParameters(
            **vars(parameters))
        self._parameters.cavity_z_end = curve_parameters.cavity_z_end
        self._parameters.cavity_z_midpoint = curve_parameters.half_cell_length
        super().__init__(curve_parameters=curve_parameters)

    # protecting the parametrs of the cavity
    @property
    def parameters(self):
        return TwoModeCavityParameters(**vars(self._parameters))

    @parameters.setter
    def parameters(self, *args, **kwargs):
        raise NotImplementedError("Direct modification of parameters is not allowed. Please create new cavity instance")

    def _define_structure(self):
        transmon_wg_coupler = Ellipse('transmon_wg_coupler',
                                      rx=self.curve_parameters.transmon_coupler_b,
                                      x0=-self.curve_parameters.transmon_coupler_b,
                                      ry=self.curve_parameters.transmon_coupler_a,
                                      y0=self.curve_parameters.transmon_wg_radius +
                                         self.curve_parameters.transmon_coupler_a,
                                      start_angle=-np.pi / 2, stop_angle=0,
                                      num_points=self.curve_parameters.points_per_segment // 2)

        connecting_line = Line('half_cell_plane',
                               start_point=[
                                   0,
                                   self.curve_parameters.transmon_wg_radius + self.curve_parameters.transmon_coupler_a],
                               end_point=[
                                   0, self.curve_parameters.half_cell_fillet_circle_y0],
                               num_points=self.curve_parameters.points_per_segment // 4)

        fillet_circle = Ellipse('fillet',
                                rx=self.curve_parameters.half_cell_fillet_radius,
                                x0=self.curve_parameters.half_cell_fillet_radius,
                                ry=self.curve_parameters.half_cell_fillet_radius,
                                y0=self.curve_parameters.half_cell_fillet_circle_y0,
                                start_angle=np.pi,
                                stop_angle=self.curve_parameters.half_cell_fillet_circle_parameter,
                                num_points=self.curve_parameters.points_per_segment // 2)

        half_cell = Ellipse('half_cell',
                            self.curve_parameters.half_cell_Lc, 0,
                            self.curve_parameters.half_cell_Rc, 0,
                            self.curve_parameters.half_cell_parameter_start,
                            self.curve_parameters.half_cell_parameter_stop, self.curve_parameters.points_per_segment)

        coupler = Ellipse('coupler',
                          self.curve_parameters.coupler_b, self.curve_parameters.half_cell_length,
                          self.curve_parameters.coupler_a, self.curve_parameters.Iris_radius +
                          self.curve_parameters.coupler_a,
                          self.curve_parameters.coupler_parameter_start,
                          self.curve_parameters.coupler_parameter_stop,
                          self.curve_parameters.points_per_segment // 2)

        full_cell = Ellipse('full_cell',
                            self.curve_parameters.full_cell_Lc,
                            self.curve_parameters.half_cell_length +
                            self.curve_parameters.full_cell_coupler_side_length,
                            self.curve_parameters.full_cell_Rc, 0,
                            np.pi - self.curve_parameters.full_cell_coupler_side_parameter,
                            self.curve_parameters.full_cell_wg_side_parameter,
                            self.curve_parameters.points_per_segment
                            )
        cavity_drive_wg_coupler = Ellipse('drive_wg_coupler',
                                          self.curve_parameters.coupler_b,
                                          self.curve_parameters.half_cell_length + self.curve_parameters.full_cell_coupler_side_length +
                                          self.curve_parameters.full_cell_wg_side_length,
                                          self.curve_parameters.coupler_a,
                                          self.curve_parameters.cavity_drive_wg_radius +
                                          self.curve_parameters.coupler_a,
                                          self.curve_parameters.cavity_drive_wg_parameter, 3 *
                                          np.pi / 2, self.curve_parameters.points_per_segment // 2
                                          )
        cavity_drive_wg = Line('cavity drive waveguide',
                               start_point=[
                                   self.curve_parameters.half_cell_length + self.curve_parameters.full_cell_coupler_side_length
                                   + self.curve_parameters.full_cell_wg_side_length,
                                   self.curve_parameters.cavity_drive_wg_radius],
                               end_point=[
                                   self.curve_parameters.half_cell_length + self.curve_parameters.full_cell_coupler_side_length + self.curve_parameters.full_cell_wg_side_length + self.curve_parameters.cavity_drive_wg_length,
                                   self.curve_parameters.cavity_drive_wg_radius],
                               num_points=self.curve_parameters.points_per_segment // 2)
        # return (transmon_wg_coupler, half_cell, coupler, full_cell, cavity_drive_wg_coupler)
        return (
            transmon_wg_coupler, connecting_line, fillet_circle, half_cell, coupler, full_cell, cavity_drive_wg_coupler,
            cavity_drive_wg)

    # def make_boundaries(self, hfss):


@dataclass
class DoubleTeslaCouplersParameters():
    # Cavity Drive Waveguide and Pin
    cavity_drive_pin_diamter: float = 1
    cavity_drive_pin_length: float = 3
    cavity_drive_pin_encloser_diamter: float = 2.3
    cavity_drive_pin_encloser_length: float = 4

    # Sapphire House And Pins
    sapphire_house_length: float = 22
    pin_1_location = 8  # distance from the shroom surface
    pin_2_location = 11  # distance from the shroom surface
    pin_3_location = 15  # distance from the shroom surface
    pin_4_location = 18  # distance from the shroom surface
    spacer: float = 1
    sapphire_house_pins_diameter: float = 0.5
    sapphire_house_pins_waveguide_diameter: float = 1.15
    sapphire_house_pins_waveguide_length: float = 6
    pin_1_length: float = 6
    pin_2_length: float = 0
    pin_3_length: float = 6.75
    pin_4_length: float = 0

    # Simulation Boundaris
    maximum_mesh_size_mm: float = 2

    make_bounmdaries_and_mesh: bool = True


class DoubleTeslaCouplers:
    def __init__(self, parameters: DoubleTeslaCouplersParameters):
        self.parameters: DoubleTeslaCouplersParameters = parameters

    def build_hfss_model(self, hfss: Hfss):
        self.build_sapphire_house(hfss)
        self.make_boundaries(hfss)

    def Boundaries_and_mesh(self, hfss: Hfss, top_face_z):
        modeler = hfss.modeler
        # Mesh
        hfss.mesh.assign_length_mesh(["cavity", ], isinside='True',
                                     maxlength=f"{self.parameters.maximum_mesh_size_mm}mm", maxel=None,
                                     meshop_name="CavityMesh")

        # Boundaray Conditions
        boundry_object = modeler.create_object_from_face(top_face_z)
        boundry_object.name = "cavity_drive_rlc_bound"
        boundary_arrow_start = top_face_z.center
        boundary_arrow_end = top_face_z.center
        # making the arrow point the positie y direction
        boundary_arrow_end[1] += 1
        hfss.assign_lumped_rlc_to_sheet(boundry_object.name, axisdir=[boundary_arrow_start, boundary_arrow_end],
                                        sourcename="cavity_drive", rlctype='"Parallel"',
                                        Rvalue=50, Lvalue=None, Cvalue=None)

    def make_boundaries(self, hfss):
        modeler = hfss.modeler
        for n in ["pin_1_wg", "pin_3_wg"]:

            top_face_z = modeler[n].bottom_face_z
            # top_face_z = modeler["pin_3_wg"].top_face_z

            boundry_object = modeler.create_object_from_face(top_face_z)

            boundry_object.name = f"{n}_rlc_bound"
            boundary_arrow_start = top_face_z.center
            boundary_arrow_end = top_face_z.center
            # making the arrow point the positie y direction
            boundary_arrow_end[2] += 0.575
            hfss.assign_lumped_rlc_to_sheet(boundry_object.name,
                                            start_direction=[boundary_arrow_start, boundary_arrow_end],
                                            rlc_type='Parallel',
                                            resistance=50, inductance=None, capacitance=None)

    def build_cavity_wg(self, hfss: Hfss):
        modeler = hfss.modeler
        # CAVITY DRIVE WAVEGUIDE PIN
        if modeler["cavity_wg"]:
            # for CAD imported shroom model
            top_face_z = modeler["cavity_wg"].top_face_z
        else:
            top_face_z = modeler["cavity"].top_face_z
        cavity_drive_pin_encloser = modeler.create_cylinder(orientation='Z', origin=top_face_z.center,
                                                            radius='cavity_drive_pin_encloser_diamter/2',
                                                            height='cavity_drive_pin_encloser_length',
                                                            name='cavity_drive_pin_ecloser', material='vacuum')
        top_face_z = cavity_drive_pin_encloser.top_face_z
        cavity_drive_pin = modeler.create_cylinder(orientation='Z', origin=top_face_z.center,
                                                   radius='cavity_drive_pin_diamter/2',
                                                   height='-cavity_drive_pin_encloser_length -cavity_drive_pin_length',
                                                   name='cavity_drive_pin', material='perfect conductor')
        return top_face_z

    def build_sapphire_house(self, hfss: Hfss):
        modeler = hfss.modeler
        # SAPPHIRE HOUSE
        sapphire_house_back_cylin1 = modeler.create_cylinder(orientation='Z', origin=[0, 2.5, '-sapphire_house_length'],
                                                             radius=3.5, height='-spacer',
                                                             name='saph_house_back_cylin1', material='vacuum')
        sapphire_house_back_cylin2 = modeler.create_cylinder(orientation='Z',
                                                             origin=[0, -2.5, '-sapphire_house_length'],
                                                             radius=3.5, height='-spacer',
                                                             name='saph_house_back_cylin2', material='vacuum')
        sapphire_house_back = modeler.create_box(origin=[-3.5, -2.5, '-sapphire_house_length'], sizes=[7, 5, '-spacer'],
                                                 name='sapphire_house_back', material='vacuum')
        sapphire_house_cylinder = modeler.create_cylinder(orientation='Z', origin=[0, 0, '-sapphire_house_length'],
                                                          radius='transmon_wg_radius', height='sapphire_house_length',
                                                          name='sapphire_house_wg', matname='vacuum')
        # Creating pin wgs
        pin_wg_1 = modeler.create_cylinder(cs_axis='Y', position=[0, 0, f'-{self.parameters.pin_1_location}'],
                                           radius='sapphire_house_pins_waveguide_diameter/2',
                                           height=f'transmon_wg_radius + sapphire_house_pins_waveguide_length',
                                           name=f'pin_1_wg', matname='vacuum')

        pin_wg_2 = modeler.create_cylinder(cs_axis='Y', position=[0, 0, f'-{self.parameters.pin_2_location}'],
                                           radius='sapphire_house_pins_waveguide_diameter/2',
                                           height=f'-transmon_wg_radius - sapphire_house_pins_waveguide_length',
                                           name=f'pin_2_wg', matname='vacuum')

        pin_wg_3 = modeler.create_cylinder(cs_axis='Y', position=[0, 0, f'-{self.parameters.pin_3_location}'],
                                           radius='sapphire_house_pins_waveguide_diameter/2',
                                           height=f'transmon_wg_radius + sapphire_house_pins_waveguide_length',
                                           name=f'pin_3_wg', matname='vacuum')

        pin_wg_4 = modeler.create_cylinder(cs_axis='Y', position=[0, 0, f'-{self.parameters.pin_4_location}'],
                                           radius='sapphire_house_pins_waveguide_diameter/2',
                                           height=f'-transmon_wg_radius - sapphire_house_pins_waveguide_length',
                                           name=f'pin_4_wg', matname='vacuum')

        # Creating pins
        pin_1 = modeler.create_cylinder(cs_axis='Y',
                                        position=[0, f'transmon_wg_radius + sapphire_house_pins_waveguide_length',
                                                  f'-{self.parameters.pin_1_location}'],
                                        radius='sapphire_house_pins_diameter/2',
                                        height=f'-pin_1_length',
                                        name=f'transmon_pin', matname='perfect conductor')
        #
        # pin_2 = modeler.create_cylinder(cs_axis='Y',
        #                                 position=[0, f'-transmon_wg_radius - sapphire_house_pins_waveguide_length',
        #                                           f'-{self.parameters.pin_2_location}'],
        #                                 radius='sapphire_house_pins_diameter/2',
        #                                 height=f'pin_2_length',
        #                                 name=f'readout_pin', matname='perfect conductor')

        pin_3 = modeler.create_cylinder(cs_axis='Y',
                                        position=[0, f'transmon_wg_radius + sapphire_house_pins_waveguide_length',
                                                  f'-{self.parameters.pin_3_location}'],
                                        radius='sapphire_house_pins_diameter/2',
                                        height=f'-pin_3_length',
                                        name=f'pin_3', matname='perfect conductor')

        # pin_4 = modeler.create_cylinder(cs_axis='Y',
        #                                 position=[0, f'-transmon_wg_radius - sapphire_house_pins_waveguide_length',
        #                                           f'-{self.parameters.pin_4_location}'],
        #                                 radius='sapphire_house_pins_diameter/2',
        #                                 height=f'pin_4_length',
        #                                 name=f'pin_4', matname='perfect conductor')


# cavity_params = TwoModeCavityParameters()
# cavity = TwoModeCavity(cavity_params)
# # Couplers - Sapphire house, cavity wave guide and pins
# couplers_params = DoubleTeslaCouplersParameters(pin_2_length=6.735, spacer=0.001)
# couplers = DoubleTeslaCouplers(couplers_params)


class SystemModeler():
    def __init__(self, parameters,
                 cavity: Cavity = None,
                 couplers: DoubleTeslaCouplers = None):
        self.parametres = parameters
        self.cavity: Cavity = cavity
        self.couplers: DoubleTeslaCouplers = couplers
        self.parts_list = (self.cavity, self.couplers)
        self.hfss_variables_dict: dict = dict()
        # self.setup: SetupHFSS = None
        self.hfss: Hfss = None

    def initialize_hfss_session(self):
        self.hfss = Hfss(new_desktop=self.parametres.new_desktop,
                         version=self.parametres.desktop_version,
                         non_graphical=self.parametres.non_graphical,
                         project=self.parametres.project_name,
                         # solution_type= self.parametres.solution_type,
                         design=self.parametres.design_name,
                         close_on_exit=False)

        # self.hfss.modeler.model_units = "mm"

    def add_design(self, design_name: str, solution_type: str = None):
        self.hfss.insert_design(design_name, solution_type)

    def set_active_desing(self, design_name: str):
        self.hfss.set_active_design(design_name)

    def create_setup(self, name: str, setup_type: str = "HFSSEigen", **kwargs):
        """_summary_
        available properties for eigen mode solution type:
            ['MinimumFrequency',
            'NumModes',
            'MaxDeltaFreq',
            'ConvergeOnRealFreq',
            'MaximumPasses',
            'MinimumPasses',
            'MinimumConvergedPasses',
            'PercentRefinement',
            'IsEnabled',
            'MeshLink',
            'MeshLink/ImportMesh',
            'BasisOrder',
            'DoLambdaRefine',
            'DoMaterialLambda',
            'SetLambdaTarget',
            'Target',
            'UseMaxTetIncrease']
        Args:
            setup_name (str): _description_
            setup_type (str, optional): ``"HFSSDrivenAuto"``, ``"HFSSDrivenDefault"``, ``"HFSSEigen"``, ``"HFSSTransient"``,
            and ``"HFSSSBR"`` Defaults to "HFSSEigen".

        """
        try:
            # Defaulting to mixed basis order
            basis_order = kwargs["BasisOrder"]
        except KeyError as err:
            kwargs["BasisOrder"] = -1
        self.setup = self.hfss.create_setup(name=name, setup_type=setup_type, **kwargs)

    def save_hfss_model(self, directory_path: str):
        # if directory_path == None:
        #     directory_path = self.parametres.directory_path or getcwd()
        project_pathname = Path(directory_path, self.parametres.project_name)
        self.hfss.save_project(filename := str(project_pathname.with_suffix('.aedt')))
        return filename

    # def save_parametres(self, directory_path: str = None):
    #     full_sysytem_parameters = {type(part).__name__: vars(part.parameters) for part in self.parts_list}
    #     parameters_file_path = Path(self.parametres.directory_path,
    #                                 f"{self.parametres.design_name}_parametrs").with_suffix('.yaml')
    #     with open(parameters_file_path, 'w+') as fp:
    #         yaml.dump(full_sysytem_parameters, fp)

    def save_all(self, directory_path: str = None):
        self.save_hfss_model(directory_path)
        # self.save_parametres(directory_path)

    def _load_parameters_to_hfss(self):
        # making filtered list if cavity or chip is not given
        parameters_list = [obj.parameters for obj in (self.cavity, self.couplers) if obj is not None]
        for parameters in parameters_list:
            self._update_hfss_dict(params_class=parameters, default_units=self.parametres.default_units)

        # setting hfss variables
        for key, value in self.hfss_variables_dict.items():
            # expression, default_units = value
            self.hfss.variable_manager.set_variable(name=key, expression=value)

    def _update_hfss_dict(self, params_class: dataclass, default_units):
        for param_field in fields(params_class):
            key = param_field.name
            value = getattr(params_class, param_field.name)
            if isinstance(value, bool):
                continue
            value_str = value if param_field.type is str else f'{value}{default_units}'
            self.hfss_variables_dict.update({key: value_str})

    def delete_all(self):
        modeler = self.hfss.modeler
        solid_list = modeler.solid_objects
        sheet_list = modeler.sheet_objects
        line_list = modeler.line_objects
        if solid_list:
            modeler.delete(solid_list)
        if sheet_list:
            modeler.delete(sheet_list)
        if line_list:
            modeler.delete(line_list)

        # deleting existing variables
        for var_name in self.hfss.variable_manager.variable_names:
            self.hfss.variable_manager.delete_variable(var_name)

    def build_hfss_model(self):
        self._load_parameters_to_hfss()
        for part in self.parts_list:
            if part:
                part.build_hfss_model(self.hfss)
        # Uniting Vacuum objects
        vacuum_objects = list(filter(lambda object: object.material_name == 'vacuum', self.hfss.modeler.solid_objects))
        cavity_solid_name = self.hfss.modeler.unite(vacuum_objects)
        # cavity_solid_object = self.hfss.modeler.get_object_from_name(cavity_solid_name)
        print('HFSS completed')


def build(
        hfss: Hfss,
        design_name: str,
        cavity_params: dict = None,
        couplers_params: dict = None):
    if cavity_params is None:
        cavity_params = {}

    if couplers_params is None:
        couplers_params = {}

    cavity_params = TwoModeCavityParameters(**cavity_params)
    cavity = TwoModeCavity(cavity_params)

    couplers_params = DoubleTeslaCouplersParameters(**couplers_params)
    couplers = DoubleTeslaCouplers(couplers_params)


    default_units = "mm"

    hfss.set_active_design('design')

    hfss.delete_design(design_name)

    hfss.save_project()


    hfss.insert_design(design_name, 'Eigenmode')

    # hfss.modeler.delete('cavity')

    part_list = (cavity, couplers)
    combined_dict = {}
    for p in part_list:
        d = asdict(p.parameters)
        # filtering bool and cast non str to str with units
        d = filter(lambda x: type(x[1]) is not bool, d.items())
        d = map(lambda x: x if type(x[1]) is str else (x[0], f'{x[1]}{default_units}'), d)
        d = dict(d)
        combined_dict.update(d)

    # setting hfss variables
    for key, value in combined_dict.items():
        # expression, default_units = value
        hfss.variable_manager.set_variable(name=key, expression=value)

    for part in part_list:
        part.build_hfss_model(hfss)

    # Uniting Vacuum objects
    vacuum_objects = list(filter(lambda object: object.material_name == 'vacuum', hfss.modeler.solid_objects))
    # print(vacuum_objects)
    cavity_solid_name = hfss.modeler.unite(vacuum_objects)

    hfss.mesh.assign_length_mesh('cavity',
                                 inside_selection=True,
                                 name='cavity_mesh',
                                 maximum_length='4mm')



    # hfss.save_project()

    hfss.set_active_design('design')

    setup = hfss.get_setup('Setup1')

    # hfss.modeler.copy(['ChipBase'])  # Copy the object by its name
    hfss.modeler.copy(['ChipBase', 'JJ', 'Transmon1', 'Transmon2', 'jj_meshbox', 'trpad_meshbox', 'line_jj1'])  # Copy the object by its name

    hfss.set_active_design(design_name)

    # Paste the object into the target design
    hfss.modeler.paste()

    hfss.assign_perfecte_to_sheets(['Transmon1', 'Transmon2'])

    hfss.mesh.assign_length_mesh(['Transmon1', 'Transmon2'],
                                 inside_selection=False,
                                 name='perfect_e_mesh',
                                 maximum_length='50um')

    hfss.create_setup('Setup1', **setup.props)

    hfss.save_project()


    return cavity_params


if __name__ == '__main__':
    pass
