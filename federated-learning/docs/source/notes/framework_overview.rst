Framework Overview
==================

Project Structure
-----------------

The code is divided into several folders:

* ``data``: contains datasets, checkpoints, certificates, logs, and everything else data related. This folder is not fixed. Data can be stored anywhere else on the disk.
* ``lib``: contains all the custom code implemented for data preprocessing, training, inference, and experimenting with models in general.
* ``mila``: contains the communication module (federated learning)
* ``vendor``: contains chunks of code from 3rd party libraries
* ``run.py``: is the entry point for experiments (models, not federated learning)
* ``environment.yml``: are installation environments and scripts

.. figure:: /_figures/structure.png
    :alt: the project structure
    :scale: 70%

The main codebase ``lib`` is furthermore split into 4 folders:

* ``core``: contains often used functionality and helper functions
* ``data``: contains data handles and pre-processing tools
* ``model``: contains architectures, metrics, and modeling tools
* ``visualization``: contains functionality from visualizing results

The ``core`` folder contains:

* ``config.py``: for configuration parsing
* ``exceptions.py``: for exception handling
* ``helpers.py``: for functionality like caching, time tracking, reflection, and dependency injection
* ``observers.py``: for event management
* ``tuning.py``: for Bayesian optimization

The ``data`` folder contains:

* ``featurizers.py``: for preparing input fields
* ``loaders.py``: for loading raw data formats from disk
* ``resources.py``: for common structures
* ``splitters.py``: for data splitting
* ``streamers.py``: where we combine data loading and preprocessing tools
* ``transformers.py``: for preparing output fields

The ``mila`` folder contains:

* ``protocol_buffers``: for service contracts and gRPC messages
* ``aggregators.py``: for aggregator implementations
* ``configs.py``: for server and client configuration parsing
* ``exceptions.py``: for exception handling
* ``factories.py``: for abstractions
* ``run.py``: is the entry point for federated learning (both server and clients)
* ``services.py``: implements the communication between server and clients

The vision and efforts for the provided solution are centered are 3 key points:

* Good quality and clean code
* Extensible with minimum effort
* Highly configurable and easy to use

Several concepts and design patterns are utilized as a means of improving these characteristics.
Some of these major components are briefly discussed in the following sections.

Abstractions
------------

Most of our components, like loaders, featurizers, networks, or execution pipelines are `designed by contract <https://en.wikipedia.org/wiki/Design_by_contract>`_.
For each group of components, we first design an abstract class (ie: AbstractLoader) with common functionality, but more importantly, common methods.
The abstract classes are then extended to implement detailed solutions (ie: CsvLoader).

Then, if high level components (like the streamers) rely on low level ones (like the loaders), it is enough for us to specify the abstraction, and the high level module will be able to handle all subtypes of it (it acts as a contract).
In object-oriented design, this is referred to as `dependency inversion <https://en.wikipedia.org/wiki/Dependency_inversion_principle>`_.

Dependency Injection
--------------------

Dependency injection makes a class independent of its dependencies (ie: input arguments).
This is achieved by decoupling the use of a component from its instantiation.

Among other things, this means the code of a lower level objects can be changed without having to modify higher level objects which depend on it.
This can be a very powerful concept, because it allows us to easily add new functionality without having to write a lot of additional code.

For a more visual way to see the benefits of this concept, see the next section.

Dynamic Configuration
---------------------

To run experiments, we require a configuration file in JSON format (details in a later section).
While some of the structure is rigid, for the most part, configurable options are directly linked to the argument lists of the components' constructor.
This is achieved with `Dependency Injection`_.

For example, let us assume we have a ``Calculator`` object we want to make use of:

.. code-block:: python

    # file: custom/helpers.py

    class Calculator:
        def __init__(self, x: int, y: int):
            self._x = x
            self._y = y

        def sum(self) -> int:
            return self._x + self._y

To make use of this object, no changes have to be made to the configuration parsing logic whatsoever.
We just point to the class we want to use and specify its arguments:

To make use of this object, no changes have to be made to the configuration parsing logic whatsoever.
We just point to the class we want to use and specify its arguments:

.. code-block:: javascript

    {
        "helper": {
            "type": custom.helpers.Calculator,
            "x": 2,
            "y": 3
        }
    }

Input arguments do not have to be numeric though, we can use any objects whatsoever.
If additional classes are required, they will be instantiated recursively.
As an example, this would also work:

.. code-block:: python

    # file: custom/computers.py

    from custom.helpers import Calculator

    class Computer:

        def __init__(self, calculator: Calculator, constants: list):
            self._calculator = calculator
            self._constants = constants

        def sum(self, x: int, y: int) -> int:
            return self._calculator.sum(x, y)


.. code-block:: javascript

    {
        "computer": {
            "type": "custom.computers.Computer",
            "calculator": {
                "type": custom.helpers.Calculator,
                "x": 2,
                "y": 3
            },
            "constants": [1, 5]
        }
    }


We make use of this functionality a lot, and it makes it very easy to use already
implemented features like loss functions from the core Pytorch library or graph convolutional operators from Pytorch Geometric.
More importantly, we can make use of them without having to write large chunks of complicated logic, or any code at all for most cases.

On the negative side, the compatibility can make the configuration less straight
forward and require a level of knowledge about the underlying arguments.
We make this easier by providing plenty of examples on how to configure experiments (see the ``experiment_configs`` folder).

Events & Observers
------------------

Not everything can be solved with dependency injection.
Some areas of any framework are just inherently complicated, complicated code is
never good because it is messy, hard to maintain and more error-prone.

One good example is the training pipeline.
Even for minimal functionality, we need to load checkpoints, initiate data loaders,
perform forward and backward passes, log progress, and compute metrics.
However, as a central area where many components connect, usually things do not
stop there and extra functionality continue to pile up in the area.

To somewhat mitigate this problem, we introduced an event manager, also called
an `observer pattern <https://en.wikipedia.org/wiki/Observer_pattern>`_.
In an observer pattern, we keep track of a list of dependents which are automatically notified when important events happen.
In case of the training pipeline for example, we can define such a dependent to
receive a payload containing the model and optimizer right before backpropagation happens.
Of course, we can then add any changes we want using that payload.

There are several benefits to this approach.

* We will not have an ever-growing training script for one
* Due to dynamic configuration, anyone can add their own event handlers without having to touch the core codebase at all
* This is very useful for backwards compatibility as well, because changes will not be overwritten upon update

However, adding too many observers which modify the original behavior can hide or cause dependency issues, and make the functionality harder to debug.

Models
------

Models live under the ``lib/`` folder.

Each experiment requires a configuration file to run, which we describe in the next section.
Furthermore, for the models to be compatible with Mila, it has to extend 2 abstract classes from the Mila library.

* The ``AbstractConfiguration`` class - responsible for configuration handling
* The ``AbstractExecutor`` class - responsible for starting the train, validation, and inference processes.

Configuration
-------------

Configuration files are stored in JSON format and parsed by a class extending ``AbstractConfiguration``.
When using Mila with a ``BenchmarkedAggregator``, the extended configuration must also include a ``checkpoint_path`` argument.

All experiments and operations make use of the same configuration file.
Certain fields are dynamic and used for dependency injection.
In these cases a "type" subfield will specify the desired class type, while all other subfields will be considered arguments for that class.
Class arguments themselves can contain a "type" subfield, in which case additional objects will be instantiated recursively.
