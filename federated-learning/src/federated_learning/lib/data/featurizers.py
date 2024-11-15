import itertools
import logging
from abc import ABCMeta, abstractmethod
from functools import partial
from typing import Any, List, Tuple, Callable, Optional, Union

import numpy as np
import torch
from rdkit import Chem
from torch_geometric.data import Data as TorchGeometricData

from federated_learning.lib.core.exceptions import FeaturizationError
from federated_learning.lib.data.resources import DataPoint


class AbstractFeaturizer(metaclass=ABCMeta):
    def __init__(
        self,
        inputs: List[str],
        outputs: List[str],
        should_cache: bool = False,
        rewrite: bool = True,
    ):
        self._inputs = inputs
        self._outputs = outputs

        self._should_cache = should_cache
        self._rewrite = rewrite

        self.__cache = {}

    @abstractmethod
    def _process(self, data: Any) -> Any:
        raise NotImplementedError

    def __process(self, data: Any) -> Any:
        if self._should_cache:
            if data not in self.__cache:
                self.__cache[data] = self._process(data)

            return self.__cache[data]
        else:
            return self._process(data)

    def run(self, data: DataPoint) -> None:
        if len(self._inputs) != len(self._outputs):
            raise FeaturizationError("Inputs and mappings must have the same length.")

        for index in range(len(self._inputs)):
            raw_data = data.inputs[self._inputs[index]]
            if self._rewrite:
                data.inputs.pop(self._inputs[index])

            data.inputs[self._outputs[index]] = self.__process(raw_data)


class TensorFeaturizer(AbstractFeaturizer):
    """Featurizer for independant linear data

    Featurizers for linear tabular type data. It return a torch type floating vector out of 1d data.
    """

    def __init__(
        self,
        inputs: List[str],
        outputs: List[str],
        should_cache: bool = False,
        rewrite: bool = True,
    ):
        super().__init__(inputs, outputs, should_cache, rewrite)

    def _process(self, data) -> torch.FloatTensor:
        return torch.FloatTensor(data)

class TensorTabularFeaturizer(TensorFeaturizer):
    """Tabular featurizer from a list of inputs.

    Takes a list of inputs and generate one vector from them
    """
    def __init__(
        self,
        inputs: List[str],
        outputs: str,
        should_cache: bool = False,
    ):
        self.group_inputs = inputs
        super().__init__(['tabular_tmp'], outputs, should_cache, rewrite=True)

    def run(self, data: DataPoint) -> None:
        raw_data = []
        for index in range(len(self.group_inputs)):
            raw_data.append(data.inputs[self.group_inputs[index]])
            if self._rewrite:
                data.inputs.pop(self.group_inputs[index])

        data.inputs['tabular_tmp'] = raw_data
        super().run(data)


class AbstractTorchGeometricFeaturizer(AbstractFeaturizer):
    """
    Featurizers preparing data for torch geometric should extend this class
    """

    def _process(self, data: str) -> TorchGeometricData:
        mol = Chem.MolFromSmiles(data)
        if mol is None:
            raise FeaturizationError("Could not featurize entry: [{}]".format(data))

        atom_features = self._get_vertex_features(mol)
        atom_features = torch.FloatTensor(atom_features).view(-1, len(atom_features[0]))

        edge_indices, edge_attributes = self._get_edge_features(mol)
        edge_indices = torch.tensor(edge_indices)
        edge_indices = edge_indices.t().to(torch.long).view(2, -1)
        edge_attributes = torch.FloatTensor(edge_attributes)

        if edge_indices.numel() > 0:  # Sort indices
            permutation = (
                edge_indices[0] * atom_features.size(0) + edge_indices[1]
            ).argsort()
            edge_indices, edge_attributes = (
                edge_indices[:, permutation],
                edge_attributes[permutation],
            )

        return TorchGeometricData(
            x=atom_features,
            edge_index=edge_indices,
            edge_attr=edge_attributes,
            smiles=data,
        )

    def _get_vertex_features(self, mol: Chem.Mol) -> List[List[float]]:
        return [self._featurize_atom(atom) for atom in mol.GetAtoms()]

    def _get_edge_features(
        self, mol: Chem.Mol
    ) -> Tuple[List[List[int]], List[List[float]]]:
        edge_indices, edge_attributes = [], []
        for bond in mol.GetBonds():
            i = bond.GetBeginAtomIdx()
            j = bond.GetEndAtomIdx()

            edge_indices += [[i, j], [j, i]]
            bond_features = self._featurize_bond(bond)
            edge_attributes += [bond_features, bond_features]

        return edge_indices, edge_attributes

    @abstractmethod
    def _featurize_atom(self, atom: Chem.Atom) -> List[float]:
        raise NotImplementedError

    @abstractmethod
    def _featurize_bond(self, bond: Chem.Bond) -> List[float]:
        raise NotImplementedError


class AbstractDescriptorComputer(metaclass=ABCMeta):
    @abstractmethod
    def run(self, mol: Chem.Mol) -> List[float]:
        raise NotImplementedError


class RdkitDescriptorComputer(AbstractDescriptorComputer):
    def _get_descriptor_calculators(self) -> List[Callable]:
        from rdkit.Chem import (
            Descriptors,
            Lipinski,
            Crippen,
            MolSurf,
            GraphDescriptors,
            rdMolDescriptors,
            QED,
        )

        return [
            Descriptors.MolWt,
            Descriptors.NumRadicalElectrons,
            Descriptors.NumValenceElectrons,
            rdMolDescriptors.CalcTPSA,
            MolSurf.LabuteASA,
            GraphDescriptors.BalabanJ,
            Lipinski.RingCount,
            Lipinski.NumAliphaticRings,
            Lipinski.NumSaturatedRings,
            Lipinski.NumRotatableBonds,
            Lipinski.NumHeteroatoms,
            Lipinski.HeavyAtomCount,
            Lipinski.NumHDonors,
            Lipinski.NumHAcceptors,
            Lipinski.NumAromaticRings,
            Crippen.MolLogP,
            QED.qed,
        ]

    def run(self, mol: Chem.Mol) -> List[Union[int, float]]:
        return [featurizer(mol) for featurizer in self._get_descriptor_calculators()]


class MordredDescriptorComputer(AbstractDescriptorComputer):
    def __init__(self):
        from mordred import Calculator, descriptors

        self._calculator = Calculator(descriptors, ignore_3D=True)

    def run(self, mol: Chem.Mol) -> List[Union[int, float]]:
        descriptors = self._calculator(mol)
        return list(descriptors.fill_missing(0))


class GraphFeaturizer(AbstractTorchGeometricFeaturizer):
    """
    Improved featurizer for graph-based models
    """

    DEFAULT_ATOM_TYPES = [
        "B",
        "C",
        "N",
        "O",
        "F",
        "Na",
        "Si",
        "P",
        "S",
        "Cl",
        "K",
        "Br",
        "I",
    ]

    def __init__(
        self,
        inputs: List[str],
        outputs: List[str],
        descriptor_calculator: AbstractDescriptorComputer,
        allowed_atom_types: Optional[List[str]] = None,
        should_cache: bool = False,
        rewrite: bool = True,
    ):
        super().__init__(inputs, outputs, should_cache, rewrite)

        if allowed_atom_types is None:
            allowed_atom_types = self.DEFAULT_ATOM_TYPES

        self._allowed_atom_types = allowed_atom_types
        self._descriptor_calculator = descriptor_calculator

    def _process(self, data: str) -> TorchGeometricData:
        mol = Chem.MolFromSmiles(data)
        data = super()._process(data=data)

        molecule_features = self._descriptor_calculator.run(mol)
        molecule_features = torch.FloatTensor(molecule_features).view(
            -1, len(molecule_features)
        )

        data.molecule_features = molecule_features
        return data

    def _featurize_atom(self, atom: Chem.Atom) -> List[float]:
        return list(
            itertools.chain.from_iterable(
                [featurizer(atom) for featurizer in self._list_atom_featurizers()]
            )
        )

    def _featurize_bond(self, bond: Chem.Bond) -> List[float]:
        return list(
            itertools.chain.from_iterable(
                [featurizer(bond) for featurizer in self._list_bond_featurizers()]
            )
        )

    def _list_atom_featurizers(self) -> List[Callable]:
        # 45 features by default
        from federated_learning.vendor.dgllife.utils.featurizers import (
            atom_type_one_hot, atom_degree_one_hot, atom_implicit_valence_one_hot, atom_formal_charge,
            atom_num_radical_electrons, atom_hybridization_one_hot, atom_is_aromatic, atom_total_num_H_one_hot
        )

        return [
            partial(
                atom_type_one_hot,
                allowable_set=self._allowed_atom_types,
                encode_unknown=True,
            ),
            atom_degree_one_hot,
            atom_implicit_valence_one_hot,
            atom_formal_charge,
            atom_num_radical_electrons,
            atom_hybridization_one_hot,
            atom_is_aromatic,
            atom_total_num_H_one_hot,
        ]

    def _list_bond_featurizers(self) -> List[Callable]:
        # 12 features
        from federated_learning.vendor.dgllife.utils.featurizers import (
            bond_type_one_hot, bond_is_conjugated, bond_is_in_ring, bond_stereo_one_hot
        )

        return [
            bond_type_one_hot,
            bond_is_conjugated,
            bond_is_in_ring,
            bond_stereo_one_hot,
        ]


class ChiralGraphFeaturizer(GraphFeaturizer):
    def _list_atom_featurizers(self) -> List[Callable]:
        from federated_learning.vendor.dgllife.utils.featurizers import (
            atom_chiral_tag_one_hot, atom_chirality_type_one_hot, atom_is_chiral_center
        )

        featurizers = super()._list_atom_featurizers()

        featurizers.extend(
            [
                atom_chiral_tag_one_hot,
                atom_chirality_type_one_hot,
                atom_is_chiral_center,
            ]
        )

        return featurizers


class AbstractFingerprintFeaturizer(AbstractFeaturizer):
    """Abstract featurizer for fingerprints"""

    @abstractmethod
    def _process(self, data: Any) -> Union[List[int], np.ndarray]:
        raise NotImplementedError


class CircularFingerprintFeaturizer(AbstractFingerprintFeaturizer):
    """Morgan fingerprint featurizer"""

    def __init__(
        self,
        inputs: List[str],
        outputs: List[str],
        should_cache: bool = False,
        rewrite: bool = True,
        fingerprint_size: int = 2048,
        radius: int = 2,
        use_chirality: bool = False,
    ):
        super().__init__(inputs, outputs, should_cache, rewrite)

        self._fingerprint_size = fingerprint_size
        self._radius = radius
        self._use_chirality = use_chirality

    def _process(self, data: str) -> torch.FloatTensor:
        mol = Chem.MolFromSmiles(data)
        if mol is None:
            raise FeaturizationError("Could not featurize entry: [{}]".format(data))

        return torch.FloatTensor(self._generate_fingerprint(mol))

    def _generate_fingerprint(self, mol: Chem.Mol) -> np.ndarray:
        from rdkit.Chem import AllChem

        fingerprint = AllChem.GetMorganFingerprintAsBitVect(
            mol,
            radius=self._radius,
            nBits=self._fingerprint_size,
            useChirality=self._use_chirality,
        )

        features = np.zeros(self._fingerprint_size, dtype=np.uint8)
        features[fingerprint.GetOnBits()] = 1

        return features


class OneHotEncoderFeaturizer(AbstractFeaturizer):
    """One-Hot encode a single string"""

    def __init__(
        self,
        inputs: List[str],
        outputs: List[str],
        classes: List[str],
        should_cache: bool = False,
        rewrite: bool = True,
    ):
        super().__init__(inputs, outputs, should_cache, rewrite)

        self._classes = classes

    def _process(self, data: str) -> torch.FloatTensor:
        features = np.zeros(len(self._classes))
        features[self._classes.index(data)] = 1

        return torch.FloatTensor(features)


class TokenFeaturizer(AbstractFeaturizer):
    """Similar to the one-hot encoder, but will tokenize a whole sentence."""

    def __init__(
        self,
        inputs: List[str],
        outputs: List[str],
        vocabulary: List[str],
        max_length: int,
        separator: str = "",
        should_cache: bool = False,
        rewrite: bool = True,
    ):
        super().__init__(inputs, outputs, should_cache, rewrite)

        self._vocabulary = vocabulary
        self._separator = separator
        self._max_length = max_length

    def _process(self, data: str) -> torch.FloatTensor:
        tokens = (
            data.split(self._separator)
            if self._separator
            else [character for character in data]
        )
        features = np.zeros((self._max_length, len(self._vocabulary)))

        for index, token in enumerate(tokens):
            if index == self._max_length:
                logging.warning(
                    "[CAUTION] Input is out of bounds. Features will be trimmed. --- {}".format(
                        data
                    )
                )
                break

            features[index][self._vocabulary.index(token)] = 1

        return torch.FloatTensor(features)


class BagOfWordsFeaturizer(AbstractFeaturizer):
    def __init__(
        self,
        inputs: List[str],
        outputs: List[str],
        vocabulary: List[str],
        max_length: int,
        should_cache: bool = False,
        rewrite: bool = True,
    ):

        super().__init__(inputs, outputs, should_cache, rewrite)

        self._vocabulary = self._get_combinations(vocabulary, max_length)
        self._max_length = max_length

    def _get_combinations(self, vocabulary: List[str], max_length: int) -> List[str]:
        combinations = []

        for length in range(1, max_length + 1):
            for variation in itertools.product(vocabulary, repeat=length):
                combinations.append("".join(variation))

        return combinations

    def _process(self, data: str) -> torch.FloatTensor:
        sample = dict.fromkeys(self._vocabulary, 0)

        for length in range(1, self._max_length + 1):
            for start_index in range(0, len(data) - length + 1):
                sample[data[start_index : start_index + length]] += 1

        return torch.FloatTensor(list(sample.values()))


class FASTAFeaturizer(BagOfWordsFeaturizer):

    def _process(self, data:str) -> torch.FloatTensor:
        data = data.split("\n")[-1]
        return super()._process(data)


class TransposeFeaturizer(AbstractFeaturizer):
    def _process(self, data: torch.Tensor) -> torch.Tensor:
        return data.transpose(-1, -2)


class FixedFeaturizer(AbstractFeaturizer):
    def __init__(
        self,
        inputs: List[str],
        outputs: List[str],
        value: float,
        should_cache: bool = False,
        rewrite: bool = True,
    ):
        super().__init__(inputs, outputs, should_cache, rewrite)
        self._value = value

    def _process(self, data: float) -> float:
        return round(data / self._value, 8)


class ConverterFeaturizer(AbstractFeaturizer):
    def __init__(
        self,
        inputs: List[str],
        outputs: List[str],
        source_format: str,
        target_format: str,
        should_cache: bool = False,
        rewrite: bool = True,
    ):
        super().__init__(inputs, outputs, should_cache, rewrite)

        self._source_format = source_format
        self._target_format = target_format

        from openbabel import pybel

        self._pybel = pybel

    def _process(self, data: str) -> str:
        return (
            self._pybel.readstring(self._source_format, data)
            .write(self._target_format)
            .strip()
        )
