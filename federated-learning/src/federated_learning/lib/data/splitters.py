import logging
import math
from random import Random
from abc import ABCMeta, abstractmethod
from collections import Counter, defaultdict
from typing import Dict, List, Union, Tuple
import numpy as np
from numpy.random import RandomState

import pandas as pd
from rdkit import Chem
from tqdm import tqdm

from federated_learning.lib.core.exceptions import SplitError
from federated_learning.lib.data.loaders import AbstractLoader


class AbstractSplitter(metaclass=ABCMeta):
    """Splitters take a loader as input and return lists of entry IDs"""

    def __init__(self, splits: Dict[str, float]):
        self.splits = splits

        if round(sum(self.splits.values()), 2) != 1:
            SplitError("Split ratios do not add up to 1!")

    @abstractmethod
    def apply(self, data_loader: AbstractLoader) -> Dict[str, List[Union[int, str]]]:
        raise NotImplementedError


class IndexSplitter(AbstractSplitter):
    """Split the dataset based on their order"""

    def apply(self, data_loader: AbstractLoader) -> Dict[str, List[Union[int, str]]]:
        splits = {}

        ids = data_loader.list_ids()
        dataset_size = len(ids)

        start_index = 0
        total_ratio = 0
        for split_name, split_ratio in self.splits.items():
            total_ratio = round(total_ratio + split_ratio, 4)
            end_index = math.floor(dataset_size * total_ratio)

            splits[split_name] = ids[start_index:end_index]
            start_index = end_index

        return splits


class RandomSplitter(AbstractSplitter):
    """Random split of the data

    Split the dataset randomly with no consideration for fields
    """

    def __init__(self, splits: Dict[str, float], seed: int,*args,**kwargs):
        super().__init__(splits=splits)
        self.random = Random(seed)

    def apply(self, data_loader: AbstractLoader) -> Dict[str, List[Union[int, str]]]:
        splits = {}
        ids = set(data_loader.list_ids())

        ratio_left = 1
        for split_name, split_ratio in self.splits.items():
            sample_size = int(split_ratio / ratio_left * len(ids))
            splits[split_name] = self.random.sample(population=ids, k=sample_size)

            ids = ids.difference(set(splits[split_name]))
            ratio_left -= split_ratio

        return splits


class CategoricalSplitter(RandomSplitter):
    """To comment

    Split the dataset randomly
    """

    def __init__(self, cat_name, splits: Dict[str, float], seed: int, test_split, id_fold_mila=None, client_distribution=None):
        super().__init__(splits=splits, seed=seed)
        self.seed = seed
        self._cat_name = cat_name
        self.id_fold_mila = id_fold_mila
        self.test_split = test_split
        if id_fold_mila is not None:
            self.client_splits = {}
            for i in range(len(client_distribution)):
                self.client_splits.update({
                    f"client_{i}": client_distribution[i]
                })
    def _load_inputs(self, data_loader: AbstractLoader) -> Dict[Union[int, str], float]:
        return {
            entry.id_: entry.inputs[self._cat_name] for entry in iter(data_loader)
        }

    def apply(self, data_loader: AbstractLoader) -> Dict[str, List[Union[int, str]]]:
        leftover_data = self._load_inputs(data_loader)
        _ids = np.array(list(leftover_data.keys()))
        cat_data = np.array(list(leftover_data.values()))
        cat_names = np.unique(cat_data)

        if self.id_fold_mila is not None:
            # Compute random split
            splits = super().apply(data_loader)
            # Keep only test fold split
            splits = {f"fold_{self.id_fold_mila}": splits[f"fold_{self.id_fold_mila}"]}
            splits.update({k: [] for k in self.client_splits.keys()})
            remaining_split = self.client_splits
            # Remove already used ids
            mask = np.invert(np.isin(_ids, splits[f"fold_{self.id_fold_mila}"]))
            cat_data = cat_data[mask]
            _ids = _ids[mask]
            ratio_left = 1
        # Only used for multi step training
        else:
            # Compute random split
            splits = super().apply(data_loader)
            # Keep only test fold split
            splits = {k: splits[self.test_split] if k==self.test_split else [] for k in self.splits.keys()}
            remaining_split = self.splits.copy()
            # Remove already used ids
            mask = np.invert(np.isin(_ids, splits[self.test_split]))
            cat_data = cat_data[mask]
            _ids = _ids[mask]
            ratio_left = 1 - remaining_split.pop(self.test_split)
            self.random.seed(self.seed)

        for split_name, split_ratio in remaining_split.items():
            sample_size = int(split_ratio / ratio_left * len(cat_data[np.isin(cat_data, cat_names)]))
            while len(splits[split_name]) < sample_size:
                chosen_cat = self.random.sample(population=list(cat_names), k=1)[0]
                splits[split_name] += _ids[cat_data == chosen_cat].tolist()
                cat_names = cat_names[cat_names != chosen_cat]
            ratio_left -= split_ratio

        [data.inputs.pop(self._cat_name) for data in data_loader._dataset]

        return splits


class StratifiedSplitter(AbstractSplitter):
    """Stratified splitting of the dataset

    This splitting preserves the proportion of samples based on a certain target/label.
    If the target is continuous, we can split it into a number of bins.
    """

    def __init__(
        self,
        splits: Dict[str, float],
        seed: int,
        target_name: str,
        bins_count: int = 0,
        is_target_input: bool = False,
        rewrite: bool = False,
        *args,
        **kwargs
    ):
        super().__init__(splits=splits)

        self._seed = seed
        self._target_name = target_name
        self._bins_count = bins_count
        self._is_target_input = is_target_input
        self.rewrite = rewrite

    def _load_outputs(
        self, data_loader: AbstractLoader
    ) -> Dict[Union[int, str], float]:
        output_index = data_loader.get_labels().index(self._target_name)
        results = {}

        for entry in iter(data_loader):
            results[entry.id_] = entry.outputs[output_index]

        return results

    def _load_inputs(self, data_loader: AbstractLoader) -> Dict[Union[int, str], float]:
        return {
            entry.id_: entry.inputs[self._target_name] for entry in iter(data_loader)
        }

    def _binify(self, data: Dict[Union[int, str], float]) -> Dict[Union[int, str], int]:
        entries = list(data.values())
        bins = pd.qcut(
            entries, self._bins_count, labels=False, duplicates="drop"
        ).tolist()

        return dict(zip(list(data.keys()), bins))

    def apply(self, data_loader: AbstractLoader) -> Dict[str, List[Union[int, str]]]:
        from sklearn.model_selection import train_test_split

        leftover_data = (
            self._load_inputs(data_loader)
            if self._is_target_input
            else self._load_outputs(data_loader)
        )
        if self._bins_count > 0:
            leftover_data = self._binify(leftover_data)

        splits = {}
        ratio_left = 1

        for split_name, split_ratio in self.splits.items():
            current_ratio = round(split_ratio / ratio_left, 4)

            if current_ratio < 1:
                current_split_ids, leftover_ids = train_test_split(
                    list(leftover_data.keys()),
                    train_size=current_ratio,
                    random_state=RandomState(self._seed),
                    stratify=list(leftover_data.values()),
                )
            else:
                current_split_ids = list(leftover_data.keys())
                leftover_ids = []

            splits[split_name] = current_split_ids
            leftover_data = {id_: leftover_data[id_] for id_ in leftover_ids}

            ratio_left -= split_ratio

        if self.rewrite:
            [data.inputs.pop(self._target_name) for data in data_loader._dataset]

        return splits


class ScaffoldBalancerSplitter(AbstractSplitter):
    def __init__(self, splits: Dict[str, float], seed: int, *args, **kwargs):
        super().__init__(splits=splits)
        self._seed = seed

    def _load_groups(self, data_loader: AbstractLoader) -> Dict[Union[int, str], str]:
        from rdkit.Chem.Scaffolds.MurckoScaffold import MurckoScaffoldSmiles

        logging.info("[SPLITTER] Extracting Scaffolds...")
        return {
            entry.id_: MurckoScaffoldSmiles(entry.inputs["smiles"])
            for entry in tqdm(data_loader)
        }

    def apply(self, data_loader: AbstractLoader) -> Dict[str, List[Union[int, str]]]:
        from sklearn.model_selection import train_test_split

        leftover_data = self._load_groups(data_loader)
        splits = {}
        ratio_left = 1

        for split_name, split_ratio in self.splits.items():
            current_ratio = round(split_ratio / ratio_left, 4)

            if current_ratio < 1:
                counts = Counter(leftover_data.values())
                lone_scaffolds = [
                    scaffold
                    for scaffold, occurrences in counts.items()
                    if occurrences == 1
                ]

                additional_ids = [
                    id_
                    for id_, scaffold in leftover_data.items()
                    if scaffold in lone_scaffolds
                ]

                leftover_ratio = len(leftover_data) * (1 - current_ratio)
                remaining_samples = len(leftover_data) - len(additional_ids)
                adjusted_ratio = 1 - leftover_ratio / remaining_samples

                leftover_data = {
                    id_: leftover_data[id_]
                    for id_ in set(leftover_data) - set(additional_ids)
                }
                current_split_ids, leftover_ids = train_test_split(
                    list(leftover_data.keys()),
                    train_size=adjusted_ratio,
                    random_state=RandomState(self._seed),
                    stratify=list(leftover_data.values()),
                )

                current_split_ids.extend(additional_ids)
            else:
                current_split_ids = list(leftover_data.keys())
                leftover_ids = []

            splits[split_name] = current_split_ids
            leftover_data = {id_: leftover_data[id_] for id_ in leftover_ids}

            ratio_left -= split_ratio

        total_samples_count = len(data_loader)
        logging.info(
            "[SPLITTER] Final Ratios: {}".format(
                [len(split) / total_samples_count for split in splits.values()]
            )
        )

        return splits


class ScaffoldDividerSplitter(AbstractSplitter):
    def __init__(self, splits: Dict[str, float], seed: int, *args, **kwargs):
        super().__init__(splits=splits)
        self._seed = seed

    def _load_groups(
        self, data_loader: AbstractLoader
    ) -> Dict[str, List[Union[int, str]]]:
        from rdkit.Chem.Scaffolds.MurckoScaffold import MurckoScaffoldSmiles

        logging.info("[SPLITTER] Extracting Scaffolds...")
        sorted_scaffolds = defaultdict(list)

        for entry in tqdm(data_loader):
            scaffold = MurckoScaffoldSmiles(entry.inputs["smiles"])
            sorted_scaffolds[scaffold].append(entry.id_)

        return sorted_scaffolds

    def apply(self, data_loader: AbstractLoader) -> Dict[str, List[Union[int, str]]]:
        leftover_data = self._load_groups(data_loader)
        mixer = Random(self._seed)

        splits = {}
        ratio_left = 1

        for split_name, split_ratio in self.splits.items():
            current_ratio = round(split_ratio / ratio_left, 4)

            if current_ratio < 1:
                scaffolds = list(leftover_data.keys())
                mixer.shuffle(scaffolds)

                current_split_ids = []
                required_entries = int(len(data_loader) * split_ratio)

                for scaffold in scaffolds:
                    if (
                        len(current_split_ids) + len(leftover_data[scaffold])
                        <= required_entries
                    ):
                        current_split_ids.extend(leftover_data[scaffold])
                        leftover_data.pop(scaffold)
            else:
                current_split_ids = []
                for ids in leftover_data.values():
                    current_split_ids.extend(ids)

            splits[split_name] = current_split_ids
            ratio_left -= split_ratio

        total_samples_count = len(data_loader)
        logging.info(
            "[SPLITTER] Final Ratios: {}".format(
                [len(split) / total_samples_count for split in splits.values()]
            )
        )

        return splits


class ButinaClusterer:
    def __init__(
        self, butina_cutoff: float = 0.5, fingerprint_size: int = 1024, radius: int = 2, *args, **kwargs
    ):
        self._butina_cutoff = butina_cutoff
        self._fingerprint_size = fingerprint_size
        self._radius = radius

    def _generate_clusters(
        self, data_loader: AbstractLoader
    ) -> Tuple[List[Union[str, int]], Tuple[Tuple[int, ...]]]:

        from rdkit import DataStructs
        from rdkit.Chem import AllChem
        from rdkit.ML.Cluster import Butina

        logging.info("[SPLITTER] Generating fingerprints...")

        ids = []
        fingerprints = []
        for entry in tqdm(data_loader):
            ids.append(entry.id_)
            fingerprints.append(
                AllChem.GetMorganFingerprintAsBitVect(
                    Chem.MolFromSmiles(entry.inputs["smiles"]),
                    self._radius,
                    self._fingerprint_size,
                )
            )

        samples_count = len(fingerprints)
        logging.info("[SPLITTER] Computing Similarities...")

        similarities = []
        for i in range(1, samples_count):
            similarity = DataStructs.BulkTanimotoSimilarity(
                fingerprints[i], fingerprints[:i]
            )
            similarities.extend([1 - j for j in similarity])

        logging.info("[SPLITTER] Clustering...")
        clusters = Butina.ClusterData(
            similarities, samples_count, self._butina_cutoff, isDistData=True
        )

        return ids, clusters


class ButinaBalancerSplitter(ScaffoldBalancerSplitter, ButinaClusterer):
    def __init__(
        self,
        splits: Dict[str, float],
        seed: int,
        butina_cutoff: float = 0.5,
        fingerprint_size: int = 1024,
        radius: int = 2,
        *args, **kwargs
    ):
        ScaffoldBalancerSplitter.__init__(self, splits=splits, seed=seed)
        ButinaClusterer.__init__(
            self,
            butina_cutoff=butina_cutoff,
            fingerprint_size=fingerprint_size,
            radius=radius,
        )

    def _load_groups(self, data_loader: AbstractLoader) -> Dict[Union[int, str], float]:
        ids, clusters = self._generate_clusters(data_loader=data_loader)

        groups = {}
        for cluster_id, sample_ids in enumerate(clusters):
            for sample_id in sample_ids:
                groups[ids[sample_id]] = cluster_id

        return groups


class ButinaDividerSplitter(ScaffoldDividerSplitter, ButinaClusterer):
    def __init__(
        self,
        splits: Dict[str, float],
        seed: int,
        butina_cutoff: float = 0.5,
        fingerprint_size: int = 1024,
        radius: int = 2,
        *args, **kwargs
    ):
        ScaffoldDividerSplitter.__init__(self, splits=splits, seed=seed)
        ButinaClusterer.__init__(
            self,
            butina_cutoff=butina_cutoff,
            fingerprint_size=fingerprint_size,
            radius=radius,
        )

    def _load_groups(
        self, data_loader: AbstractLoader
    ) -> Dict[int, List[Union[int, str]]]:
        ids, clusters = self._generate_clusters(data_loader=data_loader)

        groups = {}
        for cluster_id, sample_ids in enumerate(clusters):
            groups[cluster_id] = [ids[sample_id] for sample_id in sample_ids]

        return groups


class DescriptorSplitter(StratifiedSplitter):
    def __init__(
        self, splits: Dict[str, float], seed: int, descriptor: str, bins_count: int = 10, *args, **kwargs
    ):
        super().__init__(
            splits=splits,
            seed=seed,
            bins_count=bins_count,
            target_name="smiles",
            is_target_input=True,
        )

        from rdkit.ML.Descriptors.MoleculeDescriptors import (
            MolecularDescriptorCalculator,
        )

        self._descriptor_calculator = MolecularDescriptorCalculator([descriptor])

        self._descriptor = descriptor
        self._validate()

    def _validate(self):
        if (
            self._descriptor_calculator.CalcDescriptors(Chem.MolFromSmiles("c1ccccc1"))[
                0
            ]
            == 777
        ):
            raise AttributeError(
                "Unknown descriptor requested: {}".format(self._descriptor)
            )

    def _load_inputs(self, data_loader: AbstractLoader) -> Dict[Union[int, str], float]:
        entries = {}
        for entry in data_loader:
            entries[entry.id_] = self._descriptor_calculator.CalcDescriptors(
                Chem.MolFromSmiles(entry.inputs[self._target_name])
            )[0]

        return entries
