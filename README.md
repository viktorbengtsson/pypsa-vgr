# The Energy Toolkit

The energy toolkit enables users to:

1. Use/expand a simple model for energy generation
2. Run large numbers of scenarios to analyze options
3. Access the resulting data through a file or web API
4. Display results in a ready-made dashboard

The toolkit provides tools for a wide range of users to analyze and communicate possibilities for renewable energy-independent futures.

## Bring your own data

This repository does not contain the basic data needed to run a first model. For initial use you are required to provide the following:

1. Power demand (3h interval) for one year
2. Electricity price
...

TODO: continue writing this

## Structure of the repo

- api: empty at first, contains all the output data from running generator
- dashboard: contains the code for the Streamlit dashboard
- generator: contains the code to run all the scenarios and save results to files (will soon contain code to build the API)
- input: contains all the input required for running one or more scenarios
- model: contains general functions that can be used both by the generator and in notebooks
- workspace: contains an example notebook

## Installation
PyPSA-VGR relies on a set of other Python packages to function. We recommend using the package manager [mamba](https://mamba.readthedocs.io/en/latest/) to install them and manage your environments. For instructions for your operating system follow the `mamba` [installation guide](https://mamba.readthedocs.io/en/latest/installation/mamba-installation.html). You can also use ``conda`` equivalently.

The package requirements are curated in the [environment.yaml](https://github.com/PyPSA/pypsa-vgr/blob/prototype/environment.yaml) file. The environment can be installed and activated using:

```bash
mamba env create -f environment.yaml
mamba activate energy-toolkit
```

The equivalent commands for `conda` would be
```bash
conda env create -f environment.yaml
conda activate energy-toolkit
```

## Dev environment setup
To avoid Jupyter output to be included in commits, run following command:
```bash
git config filter.strip-notebook-output.clean jupyter "nbconvert --ClearOutputPreprocessor.enabled=True --to=notebook --stdin --stdout --log-level=ERROR"
```