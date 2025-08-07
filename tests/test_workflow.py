from quansys.workflow import WorkflowConfig, PyaedtFileParameters, DesignVariableBuilder, execute_workflow
from quansys.simulation import EigenmodeAnalysis
from pycaddy.sweeper import DictSweep

from pandas import read_csv

from pathlib import Path

SIMPLE_DESIGN_AEDT = Path(__file__).parent / "resources" / "simple_design.aedt"


def test_workflow(tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp("testing_workflow")

    config_full = WorkflowConfig(

        pyaedt_file_parameters=PyaedtFileParameters(file_path=SIMPLE_DESIGN_AEDT, non_graphical=False),
        simulations={'classical': EigenmodeAnalysis(setup_name='Setup1', design_name='my_design')},

        # A list of sweeps. We'll do a ZipSweep for chip_base_length
        builder_sweep=[DictSweep(parameters={'chip_base_width': ['3mm', '3.5mm']})],

        # The builder to apply to each sweep iteration
        builder=DesignVariableBuilder(design_name='my_design'),

        aggregation_dict={'classical_agg': ['classical']},
        root_folder=tmp_path
    )

    execute_workflow(config_full)

    summary_file = Path(config_full.root_folder) / 'aggregations' / 'classical_agg.csv'
    df = read_csv(summary_file)

    assert df.shape[0] == 2
    assert df.loc[0]['uid'] == 0
    assert df.loc[1]['uid'] == 1
    assert df.loc[0]['Mode (1) Freq. (ghz)'] >= df.loc[1]['Mode (1) Freq. (ghz)']



def test_workflow_config():
    config_full = WorkflowConfig(

        pyaedt_file_parameters=PyaedtFileParameters(file_path=SIMPLE_DESIGN_AEDT),
        simulations={'classical': EigenmodeAnalysis(setup_name='Setup1', design_name='my_design')},

        # A list of sweeps. We'll do a ZipSweep for chip_base_length
        builder_sweep=[DictSweep(parameters={'chip_base_width': ['3mm', '4mm']})],

        # The builder to apply to each sweep iteration
        builder=DesignVariableBuilder(design_name='my_design'),

        aggregation_dict={'classical_agg': ['classical']}
    )

    config_full.save_to_yaml('config.yaml')

