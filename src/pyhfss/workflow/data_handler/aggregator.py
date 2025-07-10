from pathlib import Path
from typing import Any, Generator
from pydantic import TypeAdapter

from .metadata import Metadata
from .utils import flat_data_from_json
from .json_utils import json_read


class Aggregator:
    """
    Aggregator processes and merges simulation outputs across multiple iterations.

    This class is responsible for scanning a directory containing iteration subdirectories,
    each with a 'metadata.json' file describing simulation outputs. Based on a configured
    mapping of *aggregation keys* to lists of output identifiers, the aggregator merges
    the relevant simulation outputs into flattened dictionaries and groups them by
    those aggregation keys.

    Attributes:
        grouping_config (dict[str, list[str]]):
            A mapping where each key corresponds to an aggregation group,
            and its value is a list of output identifiers to merge.
        scanning_dir (Path):
            The base directory to scan for iteration subfolders (each containing 'metadata.json').
        adapter (TypeAdapter | None):
            An optional Pydantic TypeAdapter used to parse and validate data
            before flattening. If None, data is taken as-is.
    """

    def __init__(
        self,
        grouping_config: dict[str, list[str]],
        scanning_dir: Path,
        adapter: TypeAdapter | None = None
    ) -> None:
        self.grouping_config = grouping_config
        self.scanning_dir = scanning_dir
        self.adapter = adapter

    def aggregate(self) -> dict[str, list[dict[str, Any]]]:
        """
        Aggregate the simulation outputs for each iteration in `scanning_dir`
        according to `grouping_config`.

        For every iteration folder (determined by presence of 'metadata.json'),
        this method:
          1. Loads the metadata.
          2. For each aggregation group in `grouping_config`:
             - Collects and merges the specified identifiers' JSON outputs.
             - Appends the merged dictionary (if successful) to the result list.

        Returns:
            dict[str, list[dict[str, Any]]]:
                A dictionary keyed by each aggregation group. The value for each group
                is a list of merged/flattened dictionaries containing the simulation
                data plus an "iteration_number" field.
        """
        aggregated: dict[str, list[dict[str, Any]]] = {
            key: [] for key in self.grouping_config
        }

        # Go through each iteration’s metadata file
        for meta in self._iter_metadata_files():
            for agg_key, id_list in self.grouping_config.items():
                merged_data = self._merge_by_metadata(meta, id_list)
                if merged_data is not None:
                    # Tag the iteration number
                    merged_data["iteration_number"] = meta.iteration_number
                    aggregated[agg_key].append(merged_data)

        return aggregated

    def summarize_metadata(self) -> list[Metadata]:
        """
        Gather all Metadata objects from `scanning_dir`.

        Returns:
            list[Metadata]:
                A list of Metadata objects, sorted by iteration_number.
        """
        return list(self._iter_metadata_files())

    def _iter_metadata_files(self) -> Generator[Metadata, None, None]:
        """
        Iterate over all 'metadata.json' files under `scanning_dir`, sorted by iteration_number.

        Yields:
            Metadata: Metadata for each iteration.
        """
        # First, find all 'metadata.json' files and sort them by iteration_number
        meta_files = sorted(
            self.scanning_dir.rglob("metadata.json"),
            key=lambda p: Metadata.load(p).iteration_number
        )

        for meta_file in meta_files:
            yield Metadata.load(meta_file)

    def _merge_by_metadata(
        self, metadata: Metadata, identifiers: list[str]
    ) -> dict[str, Any] | None:
        """
        Merge simulation outputs for the given identifiers in a single iteration.

        For each identifier in `identifiers`:
          - Check if the metadata has that identifier registered.
          - Load the corresponding JSON file.
          - Optionally parse it through `adapter`.
          - Flatten the resulting data and merge into a single dictionary.

        If any identifier is not found or its file does not exist, returns None.

        Args:
            metadata (Metadata): The iteration's metadata object.
            identifiers (list[str]): List of output identifiers to merge.

        Returns:
            dict[str, Any] | None:
                The merged dictionary of flattened data, or None if not all
                identifiers can be merged.
        """
        # Ensure the iteration includes all requested identifiers
        existing_ids = set(metadata.id_to_description.keys())
        required_ids = set(identifiers)
        if not required_ids.issubset(existing_ids):
            return None

        merged: dict[str, Any] = {}
        for ident in identifiers:
            output_path = metadata.get_output_path(ident)
            if not output_path.exists():
                return None

            data = json_read(output_path)
            flattened = flat_data_from_json(data, adapter=self.adapter)
            merged.update(flattened)

        return merged
