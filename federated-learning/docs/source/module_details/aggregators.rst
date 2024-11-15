.. _aggregators:

Aggregators
============

Aggregators are responsible for network aggregation between all the clients.
It is always a matter of merging the locally trained networks by individual clients after a given number of steps.
Many methods exist and aggregation in federated learning is still an active area of research.
The implemented methods in the framework are the following:

* ``plain aggregation``
* ``Weighted aggregation``
* ``benchmark aggregation``
* ``fedrox aggregation``

The aggregator is configurable in the server config file, here is an example:

.. code-block:: javascript

    {
        "task_configuration_file": "path/to/config.json",
        "aggregator_type": "mila.aggregators.WeightedTorchAggregator",
        "aggregator_options": {"weights": {"tester1": 0.8, "tester2": 0.2}},

        "config_type": "lib.core.config.Config",
        "executor_type": "run.Executor",

        "rounds_count": 50,
        "workers": 4,
        "minimum_clients": 2,
        "maximum_clients": 2,

        "client_wait_time": 300
    }


Plain aggregation
-----------------------------------

Plain aggregation is invoked by the class ``PlainTorchAggregator`` and is the most basic aggregator in federated learning, it uses FedAverage.
This aggregator considers all the clients even in the aggregation process no matter the data ratio between clients.

Plain aggregation doesn't need additional options.


Weighted aggregation
-----------------------------------

Weighted aggregator is defined in the ``WeightedTorchAggregator``.

This aggregator scales the responsibility of each client depending on data distribution/ratio.
Typically, a client with twice as many data than another client will be 2 times more important in the aggregation process.
It is the most common application of FedAvg.

With this aggregator we need to provide the weights of each client additionally as aggregator_options:

.. code-block:: javascript

    "aggregator_options":
        {
            "weights":
                {
                    "client_1": weight1,
                    "client_2": weight2,
                    ... : ...,
                }
        }

ex:
``"aggregator_options": {"weights": {"tester1": 0.8, "tester2": 0.2}}``


Benchmark aggregation
-----------------------------------

This aggregator scale the responsibility of each client depending on the result
of their respective evaluation score on the test set.
Typically, a client with a local evaluation score twice better than another client will
be 2 times more important in the aggregation process.
This is especially useful when the test dataset used in evaluation is shared across clients.

With this aggregator we need to provide the following information as aggregator_options:



.. code-block:: javascript

    "aggregator_options":
        {
            "config_type": "config_type",
            "config_path": "config_path",
            "executor_type": "Executor_type",
            "target_metric": "target_metric",
        }

ex:
``"aggregator_options": {"config_type": "lib.core.config.Config", "config_path": "path/to/config.json", "executor_type": "run.Executor", "target_metric": "rmse"}``

.. note::

    The dataset used for evaluation is the test split provided in the model config
    at the given `config_path`. This means that this dataset needs to be present on
    the server node.

Fedrox aggregation
-----------------------------------

`FedProx <https://arxiv.org/abs/1812.06127>`_ uses regularization to harmonize the individual training.
In practice, FedProx penalizes each client for changing too much from the original network received by the server at each round.
This is supposed to help convergence and reduce the dominance effect of some nodes.

Fedprox is configured differently than other aggregator and uses one of the previous aggregator like ``PlainTorchAggregator``
with an additional observer added in the model configuration:

.. code-block:: javascript

    "observers": {
            "after_criterion": [
                {
                    "type": "add_fedprox_regularization",
                    "mu": 1
                }
            ]
        },


.. note::

    According to the authors of the paper, you might want to tune mu from {0.001, 0.01, 0.1, 0.5, 1}.
    There are no default mu values that would work for all settings.