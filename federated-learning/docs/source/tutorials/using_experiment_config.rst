
Rerun experiments using provided config
=========================================


In the delivery package, there is `experiment_configs` folder containing all config
used for training the experiments.

.. note::

    There might be some path mismatch in the config between your environment and
    the one we used for training. We tried to fix those in the `experiment_configs`
    but the config present in `result` are still using our path system.


Cross validation experiments
""""""""""""""""""""""""""""""

Most experiment are federated-learning cross validation experiment.

To run those use you need to update the file `experiment_configs/mila_config/mean_cv.json`
and indicate which experiment you would like to rerun. For all our experiment
the `seed` parameter was 42 and the `num_folds` was 10.
You only need to modify `cfg_dir` and provide a path to a directory inside `mila_config`
as well as `output_path` to indicate where results will be stored.

.. note::

    Experiment base on material splitting are in the categorical folder since
    they are using the categorical splitter.

For example if you provide the following config:

.. code:: javascript

    {
        "cfg_dir": "experiment_configs/mila_config/base/epochs/2",
        "seed": 42,
        "num_folds": 10,
        "output_path": "result_dir_path",
        "log_level": "DEBUG",
        "save_results": false
    }

And run:

.. code:: none

    nims-federated-learning mean_cv experiment_configs/mila_config/mean_cv.json

It will launch the server based on the config inside the directory and launch both
client as well.
It will repeat the process 10 times for each fold. So there will be a total of
10 servers and 20 clients created. The 10 runs does not run in parallel.

At the end the mean result of each run will be saved inside a pickle file called
``result_pickle.pkl``. You can load it to review the result.

An example of result format, each element in the list correspond to the result of one fold:

.. code:: python

    {'log10timetorupture[h]':
    [
        0.22755610241596613,
        0.276156495748355,
        0.2662610935919585,
        ...
        0.25868318230217774
    ]
    }

If `save_results` is set to true, the best checkpoints of each fold training as
well as the test set inference of all folds will be generated in `output_path`.
For an example you can look into the `results` folder which contains this type of
results for the material splitting experiments.


.. note::

    For categorical experiment if you want to rerun some experiment without mean_cv
    set up, you might have to change the configuration.
    `See splitters information for more details <../modules_details/splitters>`

