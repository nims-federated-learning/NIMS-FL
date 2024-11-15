.. _mila:


Federated Learning (Mila)
==========================

.. contents::


Server and client processes are started similar to how models work. Each
servicer and consumer requires a configuration file, which is fed to the entry point.
In what follows, we describe the options for servers and clients separately.


Server Configurations
-----------------------------------

Server configuration files are expected to be in JSON format. The available options include:

``task_configuration_file (no default)``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Path to the model configuration file. This will be sent to each client along with the
checkpoint.

``config_type: (no default)``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


Module path to the configuration class (ie: "lib.config.Config")

``executor_type: (no default)``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


Module path to the executor class (ie: "run.Executor")

``aggregator_type (no default)``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Which aggregator to use? Options include:
- PlainTorchAggregator
- WeightedTorchAggregator
- BenchmarkedTorchAggregator

`more details <../module_details/aggregators>`

``aggregator_options (default={})``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Input parameters for the aggregator (the expected value is a dictionary) "PlainTorchAggregator" does not expect anything; the
"WeightedTorchAggregator" expects a "weights" options which is mapping between the client's "name" parameter and the expected wight.
For example, if we have 2 clients named "tester1" and "tester2", this option could be:

.. code-block:: javascript

    "aggregator_options": {
        "weights":
            {
                "tester1": 0.67,
                "tester2": 0.33
            }
    }

``target (default="localhost:8024")``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The gRPC service location URL (that is, the server address).

``rounds_count (default=10)``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

How many rounds to perform

``save_path (default="data/logs/server/")``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Indicates where to save checkpoints received from clients and the aggregate models.

``start_point (default=null)``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Optionally, specify a checkpoint for the first round. If nothing is specified, clients will start training from scratch.

``workers (default=2)``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Maximum number of processes handling client requests

``minimum_clients (default=2)``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Minimum number of clients required to start federated learning. The server won't
start the first round until this number is reached.

``maximum_clients (default=100)``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Maximum number of clients allowed to join the federated learning process.

``client_wait_time (default=10)``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Once the "minimum_clients" number is reach, the server will wait this many seconds
for additional clients before the process starts. After this time expires, no new members will be allowed to join.

``heartbeat_timeout (default=300)``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Indicates how long to wait for a keep alive signal from clients before declaring them "dead".

``use_secure_connection (default=false)``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

When true, the communication will be performed through HTTPS protocol. The 3 SSL files specified below must be valid for this to work.

`See here for more information about Secure connection <../tutorials/ssl_connection>`

``ssl_private_key (default="data/certificates/server.key")``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

gRPC secure communication private key

``ssl_cert (default="data/certificates/server.crt")``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

gRPC secure communication SSL certificate

``ssl_root_cert (default="data/certificates/rootCA.pem")``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

gRPC secure communication trusted root certificate

``options``
^^^^^^^^^^^^

Additional gRPC options. "grpc.max_send_message_length" represents the maximum length of a sent message, and "grpc.max_receive_message_length"
the maximum length of a received message.
The default value for this option is:

.. code-block:: javascript

    "options": [
        ["grpc.max_send_message_length", 1000000000],
        ["grpc.max_receive_message_length", 1000000000],
        ["grpc.ssl_target_name_override", "localhost"]
    ]


``blacklist (default=[])``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A list of IP addresses which will be declined upon authentication.

``whitelist (default=[])``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A list of IP addresses which will be allowed to join the federated learning process.

If "use_whitelist" is True, these will be the only IP addresses allowed to join.

``use_whitelist (default=false)``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Enables whitelist filtering.





Client Configurations
-----------------------------------

Client configuration files are also expected to be in JSON format. The available options include:

``name (no default)``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A unique identifier for this client (could be a company name for example)

``save_path (default="data/logs/client/")``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Where to save checkpoints received from the client?

``heartbeat_frequency (default=60)``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Indicates, how often keep alive signals are sent to the server.

``retry_timeout (default=1)``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If a request fails because the server is under heavy load, we retry the connection
after this many seconds.

``model_overwrites``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Used to override model configuration options. Generally, clients might want to
change the path where local (model) checkpoints are stored. The default value
for this option is:

.. code-block:: javascript

    {
    "output_path": "data/logs/local/",
    "epochs": 5
    }

``config_type: (no default)``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Module path to the configuration class (ie: "lib.config.Config")

``executor_type: (no default)``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Module path to the executor class (ie: "run.Executor")

``target (default="localhost:8024")``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The gRPC service location URL (that is, the server address)

``use_secure_connection (default=false)``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

When true, the communication will be performed through HTTPS protocol. The 3 SSL files specified below must be valid for this to work.

`See here for more information about Secure connection <../tutorials/ssl_connection>`


``ssl_private_key (default="data/certificates/client.key")``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

gRPC secure communication private key

``ssl_cert (default="data/certificates/client.crt")``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

gRPC secure communication SSL certificate

``ssl_root_cert (default="data/certificates/rootCA.pem")``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

gRPC secure communication trusted root certificate



Mean CV Configuration
-------------------------

``num_folds (no default)``
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Number of folds to run the cross validation on.

``seed (default = 42)``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Seed to use for the experiment

``cfg_clients (default = none)``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

List of path to client configuration to use during the experiment.
This field needs to be used with `cfg_server`.
This field can't be used with `cfg_dir`.

``cfg_server (default = '')``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Path to the server configuration.
This field needs to be used with `cfg_clients`.
This field can't be used with `cfg_dir`.


``cfg_dir (default = '')``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Path to a directory containing the client and server configs to use for the cross
validation training.
This field can't be used with both `cfg_clients` and `cfg_server`


``log_level (default = "INFO")``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Log level of the training possible values are ``['CRITICAL', 'FATAL', 'ERROR', 'WARN', 'WARNING', 'INFO', 'DEBUG', 'NOTSET']``


``save_results (default = False)``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Whether to save the best checkpoints and the inference results for each fold.

``output_path (no default)``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Directory where the results will be stored.