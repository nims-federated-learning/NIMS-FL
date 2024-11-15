
Splitters
==========

The last of the major abstraction based dynamic settings, the "splitter" specifies how to split the dataset.
These options are used to instantiate components extending ``lib.data.splitters.AbstractSplitter``.

An example of configuration for a stratified splitter:

.. code-block:: javascript

    "splitter": {
        "type": "stratified",
        "seed": 42,
        "target_name": "label",
        "splits": {"train": 0.8, "test": 0.2}
    },

As a dynamic option, splitter classes are specified using the "type" argument.
We have the following splitter types:

``index``:
    For index-based splitting
``random``:
    For random splits
``stratified``:
    For stratified splits based on a certain output column/property
``categorical``:
    For splitting with each split having distinct element of the specified category.

Shared argument
"""""""""""""""

``splits``

All splits require a ``splits`` argument in a dictionary (key-value) format.
The keys denote the name of the split and can be any users-specified value (we generally used ``train`` and ``test``).
The values represent the proportions for each split and should add up to 1.
Users can specify any number of splits, not only 2.

In most cases when using the ``mean_cv`` job the split are overwritten for the right number of folds.

``seed (default = 42)``

The ``random`` / ``stratified`` and ``categorical`` splitters also require a
``seed`` argument which is used to set the random state for reproducible splits.


Stratified
""""""""""""

``target_name``

The ``stratified`` split requires a ``target_name`` argument, which should be
an entry of the loader's ``target_column_names`` argument.
The split will be performed based on this column.
If the ``target_name`` contains continuous values, they can be grouped into a
number of bins using quantile-based discretization (ie: equal-sized buckets based on rank).
Users can specify the number of bins using the ``bins_count`` argument.


``is_target_input (default = False)``

In case the ``target_name`` is used as an input in the loader.


``rewrite (default = False)``

If ``is_target_input`` is True by settings ``rewrite`` to True the feature will
be deleted from the input and so will only be used for splitting and not during
training.


Categorical
""""""""""""


``cat_name``

The name of the input_feature to use for the splitting.


.. warning::

    There is two case in this scenario.

    Case 1:

    For training with ``nims-federated-learning-base`` or  in the case you are using ``mean_cv``
    task of ``nims-federated-learning`` the splitting occurs has other models.


    Case 2:

    In case of standard training with ``nims-federated-learning`` using the ``subset`` ``distribution``
    argument of model configuration is not possible to split the data between client
    since the splits needs to be made base on the category information.

    So in this case ``subset`` ``distribution`` is not useful.
    But you need to provide and ``id`` and the name of the split must be ``client_{id}``.

    For example let's look into config made for the multi-step experiment:

    .. code:: javascript

        // client2.json
        // notice we only use subset for the id, here 1.
        {
            "name": "tester2",
            "config_type": "lib.core.config.Config",
            "save_path": "data/logs/client/tester2/",
            "executor_type": "run.Executor",
            "model_overwrites": {
                "output_path": "data/logs/local/tester2/",
                "epochs": 10,
                "subset": {
                    "id": 1
                }
            }
        }


        // Here we must provide the distribution for each client, client2 will have client_{id}
        // So client_1 value it will use 8% of the dataset (10% of the training data)
        {
        ...
        "splitter": {
            "type": "Categorical",
            "cat_name": "Reference Code",
            "splits": {
                "client_0": 0.48,
                "client_1":0.08,
                "client_2":0.08,
                "client_3":0.08,
                "client_4":0.08,
                "test": 0.2
            },
            "seed": 42
        },
        ...
        }

    This is a constraint but since the categorical set up is not possible to use
    outside testing scenario with a full dataset it is possible to fix all those
    parameters.