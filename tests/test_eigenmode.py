import pytest
from quansys.simulation import EigenmodeAnalysis


NUM_OF_MODES_IN_SETUP = 5

def test_classical_result_mode_number(eigenmode_results):


    assert len(eigenmode_results.results) == NUM_OF_MODES_IN_SETUP

    prev_frequency = 0
    for mode_number, single_mode_result in eigenmode_results.results.items():
        assert(mode_number == single_mode_result.mode_number)
        assert(prev_frequency <= single_mode_result.frequency.value)
        assert(eigenmode_results.frequencies_unit.lower() == single_mode_result.frequency.unit.lower())
        prev_frequency = single_mode_result.frequency.value


def test_classical_result_flat_types(eigenmode_results):

    flat_result = eigenmode_results.flatten()

    for k, v in flat_result.items():
        assert(isinstance(k, str))
        assert(isinstance(v, (str, bool, float)))


def test_change_frequencies_unit(eigenmode_results):
    original_freq = eigenmode_results[1].frequency.value

    eigenmode_results.change_frequencies_unit("MHz")

    # Ensure unit is updated
    assert eigenmode_results.frequencies_unit.lower() == "mhz"
    assert eigenmode_results[1].frequency.unit.lower() == "mhz"
    assert eigenmode_results[1].frequency.value == pytest.approx(original_freq * 1000, rel=1e-3)


def test_generate_labeled_results(eigenmode_results):
    labeled = eigenmode_results.generate_a_labeled_version({
        1: "Mode X",
        2: "Mode Y",
        3: "Mode Z",
        4: "Mode A",
        5: "Mode B"
    })

    assert isinstance(labeled, type(eigenmode_results))
    assert labeled[0].label == "Mode X"
    assert labeled[4].label == "Mode B"
    assert labeled[0].mode_number == 0
    assert labeled[4].mode_number == 4


def test_generate_simple_form(eigenmode_results):
    simple_form = eigenmode_results.generate_simple_form()

    assert isinstance(simple_form, dict)
    assert list(simple_form.keys()) == list(eigenmode_results.results.keys())

    for k, v in simple_form.items():
        assert 'frequency' in v
        assert 'quality_factor' in v
        assert isinstance(v['frequency'], float)
        assert isinstance(v['quality_factor'], float)


def test_analyze_raises_on_invalid_hfss():
    sim = EigenmodeAnalysis(
        design_name="my_design",
        setup_name="Setup1"
    )

    with pytest.raises(ValueError, match="hfss given must be a Hfss instance"):
        sim.analyze(hfss="not_a_valid_instance")



def test_frequencies_sorted(eigenmode_results):
    freqs = [mode.frequency.value for mode in eigenmode_results.results.values()]
    assert freqs == sorted(freqs), "Frequencies are not sorted ascending."


def test_profile():

    d = {"profile": {
    "Setup1 - antenna_edge_gap='0.22500000000000001mm' chip_base_length='23.550000000000001mm' chip_base_thickness='381um' chip_base_width='2mm' chip_house_length='22mm' chip_house_radius='2mm' junction_inductance='10.800000000000001nH' junction_mesh_box_size_scale='20' junction_mesh_box_size_y='0.01mm' junction_width='0.001mm' pin_a_length='0mm' pin_a_location='8mm' pin_b_length='0mm' pin_b_location='11mm' pin_c_length='0mm' pin_c_location='15mm' pin_conductor_radius='0.25mm' pin_d_length='6.7000000000000002mm' pin_d_location='18mm' pin_waveguide_length='6.2999999999999998mm' pin_waveguide_radius='0.57499999999999996mm' purcell_e1_x='8.9399216337756769e-13um' purcell_e1_y='190.5um' purcell_e1_z='-11.624997999999998mm' purcell_e2_x='1.7267519867977679e-12um' purcell_e2_y='190.5um' purcell_e2_z='-18.424997999999999mm' purcell_readout_gap='2.25mm' purcell_size_x='1150um' purcell_size_y='1.31587340700526e-14um' purcell_size_z='6800um' readout_e1_x='0' readout_e1_y='190.5um' readout_e1_z='-2.0749979999999968mm' readout_e2_x='8.9399216337756769e-13um' readout_e2_y='190.5um' readout_e2_z='-9.3749979999999962mm' readout_size_x='1150um' readout_size_y='1.31587340700526e-14um' readout_size_z='7300um' spacer_length='0.10000000000000001mm' transmon_antenna_port_x='1.1634144591899854e-13um' transmon_antenna_port_y='190.5um' transmon_antenna_port_z='-0.42499799999999666mm' transmon_junction_left_arm_x='5.7987025939627168e-14um' transmon_junction_left_arm_y='190.5um' transmon_junction_left_arm_z='-0.90149799999999669mm' transmon_junction_right_arm_x='5.8354419979371386e-14um' transmon_junction_right_arm_y='190.5um' transmon_junction_right_arm_z='-0.89849799999999669mm' transmon_left_narrow_end_x='5.7558399559925595e-14um' transmon_left_narrow_end_y='190.5um' transmon_left_narrow_end_z='-0.90499799999999664mm' transmon_mesh_box_size_y='0.40000000000000002mm' transmon_orientation_port_x='0' transmon_orientation_port_y='190.5um' transmon_orientation_port_z='-1.3749979999999966mm' transmon_readout_gap='0.69999999999999996mm' transmon_right_narrow_end_x='5.8783046359072959e-14um' transmon_right_narrow_end_y='190.5um' transmon_right_narrow_end_z='-0.89499799999999663mm' transmon_size_x='1000.0000000000001um' transmon_size_y='0um' transmon_size_z='2599.998um' waveguide_mesh_box_size_y='0.59999999999999998mm'": {
      "profile": {
        "Props": {
          "Num. Solution Process": 1
        },
        "Children": {
          "Solution Process Group 1": {
            "Props": {
              "Start Time": "07/23/2025 11:54:59",
              "Host": "cn443.wexac.weizmann.ac.il",
              "Processor": 52,
              "OS": "Linux 5.14.0-427.42.1.el9_4.x86_64",
              "Product": "HFSS Version 2024.2.0",
              "Executing From": "/apps/easybd/programs/ANSYS/Electromagnetics/v242/Linux64/HFSSCOMENGINE.exe",
              "Allow off core": True,
              "Solution Basis Order": "Mixed",
              "Elapsed Time": "01:04:06",
              "ComEngine Memory": "128 M",
              "Stop Time": "07/23/2025 12:59:06",
              "Status": "Normal Completion",
              "Info": "Perform full validations with standard port validations"
            },
            "Children": {
              "HPC Group": {
                "Props": {
                  "Type": "Manual",
                  "Distribution Types": "Variations, Frequencies, Domain Solver, Transient Excitations, Mesh Assembly",
                  "MPI Vendor": "Intel",
                  "MPI Version": 2021
                },
                "Children": {
                  "Two Level": {
                    "Props": {
                      "Name": "Two Level",
                      "Info": "Disabled"
                    },
                    "Children": {}
                  },
                  "Machine": {
                    "Props": {
                      "Name": "cn443.wexac.weizmann.ac.il",
                      "Memory": "251 GB",
                      "RAM Limit": "90.000000%",
                      "Tasks": 1,
                      "Cores": 32,
                      "Free Disk Space": "161 GB"
                    },
                    "Children": {}
                  }
                }
              },
              "Design Validation": {
                "Props": {
                  "Name": "Design Validation",
                  "Info": "Elapsed time : 00:00:00 , HFSS ComEngine Memory : 124 M"
                },
                "Children": {}
              },
              "Initial Meshing Group": {
                "Props": {
                  "Time": "07/23/2025 11:54:59",
                  "Elapsed Time": "00:09:21"
                },
                "Children": {
                  "Stitch": {
                    "Props": {
                      "Name": "Stitch",
                      "Real time": "00:06:58",
                      "Cpu time": "00:06:57",
                      "Memory": "178 M",
                      "Triangles": 3923
                    },
                    "Children": {}
                  },
                  "Mesh": {
                    "Props": {
                      "Name": "Mesh",
                      "Real time": "00:00:14",
                      "Cpu time": "00:00:13",
                      "Memory": "199 M",
                      "Type": "Classic",
                      "Tetrahedra": 19281
                    },
                    "Children": {}
                  },
                  "Post": {
                    "Props": {
                      "Name": "Post",
                      "Real time": "00:00:03",
                      "Cpu time": "00:00:03",
                      "Memory": "230 M",
                      "Tetrahedra": 21377,
                      "Cores": 1
                    },
                    "Children": {}
                  },
                  "Manual Refine": {
                    "Props": {
                      "Name": "Manual Refine",
                      "Real time": "00:01:57",
                      "Cpu time": "00:01:58",
                      "Memory": "1.09 G",
                      "Tetrahedra": 790187,
                      "Cores": 1,
                      "Info": "chip_base_mesh, junction_mesh, junction_mesh_box, purcell_mesh, purcell_mesh_box, readout_mesh, readout_mesh_box, transmon_mesh, transmon_mesh_box, vacuum_mesh"
                    },
                    "Children": {}
                  },
                  "Lambda Refine": {
                    "Props": {
                      "Name": "Lambda Refine",
                      "Real time": "00:00:06",
                      "Cpu time": "00:00:07",
                      "Memory": "641 M",
                      "Tetrahedra": 790187,
                      "Cores": 1
                    },
                    "Children": {}
                  }
                }
              },
              "Adaptive Meshing Group": {
                "Props": {
                  "Time": "07/23/2025 12:04:20",
                  "Elapsed Time": "00:54:45",
                  "Info": "Adaptive Passes converged"
                },
                "Children": {
                  "Adaptive Pass 1 Group": {
                    "Props": {
                      "Info": "Eigenmode Solution"
                    },
                    "Children": {
                      "Simulation Setup": {
                        "Props": {
                          "Name": "Simulation Setup",
                          "Real time": "00:00:09",
                          "Cpu time": "00:00:09",
                          "Memory": "1.78 G",
                          "Disk": "335 KB"
                        },
                        "Children": {}
                      },
                      "Matrix Assembly": {
                        "Props": {
                          "Name": "Matrix Assembly",
                          "Real time": "00:00:13",
                          "Cpu time": "00:00:18",
                          "Memory": "2.25 G",
                          "Tetrahedra": 789878,
                          "Disk": "0 Bytes"
                        },
                        "Children": {}
                      },
                      "Matrix Solve": {
                        "Props": {
                          "Name": "Matrix Solve",
                          "Real time": "00:01:06",
                          "Cpu time": "00:26:44",
                          "Memory": "9.54 G",
                          "Type": "DCS",
                          "Cores": 32,
                          "Matrix size": 845393,
                          "Matrix bandwidth": 8,
                          "Eigen iterations": 54,
                          "Disk": "64.5 MB"
                        },
                        "Children": {}
                      },
                      "Field Recovery": {
                        "Props": {
                          "Name": "Field Recovery",
                          "Real time": "00:00:20",
                          "Cpu time": "00:03:32",
                          "Memory": "9.54 G",
                          "Computed eigenmodes": 5,
                          "Average order": 0,
                          "Disk": "892 MB"
                        },
                        "Children": {}
                      }
                    }
                  },
                  "Adaptive Pass 2 Group": {
                    "Props": {
                      "Max Delta Freq. %": 7.4075,
                      "Info": "Eigenmode Solution"
                    },
                    "Children": {
                      "Adaptive Refine": {
                        "Props": {
                          "Name": "Adaptive Refine",
                          "Real time": "00:00:42",
                          "Cpu time": "00:00:44",
                          "Memory": "949 M",
                          "Tetrahedra": 1027152,
                          "Cores": 1
                        },
                        "Children": {}
                      },
                      "Simulation Setup": {
                        "Props": {
                          "Name": "Simulation Setup",
                          "Real time": "00:00:12",
                          "Cpu time": "00:00:12",
                          "Memory": "2.24 G",
                          "Disk": "334 KB"
                        },
                        "Children": {}
                      },
                      "Matrix Assembly": {
                        "Props": {
                          "Name": "Matrix Assembly",
                          "Real time": "00:00:31",
                          "Cpu time": "00:00:36",
                          "Memory": "4.43 G",
                          "Tetrahedra": 1026227,
                          "Disk": "0 Bytes"
                        },
                        "Children": {}
                      },
                      "Matrix Solve": {
                        "Props": {
                          "Name": "Matrix Solve",
                          "Real time": "00:04:13",
                          "Cpu time": "01:42:41",
                          "Memory": "28.3 G",
                          "Type": "DCS",
                          "Cores": 32,
                          "Matrix size": 1932031,
                          "Matrix bandwidth": 14.8,
                          "Eigen iterations": 51,
                          "Disk": "82.9 MB"
                        },
                        "Children": {}
                      },
                      "Field Recovery": {
                        "Props": {
                          "Name": "Field Recovery",
                          "Real time": "00:00:29",
                          "Cpu time": "00:03:59",
                          "Memory": "28.3 G",
                          "Computed eigenmodes": 5,
                          "Average order": 0.228714,
                          "Disk": "641 MB"
                        },
                        "Children": {}
                      }
                    }
                  },
                  "Adaptive Pass 3 Group": {
                    "Props": {
                      "Max Delta Freq. %": 0.59104,
                      "Info": "Eigenmode Solution"
                    },
                    "Children": {
                      "Adaptive Refine": {
                        "Props": {
                          "Name": "Adaptive Refine",
                          "Real time": "00:00:33",
                          "Cpu time": "00:00:35",
                          "Memory": "963 M",
                          "Tetrahedra": 1174876,
                          "Cores": 1
                        },
                        "Children": {}
                      },
                      "Simulation Setup": {
                        "Props": {
                          "Name": "Simulation Setup",
                          "Real time": "00:00:13",
                          "Cpu time": "00:00:13",
                          "Memory": "2.56 G",
                          "Disk": "292 KB"
                        },
                        "Children": {}
                      },
                      "Matrix Assembly": {
                        "Props": {
                          "Name": "Matrix Assembly",
                          "Real time": "00:00:42",
                          "Cpu time": "00:00:47",
                          "Memory": "6.85 G",
                          "Tetrahedra": 1172873,
                          "Disk": "0 Bytes"
                        },
                        "Children": {}
                      },
                      "Matrix Solve": {
                        "Props": {
                          "Name": "Matrix Solve",
                          "Real time": "00:09:18",
                          "Cpu time": "03:57:48",
                          "Memory": "57.9 G",
                          "Type": "DCS",
                          "Cores": 32,
                          "Matrix size": 3139041,
                          "Matrix bandwidth": 17.7,
                          "Eigen iterations": 51,
                          "Disk": "92.1 MB"
                        },
                        "Children": {}
                      },
                      "Field Recovery": {
                        "Props": {
                          "Name": "Field Recovery",
                          "Real time": "00:00:38",
                          "Cpu time": "00:04:55",
                          "Memory": "57.9 G",
                          "Computed eigenmodes": 5,
                          "Average order": 0.404267,
                          "Disk": "523 MB"
                        },
                        "Children": {}
                      }
                    }
                  },
                  "Adaptive Pass 4 Group": {
                    "Props": {
                      "Max Delta Freq. %": 0.49732,
                      "Info": "Eigenmode Solution"
                    },
                    "Children": {
                      "Adaptive Refine": {
                        "Props": {
                          "Name": "Adaptive Refine",
                          "Real time": "00:00:29",
                          "Cpu time": "00:00:31",
                          "Memory": "1.02e+03 M",
                          "Tetrahedra": 1275376,
                          "Cores": 1
                        },
                        "Children": {}
                      },
                      "Simulation Setup": {
                        "Props": {
                          "Name": "Simulation Setup",
                          "Real time": "00:00:15",
                          "Cpu time": "00:00:14",
                          "Memory": "2.75 G",
                          "Disk": "295 KB"
                        },
                        "Children": {}
                      },
                      "Matrix Assembly": {
                        "Props": {
                          "Name": "Matrix Assembly",
                          "Real time": "00:00:51",
                          "Cpu time": "00:00:56",
                          "Memory": "8.74 G",
                          "Tetrahedra": 1272379,
                          "Disk": "0 Bytes"
                        },
                        "Children": {}
                      },
                      "Matrix Solve": {
                        "Props": {
                          "Name": "Matrix Solve",
                          "Real time": "00:13:32",
                          "Cpu time": "05:46:04",
                          "Memory": "81.1 G",
                          "Type": "DCS",
                          "Cores": 32,
                          "Matrix size": 4094164,
                          "Matrix bandwidth": 18.9,
                          "Eigen iterations": 51,
                          "Disk": "72.9 MB"
                        },
                        "Children": {}
                      },
                      "Field Recovery": {
                        "Props": {
                          "Name": "Field Recovery",
                          "Real time": "00:00:48",
                          "Cpu time": "00:06:12",
                          "Memory": "81.1 G",
                          "Computed eigenmodes": 5,
                          "Average order": 0.512537,
                          "Disk": "384 MB"
                        },
                        "Children": {}
                      }
                    }
                  },
                  "Adaptive Pass 5 Group": {
                    "Props": {
                      "Max Delta Freq. %": 0.10988,
                      "Info": "Eigenmode Solution"
                    },
                    "Children": {
                      "Adaptive Refine": {
                        "Props": {
                          "Name": "Adaptive Refine",
                          "Real time": "00:00:23",
                          "Cpu time": "00:00:26",
                          "Memory": "1.01e+03 M",
                          "Tetrahedra": 1325757,
                          "Cores": 1
                        },
                        "Children": {}
                      },
                      "Simulation Setup": {
                        "Props": {
                          "Name": "Simulation Setup",
                          "Real time": "00:00:15",
                          "Cpu time": "00:00:15",
                          "Memory": "2.85 G",
                          "Disk": "298 KB"
                        },
                        "Children": {}
                      },
                      "Matrix Assembly": {
                        "Props": {
                          "Name": "Matrix Assembly",
                          "Real time": "00:00:55",
                          "Cpu time": "00:00:59",
                          "Memory": "9.5 G",
                          "Tetrahedra": 1322549,
                          "Disk": "0 Bytes"
                        },
                        "Children": {}
                      },
                      "Matrix Solve": {
                        "Props": {
                          "Name": "Matrix Solve",
                          "Real time": "00:16:40",
                          "Cpu time": "06:55:22",
                          "Memory": "88.1 G",
                          "Type": "DCS",
                          "Cores": 32,
                          "Matrix size": 4478942,
                          "Matrix bandwidth": 19.2,
                          "Eigen iterations": 50,
                          "Disk": "29.4 MB"
                        },
                        "Children": {}
                      },
                      "Field Recovery": {
                        "Props": {
                          "Name": "Field Recovery",
                          "Real time": "00:00:46",
                          "Cpu time": "00:06:02",
                          "Memory": "88.1 G",
                          "Computed eigenmodes": 5,
                          "Average order": 0.542609,
                          "Disk": "171 MB"
                        },
                        "Children": {}
                      }
                    }
                  }
                }
              },
              "Simulation Summary Group": {
                "Props": {
                  "Max solved tets": 1322549,
                  "Max matrix size": 4478942,
                  "Matrix bandwidth": 19.2
                },
                "Children": {
                  "Design Validation": {
                    "Props": {
                      "Name": "Design Validation",
                      "Elapsed Time": "00:00:00",
                      "Total Memory": "124 MB"
                    },
                    "Children": {}
                  },
                  "Initial Meshing": {
                    "Props": {
                      "Name": "Initial Meshing",
                      "Elapsed Time": "00:09:21",
                      "Total Memory": "1.09 GB"
                    },
                    "Children": {}
                  },
                  "Adaptive Meshing": {
                    "Props": {
                      "Name": "Adaptive Meshing",
                      "Elapsed Time": "00:54:45",
                      "Total Memory": "265 GB",
                      "Total number of cores": 32
                    },
                    "Children": {}
                  }
                }
              }
            }
          }
        }
      }
    }
  }
    }
    from quansys.simulation.eigenmode.results import parse_profile
    value = parse_profile(d)
    print(value)





