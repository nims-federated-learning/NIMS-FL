# Overview

This repository contains code for a Federated Learning study and inludes content copyrighted by NIMS.
Code content is based on a version of kmol (https://github.com/elix-tech/kmol)

## Content of the repository

You can find in the deliverables the following files and folders:

-  federated-learning (folder)

    :   Holds the project code.

-  
    docs (folder)

    :   Contains a .pdf and .HTML version of the documentation.

-   experiment_configs (folder)

    :   Contains all experiment configs necessary to rerun our
        experiments.

-   README.md (file)

    :   Quick guide to the project manipulation, subset of report.pdf.

## Installation

Use the provided conda snapshot:
```bash
conda env create -f environment.yml  # first time only
conda activate federated
bash install_additional_dependencies.sh  # first time only
```

## Command line

There are two commands line input possible:

-   `nims-federated-learning-base`
-   `nims-federated-learning`

### nims-federated-learning-base

This command is used for standard training (not federated-learning) and
optimization. There is a variety of commands possible.

It expects 2 arguments:

``` none
nims-federated-learning-base {job} {config}
```

Where `job` is one of the task detail below and `config` the path to the
model configuration.

#### `train`

Run a standard training base on the configuration provided.

#### `eval`

Launch evaluation of the model and return the target metric for the
[checkpoint_path] provided.

#### `mean_cv`

Run cross validation for the given config and return the mean average of
the target metric.

#### `predict`

Run inference on the dataset [test_split] and save result in
a [predictions.csv] file in the [output_path]
directory.

#### `optimize`

Run optimization with optuna base on the configuration provided

More detail on optimisation runs in the full documentation.

#### `find_best_checkpoint`

Find the best checkpoint base on the [output_path] and
[epochs] parameters. It will evaluate all checkpoint in the
directory until provided [epochs] number and return the best
one as well as it\'s target metrics.

### nims-federated-learning

This command is used for federated-learning training.

It expects 2 arguments:

``` none
nims-federated-learning {job} {config}
```

Where `job` is one of the three tasks `server`, `client` or `mean_cv`
and `config` the path to the expected config format to the task. See the
expected format in the full documentation.

#### `server`

Launch a server node (should always be the first node to be launched).

#### `client`

Launch a client node

#### `mean_cv`

Wrapper around multiple launchs for both server and clients. It will
launch [num_folds] number of experiments and save all
results and predictions to the [output_path].

This is a scenario only useful for testing different models and should
be run on only on one computer since one program manages clients and
server. This is due to the fact that when splitting the dataset, we must
have the full dataset at hand to make the different folds. And all
clients must split the dataset in the exact same way.

# Configuration Overview

There are two mains sets of configuration. One is for the use of
`nims-federated-learning-base` command line argument, whereas for `nims-federated-learning`
both type are needed.

## Model Configuration

Configuration used to make a standard training. So it provides
information about the splitter, the optimizer, etc.

More details in the full documentation

## Mila Configuration (Federated learning)

There is three set of configuration.

-   Server configuration:

    :   Used to start a server node

-   Client configuration:

    :   Used to start a client node

-   Mean_cv configuration:

    :   Used in parallel with Server and Client config to launch a cross
        validation experiment.
        This can only be used on one machine where the dataset is being
        split across clients nodes and the folds are managed between
        each run.

More details in the full documentation

# Configuration Examples

In the delivery package, there is [experiment_configs]
folder containing all config examples for this project.

::::

## Cross validation experiments

To run those use you need to update the file
[experiment_configs/mila_config/mean_cv.json] and indicate
which experiment you would like to rerun. For all our experiment the
[seed] parameter was 42 and the [num_folds] was
10. You only need to modify [cfg_dir] and provide a path to
a directory inside [mila_config] as well as
[output_path] to indicate where results will be stored.

Experiment base on material splitting are in the categorical folder
since they are using the categorical splitter.
::::

For example if you provide the following config:

``` javascript
{
    "cfg_dir": "experiment_configs/mila_config/base/epochs/2",
    "seed": 42,
    "num_folds": 10,
    "output_path": "result_dir_path",
    "log_level": "DEBUG",
    "save_results": false
}
```

And run:

``` none
nims-federated-learning mean_cv experiment_configs/mila_config/mean_cv.json
```

It will launch the server based on the config inside the directory and
launch both client as well. It will repeat the process 10 times for each
fold. So there will be a total of 10 servers and 20 clients created. The
10 runs does not run in parallel.

At the end the mean result of each run will be saved inside a pickle
file called `result_pickle.pkl`. You can load it to review the results.

An example of results format, each element in the list correspond to the
result of one fold:

``` python
{'log10timetorupture[h]':
[
    0.22755610241596613,
    0.276156495748355,
    0.2662610935919585,
    ...
    0.25868318230217774
]
}
```

If [save_results] is set to true, the best checkpoints of
each fold training as well as the test set inference of all folds will
be generated in [output_path]. For an example, you can look
into the [results] folder which contains this type of
results for the material splitting experiments.

For categorical experiments, if you want to rerun some experiments
without mean_cv set up, you might have to change the configuration. [See
splitters information for more details
\<../modules_details/splitters\>]

