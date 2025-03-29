from dataclasses import dataclass, field, replace, asdict
import numpy as np
import pandas as pd
from scipy.optimize import fsolve
from abc import ABC, abstractmethod
import matplotlib.pyplot as plt
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


def add_cavity(hfss, **parameters):

    default_units = 'mm'

    double_cavity_parameters = TwoModeCavityParameters(**parameters)
    double_cavity = TwoModeCavity(double_cavity_parameters)

    combined_dict = {}
    d = asdict(double_cavity.parameters)

    # filtering bool and cast non str to str with units
    d = filter(lambda x: type(x[1]) is not bool, d.items())
    d = map(lambda x: x if type(x[1]) is str else (x[0], f'{x[1]}{default_units}'), d)
    d = dict(d)
    combined_dict.update(d)

    # setting hfss variables
    for key, value in combined_dict.items():
        # expression, default_units = value
        hfss.variable_manager.set_variable(name=key, expression=value)


    double_cavity.build_hfss_model(hfss)

