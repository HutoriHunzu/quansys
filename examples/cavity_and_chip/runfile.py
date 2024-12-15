from src.pysubmit.simulation.config_handler.config import load
from src.pysubmit.simulation.analyze import main

path = './builder_config.yaml'

config = load(path)

main(config)

# main(config)


"""
mode_to_freq_and_q_factor = {
    1: {'freq': 3.5, 'q_factor': 100},
    2: {'freq': 5.1, 'q_factor': 130},
    3: {'freq': 5.8, 'q_factor': 90},
    4: {'freq': 6.0, 'q_factor': 120}
}

for mode_and_labels in config.modes_and_labels:
    result = mode_and_labels.parse(mode_to_freq_and_q_factor)
    print(result)

print(1)
"""