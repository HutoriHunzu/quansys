"""
In this chapter we are going to cover the usage of the simulation
subpackage:

1. executing an Eigen Mode simulation on a given aedt file
2. saving the data
3. changing simulation parameters
4. loading simulation from disk
5. note about different simulation options

"""

from pysubmit.simulation import EignmodeAnalysis

"""
All the simulations are imported using pysubmit.simulation and all share the same concept:

1. has both 'id' and 'type' attributes which store the name of the simulation and its type as strings
2. has two methods: 'analyze' and 'report', each returns a result object that can be saved.

"""

"""
lets start by taking a already made simple design and simulate it
"""

from pyaedt.hfss import Hfss

# opening the file using pyaedt
with Hfss(project='simple_design_readout.aedt', design='my_design', remove_lock=True,
          close_on_exit=True) as hfss:
    # setting up the simulation:
    # one must pass the name of the setup and the name of the design
    # to be simulated.
    simulation = EignmodeAnalysis(setup_name='Setup1', design_name='my_design')

    # calling analyze with hfss instance
    result = simulation.analyze(hfss)

    """
    now we can proceed and use the results object or save it to the disk
    """

    # the result object is both printable and serializable:
    print(result)

    # accessing the first mode:
    print(f'{result.results[1].frequency=}')
    print(f'{result.results[1].quality_factor=}')

    # and lastly you can save it to json by first serializing it:
    result_as_string_for_json = result.model_dump_json(indent=4)
    print(result_as_string_for_json)

    # and then save it like a text file (no need for JSON package):
    with open('my_results.json', 'w') as f:
        f.write(result_as_string_for_json)

    """
    next, we would like to maybe change the number of passes or any other parameter.
    the simulation object can get 'setup_parameters' we are directly passes to the setup pyaedt object.
    one can look for all the options here (look for the correct simulation type):
    https://aedt.docs.pyansys.com/version/stable/API/SetupTemplates.html
    """

    # let's change some parameters:
    setup_parameters = {
        'MaximumPasses': 4,
        'MinimumConvergedPasses': 1,
        'MinimumPasses': 1,
        'MinimumFrequency': '2GHz',
        'NumModes': 3,
        'MaxDeltaFreq': 0.2,
        'ConvergeOnRealFreq': True,
        'PercentRefinement': 30,
        'BasisOrder': -1,
        'DoLambdaRefine': True,
        'DoMaterialLambda': True,
        'SetLambdaTarget': False,
        'Target': 0.4,
        'UseMaxTetIncrease': False,
    }

    simulation.setup_parameters = setup_parameters
    # and now re-running it will change the parameters of the setup and execute it.

    """
    next we'll cover another option for the simulation usage, which is to define it as json and load
    it:
    """

    # so any simulation object can itself be serialized to the file and loaded:
    simulation_as_string = simulation.model_dump_json(indent=4)
    print(simulation_as_string)

    # and then save it like a text file (no need for JSON package):
    with open('my_simulation.json', 'w') as f:
        f.write(simulation_as_string)

    # and then it can be loaded:
    with open('my_simulation.json', 'r') as f:
        data = f.read()

    simulation_loaded = EignmodeAnalysis.model_validate_json(data)
    print(simulation_loaded)

    """
    lastly i want to cover also quantum epr simulation type. the usage is almost identical the only
    different is that you'll need to pass a bit different arguments:
    1. junction_configuration 
    2. modes_to_labels 
    """
    from pysubmit.simulation import QuantumEpr

    # starting with junction configuration, this is simply put a the name of the junction and the name of the
    # inductance variable:

    from pysubmit.simulation.quantum_epr import ConfigJunction

    junction_config = ConfigJunction(name='my_junction_name', inductance_variable_name='Lj')

    # of course one can pass either a single junction configuration or a list of them.

    # going next to modes_to_labels: on the very basic level it can be a dict of integer to string:

    modes_to_labels = {1: 'my_transmon_mode',
                       3: 'my_readout_mode',
                       4: 'my_purcell_mode'}

    # however, modes to labels also support more complex behavior that it is based on the current results.
    # a use case for that: let's say you want to assign the two lowest quality factor modes to readout and purcell.

    # in order to use the complex strucutre one needs to import ModesAndLabels
    # and the types of complex behavior you want, currently there are only ManualInference and OrderInference
    # from quantum_epr module.

    from pysubmit.simulation.quantum_epr import ModesAndLabels, ManualInference, OrderInference

    # and now we only need to create an instance of ModesAndLabels. this object contains a list
    # of inferences object, each has a single method called '.infer' which gets as an input the results
    # from eigenmode and compute the desired labels. lets do some examples:

    eigenmode_results = {1: {'frequency': 2, 'quality_factor': 50000},
                         2: {'frequency': 3.5, 'quality_factor': 2000},
                         3: {'frequency': 4.5, 'quality_factor': 3000},
                         4: {'frequency': 5.5, 'quality_factor': 6000},
                         5: {'frequency': 6.5, 'quality_factor': 300},
                         6: {'frequency': 7.5, 'quality_factor': 500}}


    # we start with manual inference, this is essentailly like the given dict of mode
    # number to label, as we saw before.
    # the main difference here is that it allows for the passing of the eigenmode result (doesn't use it
    # as it is manual) but this can be executing with other types of inferences that do use the result
    manual_inference = ManualInference(mode_number=3, label='uri')
    manual_inference_result = manual_inference.infer(eigenmode_results=eigenmode_results)

    # here we just expect the result to be: {3: 'uri'}
    print(f'{manual_inference_result=}')


    # here we demonstrate an ordered inference, this corresponds to the use case mentioned above. lets say
    # we want to get the two lowest quality factors modes assigned as readout and pucell where the readout has lower
    # frequency then the pucell:
    order_inference = OrderInference(num=2, min_or_max='min', ordered_labels_by_frequency=['readout', 'purcell'],
                                     quantity='quality_factor')
    order_inference_result = order_inference.infer(eigenmode_results=eigenmode_results)

    # now we expect {5: 'readout', 6: 'purcell'}
    print(f'{order_inference_result=}')

    # after understaing the inferences we can just construct a modes to labels object:
    complex_modes_to_labels = ModesAndLabels(inferences=[manual_inference, order_inference])


    # now we can put everything togather;
    quantum_sim = QuantumEpr(setup_name='Setup1', design_name='my_design',
                             modes_to_labels=complex_modes_to_labels,
                             junctions_infos=junction_config)

    # in the current demo file there is no junction so it won't work but the usage is the same
    # as before, result = qunautm_sim.analyze(hfss)