.. _model:

Models
========

The model option is used to specify which model architecture to use and the options of that model.
It is a dynamic field and used to instantiate torch modules which extend ``lib.model.architectures.AbstractNetwork``.

As a dynamic field, the "type" argument is used to specify which class to use.
At the moment, we support 6 architectures as input for the "type" option:

* ``graph_convolutional``
* ``message_passing``
* ``triplet_message_passing``
* ``linear``
* ``convolutional``
* ``protein_ligand``
* ``SimpleMLP``

The following is an example of configuring a Graph Convolutional Network

.. code-block:: javascript

    "model": {
        "type": "graph_convolutional",
        "in_features": 45,
        "out_features": 1,
        "hidden_features": 160,
        "dropout": 0.1,
        "layer_type": "torch_geometric.nn.GCNConv",
        "layers_count": 3,
        "molecule_features": 17,
        "is_residual": 1,
        "norm_layer": "lib.model.layers.BatchNorm"
    }

Graph Convolutional Networks
-----------------------------------

The ``graph_convolutional`` is by far the most configurable architecture.
Customizable arguments for this model are as follows:

``in_features``:
    The number of input features. This value will depend on the options configured for graph featurizer, but should be ``45`` by default.

``hidden_features``:
    Number of hidden features used in the graph convolutional operation.

``out_features``:
    The number of output features. This should coincide with the number of concurrent tasks we are trying to predict (ie: 12 for Tox21, and 1 for AMES).

``molecule_features``:
    How many molecule level features are we expecting? This should be set to ``17`` for RdKit descriptors and ``1613`` for Mordred descriptors.

``dropout``:
    The dropout rate

``layer_type``:
    The graph convolutional operator (defaults to ``torch_geometric.nn.GCNConv``).
    We leverage implementations from Pytorch Geometric and support many layers listed in `torch_geometric.nn <https://pytorch-geometric.readthedocs.io/en/latest/modules/nn.html>`_.
    Layers which have been tested to work are as follows:

    * ``torch_geometric.nn.GCNConv``
    * ``torch_geometric.nn.ChebConv``
    * ``torch_geometric.nn.SAGEConv``
    * ``torch_geometric.nn.GraphConv``
    * ``torch_geometric.nn.ARMAConv``
    * ``torch_geometric.nn.LEConv``
    * ``torch_geometric.nn.GENConv``
    * ``torch_geometric.nn.ClusterGCNConv``
    * ``torch_geometric.nn.FeaStConv``
    * ``torch_geometric.nn.GATConv``
    * ``torch_geometric.nn.TAGConv``
    * ``torch_geometric.nn.SGConv``
    * ``lib.model.layers.GINConvolution``
    * ``lib.model.layers.TrimConvolution``

``layers_count``:
    The number of graph layers to use (defaults to ``2``)

``is_residual``:
    Whether to apply a residual connection to the graph operation (defaults to ``True``)

``norm_layer``:
    Which normalization layer to apply after the graph operation (defaults to ``None``).
    The available options are:

    * ``None``
    * ``lib.model.layers.BatchNorm``
    * ``lib.model.layers.GraphNorm``
    * ``torch_geometric.nn.LayerNorm``

``activation``:
    The activation function to use (defaults to ``torch.nn.ReLU``).
    For a list of options, please check the `PyTorch documentation on non-linear activations <https://pytorch.org/docs/stable/nn.html#non-linear-activations-weighted-sum-nonlinearity>`_.

``edge_features``:
    The number of edge features (defaults to ``0``).
    At the moment, the only working options are ``0`` or ``12``.
    If set to ``12``, edge features will be concatenated with atom features.

Message Passing Neural Networks
-----------------------------------

The ``message_passing`` architecture accepts the following options:

``in_features``:
    The number of input features.
    This value will depend on the options configured for graph featurizer, but should be "45" by default.

``hidden_features``:
    Number of hidden features used in the graph convolutional kernel.

``out_features``:
    The number of output features.

``edge_features``:
    The number of edge features.
    At the moment, the only working option is 12.

``edge_hidden``:
    The number of hidden features for the edge block.

``steps``:
    Number of processing steps to run

``dropout``:
    The dropout rate (defaults to ``0``)

``aggregation``:
    The aggregation scheme to use. (Options are: ``add``, ``mean``, or ``max``) (defaults to ``add``)

``set2set_layers``:
    Number of recurrent layers to use in the global pooling operator (defaults to ``3``)

``set2set_steps``:
    Processing steps for the global pooling operator (defaults to ``6``)

Triplet Message Passing Networks
----------------------------------------

The ``triplet_message_passing`` architecture accepts the following options:


``in_features``:
    The number of input features.
    This value will depend on the options configured for graph featurizer, but should be ``45`` by default.

``hidden_features``:
    Number of hidden features used in the graph convolutional kernel.

``out_features``:
    The number of output features.

``edge_features``:
    The number of edge features.
    At the moment, the only working option is ``12``.

``layers_count``:
    The number of Triplet Message Passing layers to use

``dropout``:
    The dropout rate (defaults to ``0``)

``set2set_layers``:
    Number of recurrent layers to use in the global pooling operator (defaults to ``1``)

``set2set_steps``:
    Processing steps for the global pooling operator (defaults to ``6``)

Linear Networks
---------------

The ``linear`` architecture is a simple Shallow Neural Network with 2 linear layers.

``in_features``:
    The number of input features

``hidden_features``:
    The number of hidden features

``out_features``:
    The number of output features

``activation``:
    The activation type (defaults to ``torch.nn.ReLU``)


SimpleMLPNetwork
-----------------

The ``SimpleMLPNetwork`` s a classic MLP Network used for tabular data. It is a succession of ``n_layer`` fully connected layer.

``in_features``:
    The number of input features

``hidden_features``:
    The number of hidden features

``out_features``:
    The number of output features

``n_layer``:
    The number of fully connected layer

``dropout``:
    Dropout for each block. Dropout is used for better generalization.

Convolutional Networks
-------------------------

The ``convolutional`` architecture is a simple Convolutional Network with a single 1D convolutional layer, and a max pooling layer, followed by a linear block as describe above:

``in_features``:
    The number of input features

``hidden_features``:
    The number of hidden features

``out_features``:
    The number of output features

Protein Ligand
---------------

The ``protein_ligand`` is a composite architecture.
That is, it takes 2 other modules as input, one for the ligand and one for the protein features.
Dependency injection again makes our work easy.

The following is an example configuration for Protein-Ligand Architecture

.. code-block:: javascript

    "model": {
        "type": "protein_ligand",
        "protein_module": {
            "type": "linear",
            "in_features": 9723,
            "hidden_features": 160,
            "out_features": 16
        },
        "ligand_module": {
            "type": "graph_convolutional",
            "in_features": 45,
            "out_features": 16,
            "hidden_features": 192,
            "dropout": 0.0,
            "layer_type": "torch_geometric.nn.GENConv",
            "layers_count": 5,
            "molecule_features": 17,
            "is_residual": 0,
            "norm_layer": "lib.model.layers.BatchNorm"
        },
        "hidden_features": 32,
        "out_features": 3
    }

``protein_module``:
    A list set of options for the protein module.
    Supported options include a *convolutional* architecture for tokenized inputs, or a *linear* architecture for bag-of-words featurized inputs.

``ligand_module``:
    A list set of options for the ligand module.

Supported options include a ``graph_convolutional``, ``message_passing``, or ``triplet_message_passing`` architecture for graph featurized ligands, or a ``linear`` architecture for circular fingerprints.

``hidden_features``:
    The number of hidden features

``out_features``:
    The number of output features

After the individual blocks are passed through, the outputs are concatenated and passed through a final ``linear`` block.
