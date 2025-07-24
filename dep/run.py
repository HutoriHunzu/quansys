def run_job(config_path):
    # Use cached imports for better performance on repeated calls
    from .cache import cached_import
    
    WorkflowConfig = cached_import('quansys.workflow', attr_name='WorkflowConfig')
    execute_workflow = cached_import('quansys.workflow', attr_name='execute_workflow')

    config = WorkflowConfig.load_from_yaml(config_path)
    execute_workflow(config)
