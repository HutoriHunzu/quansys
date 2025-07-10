def run_job(config_path):

    from pyhfss.workflow import WorkflowConfig, execute_workflow

    config = WorkflowConfig.load_from_yaml(config_path)
    execute_workflow(config)
