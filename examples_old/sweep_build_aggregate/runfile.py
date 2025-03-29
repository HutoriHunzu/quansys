from pysubmit.workflow import WorkflowConfig, execute_flow

path = './config.yaml'

config = WorkflowConfig.load_from_yaml(path)

execute_flow(config)