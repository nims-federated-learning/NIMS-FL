

Use Bayesian optimization
=======================================

`Optuna <https://optuna.org/>`_ is an open source hyperparameter optimization
framework we are using for the Bayesian optimization.

In order to use Optuna, you need to update your `model configuration <../configuration_details/configuration_model>`
in a certain way to enable the parsing of the argument to optimize.

Once you finished updated your config, simply run:

.. code:: none

    nims-federated-learning-base optimize path_to/config.json


Set up config for Bayesian optimization
"""""""""""""""""""""""""""""""""""""""

We have a parser to recognize which fields are supposed to be optimized with Optuna.
You need to follow the following rules:

- each placeholder should have a name and some options, separated by an equal sign - ie: ``"{{{name=options}}}"``
- options separated by ``|`` will be categorical - ie: ``"{{{aggregate=mean|sum|max}}}"``
- numeric values should have 3 options separated by a dash ``-``. ie: ``"{{{dropout=min|max|step}}}"``
- The first value is the minimum value
        - The second value is the maximum value
        - The third value is the incremental step between the minimum and the maximum
        - The [minimum, maximum] is a closed interval
- if numeric values contain a dot ".", a float value will be suggested ie: ``"{{{dropout=0.0-0.7-0.1}}}"``
- if numeric values do not contain a dot ".", an int value will be suggested ie: ``"{{{layers=2-5-1}}}"``

So for example if I want to test various values of dropout in my model I will change
the model parameter with:

.. code:: javascript

    "model": {
        "type": "SimpleMLP",
        "in_features": 22,
        "out_features": 1,
        "hidden_features": 512,
        "n_layer": 5,
        "dropout": "{{{dropout=0.0-0.7-0.1}}}"
    }

At the end of the study the result of the best parameters will be displayed with
its target metric results.
