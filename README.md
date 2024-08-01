# A power modeler for Västra Götalandsregionen (VGR)

Version: WIP

This repo contains software for modelling expanded energy production in Västra Götalandsregionen (VGR) of Sweden. 

1. One or more scenarios can be built, run, and analyzed in jupyter notebooks using the helper functions in /library
2. Data for a large set of scenarios can be generated with the scripts in /generator. This data can be accessed through files (and soon a simple API)
3. The data from generator can be analyzed in the Streamlit dashboard in /dashboard

The overall purpose is to allow the user to build and tinker with a general model in a notebook, and then feed this model into a generator to run scenarios that can then be analyzed through an API or in our dashaboard.

## Structure of the repo

- dashboard: contains the code for the Streamlit dashboard
- generator: contains the code to run all the scenarios and save results to files (will soon contain code to build the API)
- input: contains all the input required for running one or more scenarios
- library: contains general functions that can be used both by the generator and in notebooks
- notebooks: contains an example notebook
- output: empty at first, contains all the output data from running generator


## Installation
PyPSA-VGR relies on a set of other Python packages to function.
We recommend using the package manager [mamba](https://mamba.readthedocs.io/en/latest/) to install them and manage your environments.
For instructions for your operating system follow the `mamba` [installation guide](https://mamba.readthedocs.io/en/latest/installation/mamba-installation.html).
You can also use ``conda`` equivalently.

The package requirements are curated in the [environment.yaml](https://github.com/PyPSA/pypsa-vgr/blob/prototype/environment.yaml) file.
The environment can be installed and activated using

```bash
mamba env create -f environment.yaml
mamba activate pypsa-vgr
```

The equivalent commands for `conda` would be
```bash
conda env create -f environment.yaml
conda activate pypsa-vgr
```

## Dev environment setup
To avoid Jupyter output to be included in commits, run following command:
```bash
git config filter.strip-notebook-output.clean jupyter "nbconvert --ClearOutputPreprocessor.enabled=True --to=notebook --stdin --stdout --log-level=ERROR"
```

## Data used in scripts

### GIS data
- Swedish municipals (GeoJSON) https://data.opendatasoft.com/explore/dataset/georef-sweden-kommun%40public/map/?disjunctive.lan_code&disjunctive.lan_name&disjunctive.kom_code&disjunctive.kom_name&sort=year&location=8,56.03216,14.2218&basemap=jawg.streets
- Landuse (in data/geo/corine.tif) comes from https://land.copernicus.eu/pan-european/corine-land-cover/clc2018?tab=download (License: Citation...)
- Here are the set of codes that define the type of land use: https://land.copernicus.eu/content/corine-land-cover-nomenclature-guidelines/docs/pdf/CLC2018_Nomenclature_illustrated_guide_20190510.pdf. Main categories (and relevant ones) are:
  - Class 1: Artificial areas (Urban, Industrial, Mines, Non-agricultural vegetative areas)
  - Class 2: Agricultural areas
  - Class 3: Forest and semi-natural areas
  - Class 4: Wetlands
  - Class 5: Water bodies
    - Class 5.1: Inland waters
    - Class 5.2: Warine waters
- Here are the codes used in the exclusions for these: https://collections.sentinel-hub.com/corine-land-cover/readme.html
