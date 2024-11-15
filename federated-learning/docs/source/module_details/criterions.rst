Criterions
==========

The criterion option is used to specify the loss function.
It is a dynamic option, however, it is not relying on abstractions.

Users can specify any native Torch or custom written loss functions:

.. code-block:: javascript

    "criterion": {
        "type": "torch.nn.BCEWithLogitsLoss"
    },

We also provide a custom-built masked loss function, which wraps around a regular loss function, but ignores missing labels.
Using the masked loss is easy with dependency injection:

.. code-block:: javascript

    "criterion": {
        "type": "lib.model.criterions.MaskedLoss",
        "loss": {"type": "torch.nn.BCEWithLogitsLoss"}
    },

As a dynamic setting, of course, users can specify any additional input arguments for their loss function.
For a list of all criterions, we point readers to the `pytorch documentation on loss function <https://pytorch.org/docs/stable/nn.html#loss-functions>`_.
