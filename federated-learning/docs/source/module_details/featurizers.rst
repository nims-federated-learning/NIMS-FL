
Featurizers
=============

.. code-block:: javascript

    "featurizers": [
        {
            "type": "graph",
            "inputs": ["smiles"],
            "outputs": ["ligand"],
            "descriptor_calculator": {"type": "rdkit"}
        }, {
            "type": "bag_of_words",
            "inputs": ["target_sequence"],
            "outputs": ["protein"],
            "should_cache": true,
            "vocabulary": [
                "A", "C", "D", "E", "F", "G", "H", "I", "K", "L", "M",
                "N", "P", "Q", "R", "S", "T", "V", "W", "Y", "X"
            ],
            "max_length": 3
        }
    ],

The above is an example configuration of a featurizer for protein-ligand affinity prediction

Featurizers prepare the input features for the training or inference.
The expected input is a list, and therefore we can specify more than one featurizer per experiment.
Featurizers are dynamic fields used to instantiate components extending ``lib.data.featurizers.AbstractFeaturizer``.

As any dynamic field, the featurizer to be used is specified with the ``type`` option.

The supported featurizers are as follows:

``graph``:
    For graph featurization.
    This featurizer expects a SMILES string for input, and the generated features can be used by graph architectures ``graph_convolutional``, ``message_passing``, or ``triplet_message_passing``)
``circular_fingerprint``:
    For fingerprint featurization.
    This featurizer expects a SMILES string for input, and the generated features can be used by the *linear* architecture.
``token``:
    Similar to the one-hot encoder, but will tokenize a whole sentence (like an amino-sequence).
    The expected input is a sequence (string), and the output can be used by the *convolutional* architecture.
``bag_of_words``:
    Performs an n-gram, bag-of-words featurization.
    The expected input is a sequence (string), and the generated features can be used by the *linear* architecture.
``one_hot_encoder``:
    Can one-hot encode categorical features.
    The expected input is a string.
    No architectures make direct use of this featurizer at this point, however, it could be used in a featurization pipeline to prepare inputs for other featurizers.
``transpose``:
    Is an intermediary featurizer.
    It expects a Torch Tensor as input and will output a transposed version of it.
    This of course can be done in a model directly, however, featurized outputs are cached, and can save valuable computational time.
``fixed``:
    Is an intermediary featurizer.
    It expects a single float as input and will return that value divided by a user specified value.
``tensor``:
    Featurizer for independant linear data.
    Featurizers for linear tabular type data. It return a torch type floating vector out of 1d data.
``tensor tabular``:
    Similar to `tensor` but concatenate all inputs in one 1d vector data.

Featurizers have custom arguments which can be configured, but all of them will have at least 3 parameters:

``inputs``:
    A list of input targets.
    These values should match the ones specified in the ``input_column_names`` option of the loader.
``outputs``:
    A list of output targets.
    These values should match the arguments expected by the network architectures.
    The list of arguments expected by each model is listed in Table 3.1.
``should_cache``:
    Whether we should perform sample level caching.
    Note that this is different from global caching, which is performed after featurization.
    When this option is set to true, each input will be cached in-memory and will not be processed again.
    This can be very helpful when we are dealing with many duplicates in a certain column which are expensive to compute, like amino-acid sequences. (defaults to ``False``)

All featurizers will have these configurable options, and the ``inputs`` and ``outputs`` arguments are mandatory.
However, most featurizers will have additional configurable options.

The ``graph`` featurizer supports:
    ``descriptor_calculator``:
        Specify how and what molecule level features to compute.
        The supported options include RDKit and mordred.
    ``allowed_atom_types``:
        Specify which atom types should be considered explicitly for (one-hot) encoding.
        Other atoms will be grouped as a general ``other`` feature.
        The default option includes: B, C, N, O, F, Na, Si, P, S, Cl, K, Br, and I.

In additional to symbol based encoding, the graph featurizer also encodes a one-hot atom degree encoding (from 0 to 10), one-hot implicit valence encoding (form 0 to 6), the formal charge, the number of radical electrons, one-hot encoded hybridization, an aromaticity flag, and the total number of Hydrogen atoms.
By default, these amounts to 45 input features.
If additional atom types are specified, the input features settings should reflect those changes.

For bond level features, we compute a bond type one-hot encoding (single, double, triple, or aromatic), a conjucation flag, a ring membership flag, a stereo configuration encoding.
All these amount to 12 edge features.

The ``circular_fingerprint`` featurizer supports:
    ``fingerprint_size``:
        The number of bits (defaults to ``2048``)
    ``radius``:
        Defaults to ``2``

The ``one_hot_encoder`` featurizer requires:
    ``classes``:
        A list of all possible tokens (ie: ``male``, ``female``)

The ``token`` featurizer supports:
    ``vocabulary``:
        A list of all possible tokens (ie: ``A``, ``C``, ``T``, ``G``)
    ``max_length``:
        The length of the largest sequence (smaller sequences will be 0-padded)
    ``separator``:
        A separator for the tokens.
        If an empty string ``""`` is specified, the string will be split character-by-character (defaults to ``""``)

The ``bag_of_words`` featurizer supports:
    ``vocabulary``:
        A list of all possible tokens (ie: ``A``, ``C``, ``T``, ``G``)
    ``max_length``:
        The length of the largest sequence (smaller sequences will be 0-padded)

The ``fixed`` featurizer requires:
    ``value``: the value to divide the input by


The ``tensor`` and ``tensor_tabular`` featurizer doesn't require additional feature.