Getting Started
===============

.. contents::


Content of the deliverable
-----------------------------

In the deliverable we provided there is the various file and folder describe below:

- federated-learning (folder)
    Contain the code for the project.
- docs (folder)
    Contain a pdf and HTML version of this documentation.
- experiment_configs (folder)
    Contain all experiment configs necessary to rerun our experiments.
- README.md (file)
    Contains a subset of the documentation


Installation
-----------------------------------

Use the provided conda snapshot:

.. code:: bash

    conda env create -f environment.yml  # first time only
    conda activate federated
    bash install_additional_dependencies.sh  # first time only


Command line
-----------------------------------

There are two commands line input possible:

- ``nims-federated-learning-base``
- ``nims-federated-learning``

nims-federated-learning-base
""""""""""""""

This command is used for standard training (no federated-learning) and optimization there is a variety of command possible.

It expects a couple of argument:

.. code:: none

    nims-federated-learning-base {job} {config}

Where ``job`` is one of the task detail below and ``config`` the path to a
:doc:`model configuration <../configuration_details/configuration_model>`.

``train``
^^^^^^^^^^

Run a standard training base on the configuration provided.


``eval``
^^^^^^^^^

Launch evaluation of the model and return the target metric for the `checkpoint_path` provided.

``mean_cv``
^^^^^^^^^^^^

Run cross validation for the given config and return the mean average of the target
metric.


``predict``
^^^^^^^^^^^^

Run inference on the dataset `test_split` and save result in a `predictions.csv` file
in the `output_path` directory.


``optimize``
^^^^^^^^^^^^^

Run optimization with optuna base on the configuration provided

:doc:`more detail on optimisation runs <../tutorials/using_optuna>`


``find_best_checkpoint``
^^^^^^^^^^^^^^^^^^^^^^^^^

Find the best checkpoint base on the `output_path` and `epochs` parameters.
It will evaluate all checkpoint in the directory until provided `epochs` number and return the
best one as well as it's target metrics.



nims-federated-learning
"""""""""""""""""""""""""

This command is used for federated-learning training.

It expects a couple of argument:

.. code:: none

    nims-federated-learning {job} {config}

Where ``job`` is one of the three tasks ``server``, ``client`` or ``mean_cv``
and ``config`` the path to the expected config format to the task,
:doc:`see the expected format here <../configuration_details/configuration_mila>`.

``server``
^^^^^^^^^^^

Launch a server node (should always be the first node to be launch)

``client``
^^^^^^^^^^^

Launch a client node


``mean_cv``
^^^^^^^^^^^^

Wrapper around multiple launch of both server and clients.
It will launch `num_folds` number of experiment and save all results and prediction
to the `output_path`.

This is a scenario only useful for testing different model and should be run on
only one computer since one program manage all client and server.
This is due to the fact that when splitting the dataset, we must have the full
dataset at hand to make the different folds. And all clients must split the dataset
in the exact same way.