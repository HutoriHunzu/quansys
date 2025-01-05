import h5py
import numpy as np
from datetime import datetime
from typing import Literal
from contextlib import contextmanager

import h5py
import numpy as np
from datetime import datetime


class HDF5Handler:
    def __init__(self, file_path, project_name: str):
        """
        Initialize the HDF5 handler.

        Parameters:
        - file_path (str): Path to the HDF5 file.
        """
        self.file_path = file_path
        iterations_path, metadata_path = self.prepare_project(project_name)
        self.iterations_path = iterations_path
        self.metadata_path = metadata_path

    def prepare_project(self, project_name):
        """
        Prepare the project structure with the current date.

        Parameters:
        - project_name (str): Name of the project.

        Returns:
        - str: The path to the initialized project group.
        """
        date = datetime.now().strftime('%Y-%m-%d')
        with h5py.File(self.file_path, 'a') as hdf5_file:
            project_group = hdf5_file.require_group(project_name)

            iteration_group = project_group.require_group('iterations')

            metadata_group = project_group.require_group('metadata')
            metadata_group.create_dataset('date', data=str(date))  # Explicitly handle string data

        return f"{project_name}/iterations", f"{project_name}/metadata"

    @staticmethod
    def _add_data_to_group(group, data: dict):
        """
        Save a dictionary of data to a specified HDF5 group.

        Parameters:
        - group (h5py.Group): HDF5 group to save the data to.
        - data (dict): Dictionary of data to save. Supported types: str, list, np.ndarray.
        """
        for key, value in data.items():
            if isinstance(value, str):  # Save strings directly
                group.create_dataset(key, data=value)
            elif isinstance(value, (list, np.ndarray)):  # Convert lists to numpy arrays
                value = np.array(value)
                group.create_dataset(key, data=value)
            elif isinstance(value, (int, float)):  # Save scalars as attributes
                group.attrs[key] = value
            else:
                raise ValueError(f"Unsupported data type for key '{key}': {type(value)}")

    @contextmanager
    def _get_group(self, name: Literal['iterations', 'metadata']):
        path_mapping = {'iterations': self.iterations_path,
                        'metadata': self.metadata_path}

        with h5py.File(self.file_path, 'a') as f:
            # head group
            yield f[path_mapping[name]]

    def create_new_iteration(self):

        with self._get_group('iterations') as group:
            # Determine the next incremental number
            iteration_num = len(group.keys())

            # Create the iteration group and returns it
            return group.require_group(str(iteration_num))

    def add_data(self, category: str, data: dict, add_to_last_iteration: bool = True):
        """
        Incrementally add data to the HDF5 file under a consecutive number.

        Parameters:
        - project_name (str): Project name.
        - category (str): Category of the data (e.g., 'classical', 'misc').
        - tag (dict): Metadata identifying this specific iteration.
        - data (dict): Data to save under the specified category.
        """

        if not add_to_last_iteration:
            self.create_new_iteration()

        with self._get_group('iterations') as group:
            # Determine the next incremental number
            iteration_num = len(group.keys())

            # Create the iteration group
            iteration_group = group[str(iteration_num - 1)]

            # inside the iteration group
            data_group = iteration_group.require_group(category)

            # adding data
            self._add_data_to_group(data_group, data)


# Open the HDF5 file and print its structure to validate
def print_hdf5_tree(name, obj):
    if isinstance(obj, h5py.Group):
        print(f"Group: {name}")
    elif isinstance(obj, h5py.Dataset):
        print(f"  Dataset: {name}, Data: {obj[()]}")


if __name__ == '__main__':
    # Initialize the handler
    handler = HDF5Handler('../../shared/example.h5', 'MyProject')

    # Add metadata
    # with handler.get_group('metadata') as metadata_group:
    #     handler.add_data_to_group(metadata_group, {'experiment': 'test_run', 'author': 'researcher'})

    # First iteration: Add classical analysis data
    handler.add_data(
        category='classical',
        data={'frequencies': np.array([1.0, 2.0, 3.0]), 'amplitudes': [0.1, 0.2, 0.3]},
        add_to_last_iteration=False,
    )

    # Second iteration: Add profiling data
    handler.add_data(
        category='profiling',
        data={'profile': 'Profile data string', 'runtime': '123 seconds'},
        add_to_last_iteration=True,
    )

    print("\nHDF5 File Structure and Data:")
    with h5py.File('example.h5', 'r') as f:
        f.visititems(print_hdf5_tree)
