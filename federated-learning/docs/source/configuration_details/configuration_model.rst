Model Configuration
====================

.. contents:

:doc:`model <../module_details/models>`
""""""""""""""""""""""""""""""""""""""""""""

The model option is used to specify which model architecture to use and the options of that model.
It is a dynamic field and used to instantiate torch modules which extend ``lib.model.architectures.AbstractNetwork``.

As a dynamic field, the "type" argument is used to specify which class to use.
At the moment, we support 7 architectures as input for the "type" option:

* ``graph_convolutional``
* ``message_passing``
* ``triplet_message_passing``
* ``linear``
* ``convolutional``
* ``protein_ligand``
* ``simple_mlp``

:doc:`more details <../module_details/models>`

:doc:`loader <../module_details/loaders>`
"""""""""""""""""""""""""""""""""""""""""""""""
The loader option is used to configure how raw data files are loaded.
It is a dynamic field used to instantiate components which extend ``lib.data.loaders.AbstractLoader``.

We support 3 loaders at this time, which are specified in the ``type``:

* **csv**: For comma-separated values
* **excel**: For Excel spreadsheets (only one spreadsheet can be loaded at a time)
* **sdf**: For SDF files (where the whole dataset is stored in a single SDF file)

:doc:`more details <../module_details/loaders>`


:doc:`featurizer <../module_details/featurizers>`
"""""""""""""""""""""""""""""""""""""""""""""""""""""""
Featurizers prepare the input features for the training or inference.
The expected input is a list, and therefore we can specify more than one featurizer per experiment.
Featurizers are dynamic fields used to instantiate components extending ``lib.data.featurizers.AbstractFeaturizer``.

As any dynamic field, the featurizer to be used is specified with the ``type`` option.

:doc:`more details <../module_details/featurizers>`


:doc:`transformer <../module_details/transformers>`
""""""""""""""""""""""""""""""""""""""""""""""""""""""""
Transformers are very similar to featurizers, expect they are applied to output features, and are generally used to normalize values.
Transformers are dynamic fields used to instantiate components extending ``lib.data.transformers.AbstractTransformer``.

Each transformer implements an "apply" and a "reverse" operation, which converts the values back after inference (for prediction only, does not apply to metrics).
Similar to featurizers, multiple transformers can be used in the same experiment

:doc:`more details <../module_details/transformers>`


:doc:`splitter <../module_details/splitters>`
""""""""""""""""""""""""""""""""""""""""""""""""""""""""
The last of the major abstraction based dynamic settings, the "splitter" specifies how to split the dataset.
These options are used to instantiate components extending ``lib.data.splitters.AbstractSplitter``.

:doc:`more details <../module_details/splitters>`


:doc:`criterion <../module_details/criterions>`
""""""""""""""""""""""""""""""""""""""""""""""""""""""""
The criterion option is used to specify the loss function.
It is a dynamic option, however, it is not relying on abstractions.

Users can specify any native Torch or custom written loss functions.

:doc:`more details <../module_details/criterions>`



optimizer
""""""""""""""""""""""""""""""""""""""""""""""""""""""""
Is a dynamic option used to specify and configure the optimizer.
As any other dynamic option, the class is specified with the "type" argument, and everything else is injected into the constructor:

.. code-block:: javascript

    "optimizer": {
        "type": "torch.optim.Adam",
        "lr": 0.01,
        "weight_decay": 0.00056
    },

For a list of native PyTorch optimizers, please see the `pytorch documentation on optim <https://pytorch.org/docs/stable/optim.html>`_.
Of course, custom optimizers can be used as well.
As an example, we provide support for the recent AdaBelief optimizer:

.. code-block:: javascript

    "optimizer": {
        "type": "lib.model.optimizers.AdaBelief",
        "weight_decay": 0,
        "betas": [0.9, 0.999]
    },


scheduler
""""""""""

Schedulers are used to adjust the learning rate during training.
This is a dynamic option very similar to the criterion or the optimizer.

For a list of native Pytorch learning rate schedulers, please visit the `pytorch documentation <https://pytorch.org/docs/stable/optim.html#how-to-adjust-learning-rate>`_.

.. code-block:: javascript

    "scheduler": {
        "type": "torch.optim.lr_scheduler.OneCycleLR",
        "max_lr": 0.01,
        "epochs": 200,
        "pct_start": 0.3,
        "div_factor": 25,
        "final_div_factor": 1000
    },

is_stepwise_scheduler (default: ``True``)
""""""""""""""""""""""""""""""""""""""""""

A static field.
If true, we perform scheduler updates after every forward pass.
Otherwise, we perform the update after every epoch.

is_finetuning (default: ``False``)
"""""""""""""""""""""""""""""""""""

A static field.
This should remain ``False`` if one wishes to continue training after a reboot, and be set to ``True``
when we wish to train on a new dataset using a previous checkpoint.
When this option is ``True``, only model weights will be loaded, otherwise we
also load the optimizer, scheduler, and epoch tracking information.

output_path
""""""""""""

Points to the location where checkpoints will be saved to.

checkpoint_path (default: ``None``)
"""""""""""""""""""""""""""""""""""""

A static field marking the path to a checkpoint.
Some operations like single checkpoint evaluation or inference require a fixed checkpoint.
One can also specify a checkpoint path if they wish to continue training on a previous task, or for fine-tuning on another dataset.

threshold (default: ``0.5``)
"""""""""""""""""""""""""""""

Specifies what threshold to use when converting logits to predictions.
This is going to affect certain metrics (like accuracy) and predicted values (when running inference).

Note: The threshold is used only for classification tasks.

cross_validation_folds (default: ``5``)
""""""""""""""""""""""""""""""""""""""""""

How many folds to split the data into when performing cross-validation?

train_split (default: ``train``)
"""""""""""""""""""""""""""""""""

Specify which split to use for training.
This should be one of the keys specified in the ``splits`` option of the ``splitter``.

test_split (default: ``test``)
"""""""""""""""""""""""""""""""

Specify which split to use for evaluation and inference.
This should be one of the keys specified in the ``splits`` option of the ``splitter``.

train_metrics (default: ``[]``)
"""""""""""""""""""""""""""""""""

Specify which metrics to report during training.
This option is expected to be a list of strings, thus multiple metrics can be specified.
But please note that metric computations can slow down the training process.

List of metrics:

- Regression
    mae, mse, rmse, r2, pearson, spearman, kl_div, js_div,chebyshev, manhattan, rank_quality
- Classification
    roc_auc, pr_auc, accuracy, precision, recall, f1, cohen_kappa, jaccard


test_metrics (default: ``[]``)
""""""""""""""""""""""""""""""""

Specify which metrics to report during evaluation.
This option is expected to be a list of strings, thus multiple metrics can be specified.


epochs (default: ``200``)
""""""""""""""""""""""""""

The number of training iteration upon seeing all datapoints

batch_size (default: ``32``)
"""""""""""""""""""""""""""""""

The number of datapoints to use (in all operations) in a single iteration.

use_cuda (default: ``true``)
"""""""""""""""""""""""""""""""

If true, and if an NVIDIA graphics card is available, the model will use GPU acceleration.

cache_location (default: ``/tmp/federated/``)
"""""""""""""""""""""""""""""""""""""""""""""""

A folder where cached objects will be stored in.
It is recommended to monitor the size of this directory.

clear_cache (default: ``False``)
"""""""""""""""""""""""""""""""""""

When set to ``True``, cached data for the specific experiment will be flushed.

log_frequency (default: ``20``)
"""""""""""""""""""""""""""""""""

The number of iterations an update will be printed to the console when training the model.

log_level (default: ``info``)
""""""""""""""""""""""""""""""

How many logs should be printed.
The available options are: ``debug``, ``info``, ``warn``, ``error``, and ``critical``.

log_format (default: ``""``)
""""""""""""""""""""""""""""""

Can be used to include additional details for logged messages, like timestamps.

target_metric (default: ``roc_auc``)
"""""""""""""""""""""""""""""""""""""""""

Specify which metric to use as feedback for Bayesian optimization.
This option is also used when to find best performing checkpoints.

See `train_metrics` for a list of metrics

optuna_trials (default: ``1000``)
"""""""""""""""""""""""""""""""""""

Number of trials that should be performed when running Bayesian Optimization.


subset (default: ``None``)
""""""""""""""""""""""""""""

The subset is a static, but composite setting.
It expects a dictionary containing an ``id`` and a ``distribution`` field.

The option is used to run experiments on a subset of the whole dataset, and is very helpful for distributed learning experiments.
Otherwise, it provides little use, as the specific subsets can be obtained using the regular splitter functionality.

The ``distribution`` setting specifies a list of fractions the dataset should be
split into, and the expected value is a list of floating point values which sum up to 1.
The ``id`` setting specifies which subset should be used from the list of "distribution"s and is a 0-based index.

As an example, the below setting will split the dataset into 2 equal proportions, and will use the first half of the split for training.

.. code-block:: javascript

    "subset": {
        "id": 0,
        "distribution": [0.5, 0.5]
    }


observers (default: ``{}``)
""""""""""""""""""""""""""""

Observers are handlers which listen for and handle incoming events.
We set up various event dispatchers throughout the framework like before a checkpoint
is loaded, before training starts, or after training finished.
A full list of event dispatchers and their payload is listed in Table 3.2.

Event listeners watch the dispatchers and act on the payload.
Features like differential privacy are implemented entirely with observers.
As for user specified handlers, the ``add_sigmoid`` handler is the most useful ones,
which adds a sigmoid activation to the output of a model.
It should be attached to ``before_criterion``, and ``before_predict`` dispatchers.

.. code-block:: javascript

    "observers": {
        "before_criterion": ["lib.core.observers.AddSigmoidHandler"],
        "after_predict": ["lib.core.observers.AddSigmoidHandler"]
    },