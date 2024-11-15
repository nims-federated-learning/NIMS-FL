

Transformers
=============

Transformers are very similar to featurizers, expect they are applied to output features, and are generally used to normalize values.
Transformers are dynamic fields used to instantiate components extending ``lib.data.transformers.AbstractTransformer``.

Each transformer implements an "apply" and a "reverse" operation, which converts the values back after inference (for prediction only, does not apply to metrics).
Similar to featurizers, multiple transformers can be used in the same experiment

The following is an example of how to configure transformers

.. code-block:: javascript

    "transformers": [
        {"type": "log_normalize", "targets": [0, 2]},
        {"type": "standardize", "target": 1, "mean": 2.1863357142857143, "std": 1.203003713387104}
    ],

As a dynamic field, the transformer type is again specified with the "type" argument:

``log_normalize``:
    Converts the target to its log value.
    This transformer expects a ``targets`` argument, which is a list of (0-based) indices mapping to the "target_column_names" argument of the loader.
``min performs min-max normalization``:
    This transformer has a ``target`` argument similar to the log transformer, however, in this case, we expect a single value instead of a list.
    The "minimum" and "maximum" arguments are also mandatory, which should reflect the smallest and largest values recorded for the column/property.
``fixed``:
    Divides the target values by a fixed number.
    This transformer expects a ``targets`` argument, which is a list in this case.
    The "value" argument is used to specify the value used for the division.
``standardize``:
    Performs z-score normalization.
    This transformer has a ``target`` argument which is a single 0-based index (not a list).
    The "mean" and "std" options are also mandatory which denote the average value and the standard deviation for the target.
``cutoff``:
    Converts a continuous value to a discrete one, using a user-specified cutoff.
    Note that this operation is destructive and cannot be reversed.
    We expect a ``target`` argument with a single 0-based index, and a "cutoff" argument denoting the threshold for binarization.
