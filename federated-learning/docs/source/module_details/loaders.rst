
Loaders
=========

The following is an example configuration of a CSV loader for the AMES dataset:

.. code-block:: javascript

    "loader": {
        "type": "csv",
        "input_path": "data/input/tox21/raw/tox21.csv",
        "input_column_names": ["smiles"],
        "target_column_names": [
            "NR-AR", "NR-AR-LBD", "NR-AhR", "NR-Aromatase",
            "NR-ER", "NR-ER-LBD", "NR-PPAR-gamma", "SR-ARE",
            "SR-ATAD5", "SR-HSE", "SR-MMP", "SR-p53"
        ]
    },

The loader option is used to configure how raw data files are loaded.
It is a dynamic field used to instantiate components which extend ``lib.data.loaders.AbstractLoader``.

We support 3 loaders at this time, which are specified in the ``type``:

* **csv**: For comma-separated values
* **excel**: For Excel spreadsheets (only one spreadsheet can be loaded at a time)
* **sdf**: For SDF files (where the whole dataset is stored in a single SDF file)

The additional arguments are identical for the most part at this time.
One exception is the **excel** loader, which accepts a numeric ``sheet_index`` to specify which sheet to load (numbering starts from 0 for the first sheet in the file).
Otherwise, all loaders are expected to receive 3 fields:

``input_path``:
    The relative or absolute path to the input file

``input_column_names``:
    A list of columns or properties which should be mapped as input features

``target_column_names``:
    A list of columns or properties which should be mapped as output features
