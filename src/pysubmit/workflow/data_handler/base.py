from abc import ABC, abstractmethod

"""
the structure of the data handler:

# needs to be able to add solutions, each solution has a unique parameter set --> parameters (dict), data (dict)
# should keep track of the date --> date for each data point
# should be able to append to a known file as well as to clear it
# support tagging for sweep operations



def add_solution(parameters: dict, solution: dict):
    pass 
    
def add_tag(tag: dict):
    pass
    
def clear():
    pass
    
def parse():
    pass
    
def query():
    pass


# Hierarchy of saving stuff:

# top level:
#   project name
#       list of iterations

# iteration details (encapsulate a single build variation)
# list of solutions
# build_parameters: --> dict from build
# hfss variables: variation compound

# solution details (encapsulate a single solution):
# setup_type: str
# setup_parameters: dict
# data: dict
# raw_data: dict (optional)



"""




class BaseDataHandler(ABC):
    pass


class Example:

    def __init__(self, file_path, project_name: str):
        pass

    def clear(self):
        pass

    def parse(self):
        pass

    def query(self):
        pass

    def add_iteration(self):
        pass

    def add_solution(self, parameters: dict, data: dict):
        pass

    def add_metadata(self, tag):
        pass


if __name__ == '__main__':
    data_handler = Example()

    data_handler.clear()

    data_handler.add_iteration()

    pass
