# A power model for Västra Götalandsregionen (VGR)

Version: WIP

This repo contains a pypsa model for expanded renewable energy production in VGR.

## Assumptions

- This simplified model contains no network. All constituent parts of the network connect to a single main bus.
- We are implementing four different types of generators
  1. Solar plant
  2. Wind park (onshore)
  3. Wind park (offshore)
  4. (Hydrogen gas turbine)

## Data used in scripts

- Swedish municipals (GeoJSON)
https://data.opendatasoft.com/explore/dataset/georef-sweden-kommun%40public/map/?disjunctive.lan_code&disjunctive.lan_name&disjunctive.kom_code&disjunctive.kom_name&sort=year&location=8,56.03216,14.2218&basemap=jawg.streets


### Landuse

Landuse (in data/geo/corine.tif) comes from https://land.copernicus.eu/pan-european/corine-land-cover/clc2018?tab=download (License: Citation...)

Here are the set of codes that define the type of land use:
https://land.copernicus.eu/content/corine-land-cover-nomenclature-guidelines/docs/pdf/CLC2018_Nomenclature_illustrated_guide_20190510.pdf

Main categories (and relevant ones) are:
- Class 1: Artificial areas (Urban, Industrial, Mines, Non-agricultural vegetative areas)
- Class 2: Agricultural areas
- Class 3: Forest and semi-natural areas
- Class 4: Wetlands
- Class 5: Water bodies
  - Class 5.1: Inland waters
  - Class 5.2: Warine waters
Here are the codes used in the exclusions for these:
https://collections.sentinel-hub.com/corine-land-cover/readme.html




## Installation
PyPSA-VGR relies on a set of other Python packages to function.
We recommend using the package manager [mamba](https://mamba.readthedocs.io/en/latest/) to install them and manage your environments.
For instructions for your operating system follow the `mamba` [installation guide](https://mamba.readthedocs.io/en/latest/installation/mamba-installation.html).
You can also use ``conda`` equivalently.

The package requirements are curated in the [envs/environment.yaml](https://github.com/PyPSA/pypsa-vgr/blob/prototype/envs/environment.yaml) file.
The environment can be installed and activated using

```bash
mamba env create -f envs/environment.yaml
mamba activate pypsa-vgr
```

The equivalent commands for `conda` would be
```bash
conda env create -f envs/environment.yaml
conda activate pypsa-vgr
```


## Dev environment setup
To avoid Jupyter output to be included in commits, run following command:
```bash
git config filter.strip-notebook-output.clean jupyter "nbconvert --ClearOutputPreprocessor.enabled=True --to=notebook --stdin --stdout --log-level=ERROR"
```