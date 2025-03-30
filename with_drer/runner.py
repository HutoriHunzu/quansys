# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "pysubmit @ git+https://github.com/RosenblumLab/pysubmit.git",
# ]
# ///


from pysubmit import WorkflowConfig, execute_flow

path = './config.yaml'

config = WorkflowConfig.load_from_yaml(path)

execute_flow(config)