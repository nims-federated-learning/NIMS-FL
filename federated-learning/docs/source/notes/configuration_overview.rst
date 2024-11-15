Configuration Overview
=======================

.. contents:


There are two mains sets of configuration. One is for the use of ``nims-federated-learning-base`` command
line argument, whereas for ``nims-federated-learning`` both type are needed.


:doc:`Model Configuration <../configuration_details/configuration_model>`
---------------------------------------------------------------------------

Configuration used to make a standard training. So it provides information about
the splitter, the optimizer, etc.


:doc:`more details <../configuration_details/configuration_model>`


:doc:`Mila Configuration (Federated learning) <../configuration_details/configuration_mila>`
----------------------------------------------------------------------------------------------

There is three set of configuration.


- Server configuration:
    Used to start a server node

- Client configuration:
    Used to start a client node

- Mean_cv configuration:
    Used in parallel with Server and Client config to launch a cross validation
    experiment.

    This can only be used on one machine where the dataset is being split across
    clients node and the folds are managed between each run.

:doc:`more details <../configuration_details/configuration_mila>`