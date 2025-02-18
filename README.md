# Generation Toolkit applied to Västra Götalandsregionen (VGR)

Generation Toolkit is a PyPSA-based toolkit for modelling electricity production for self-sufficiency in a geography. It forms part of a larger Energy Toolkit developed by AI Sweden together with partners.

> [!NOTE]
> This instance of Generation Toolkit (formerly PyPSA-VGR) is applied to VGR. It is the most complete prototype of Generation Toolkit. The frontend can be accessed at https://vgr.toolkit.energy/. The documentation in this document is likewise a prototype of the Generation Toolkit documentation.

## Description of the project

The Generation Toolkit was developed to help answer a simple question:

> What do we have to build in order to meet future electricity demand?

The toolkit can be used by regional and local stakeholders with an interest in or responsibility for energy, as well as by industry and the general public. The visual interface is designed to be easily accessible to anyone with a basic understanding of electricity production.

For more technically inclined users, the underlying power model and scenario generator can be modified. This allows the model to be adapted and scenarios to be conducted that reflect specific conditions in different locations, enabling in-depth analyses and tailored insights.

The toolkit has been developed with the following user groups in mind:
- Decision-makers (including the general public) who may not have specialized knowledge in the energy sector.
- Energy specialists who have a deeper understanding of energy-related issues but may lack detailed knowledge of power system optimization and analysis.
- Energy modelers who are experts in modeling power systems.

### Three main components

** 1. The generator **

** 2. The API **

** 3. The dashboard **

### Philosophy

Generation Toolkit follows the same philosophy as the other projects in the Energy Toolkit:

- **Open source** - The application code is free to use by private sector, academia, and public sector.
- **Useful** - The application targets a broad user base in a clear way.
- **Portable** - The application is easy to move, run on a local machine, or deploy in the cloud.
- **Secure** - The application is designed with security in mind and can be used with sensitive data.

### How the application works

1. The power system (demand, production, and storage) is modelled with PyPSA.
2. It takes input in the form of weather data, GIS data, and assumptions about costs, lifetimes, efficiencies, etc.
3. We define scenarios in a configuration as lists of parameter values (e.g. total yearly demand for each target year)
4. The generator runs all possible combinations of parameter values from the configuration and saves the results to csv files.
5. Each run of the generator is a PyPSA optimization of the power system. It derives the most cost-effective system (how much solar, wind, storage, etc.) to meet the demand given the assumptions and constraints.
6. The outout can be accessed from files or through an API in any number of applications.
7. The frontend of the application is a dashboard that visualizes some of the results in a more accessible way.

## Structure of the repo

- dashboard: contains the code for the Streamlit dashboard
- generator: contains the code to run all the scenarios and save results to files (will soon contain code to build the API)
- input: contains all the input required for running one or more scenarios
- library: contains general functions that can be used both by the generator and in notebooks
- notebooks: contains an example notebook
- api: empty at first, contains all the output data from running generator

## The generator

> [!NOTE]
> The generator configs currently run all combinations of parameters. This will be changed to a dictionary of parameters to run in future versions.

### General assumptions and constraints

The following assumptions, constraints, and simplifications are built into many different parts of the application:

- We use 3h as the base resolution for all data. This is done in order to keep the timeseries reasonable for running optimization on a normal laptop with an open-source solver.
- We use 2023 weather data and a 2023 load profile as the basis for generation and demand in the model.
- We do not model existing power production as power plant data is not readily available in Sweden. The model only focuses on new power production to meet future demand.
- We do not model the grid as grid data is not readily available in Sweden.

### The input (specific to the VGR instance)

#### Demand

The VGR project uses a load profile based on the 2023 data from Svenska Kraftnät for the geography SE3. Hourly mean load data is downloaded, normalized (total energy per year is 1) and resampled to 3h resolution. This load profile can then be multiplied by total early energy and used in the model.

> [!NOTE]
> The `input/demand` folder also contains scripts for generating load profiles for counties and municipalities for a range of years. These scripts and the output is not used in the current instance.

#### GIS data

The model uses open source GIS data, stored in the `input/geo` folder, for:

- Economic zone delimitations
- The municipalities of Sweden (GeoJSON) https://data.opendatasoft.com/explore/dataset/georef-sweden-kommun%40public/map/?disjunctive.lan_code&disjunctive.lan_name&disjunctive.kom_code&disjunctive.kom_name&sort=year&location=8,56.03216,14.2218&basemap=jawg.streets
- Land use in the municipalities of Sweden
- Corine land cover for Sweden https://land.copernicus.eu/pan-european/corine-land-cover/clc2018?tab=download

#### Weather data

- Weather data is downloaded from the [ERA5](https://cds.climate.copernicus.eu/cdsapp#!/dataset/reanalysis-era5-single-levels?tab=overview) dataset.
- We use 2023 weather data for the model.
- The weather data resolution is 3h.

#### Renewables data

The Atlite library is used to generate solar and wind generation data for the model. The output is capacity factor timeseries for each rewnewable generator (solar, onwind, offwind) per geography. This capacity factor represents the mean fraction of the nominal power that could be generated given weather conditions for each 3h interval in the year.

> E.g. if the capcity factor for a given 3h interval is 0.3 and the size of the generator is 10 MW then the mean generation in that 3h interval is 3 MW.

#### Other assumptions

Cost, lifetime, efficiency, etc. are all collected in the `input/assumptions.csv` file. The assumptions are dated, allowing for calculations that infer evolution of cost over time, and for present value calculations.

- The majority of assumptions are taken from the Danish Energy Agency, a common source of assumptions in the academic literature.
- Costs are in 2020 euros.
- Lifetime is in years.
- Efficiency is a dimensionless fraction.

Generators have five categories of parameters:

- Capital costs: the cost of building the generator
- FOM (Fixed Operation and Maintenance costs): the yearly cost of operating and maintaining the generator
- VOM (Variable Operation and Maintenance costs): the cost of operating and maintaining the generator per MWh
- Lifetime: the lifetime of the generator
- Unit size: the size in MW of the generator (e.g. a turbine)

For more details on the assumptions, see the `input/assumptions.csv` file.

### The model (specific to the VGR instance)

The model consists of a PyPSA network object that is built in the `model/network_core.py` file. It has the following structure:

- Load bus:
  - Load: Total load in the geography
  - Backstop: 
  - Market: Electricity bought on the market to meet peak demand
- Renewables bus
  - Solar: Solar generation (generator)
  - Onwind: Onshore wind generation (generator)
  - Offwind: Offshore wind generation (generator) (if offwind is used)
- Battery bus
  - Battery storage (store)
  - Inverter battery charge (link)
  - Interver battery discharge (link)

- Turbine bus (if H2 or biogas is used)
- H2 bus (if H2 is used)


> [!IMPORTANT]
> The model does not include any existing power production. We interpret this constraint as the model only focusing on new power production to meet future demand (i.e. on top of existing demand). The reason for this simplication is to avoid the length and complicated process of identifying and modelling existing power plants accurately.

> [!IMPORTANT]
> Currently the model does not include a representation of the grid. No constraints on transmission or distribution are included, nor any losses. The reason for this simplication is the lack of accessible grid data in Sweden.

> [!INFO]
> In future versions the model will include approximations of the grid, as well as existing power production.

## The API

The API is file-based and can be used locally, served with e.g. Node.js, or deployed to API services in e.g. Azure or AWS.

## The dashboard (frontend)

The current frontend is a dashboard built with [Streamlit](https://streamlit.io/). It can be run locally, deployed for free to Streamlit Community Cloud, or deployed to a cloud service like Azure or AWS.

> [!NOTE]
> The frontend will be completely replaced in future versions of Generation Toolkit. The new frontend will allow for more clear data storytelling with the output of the generator. It will be built with Svelte and follow the design system of the Energy Toolkit.

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
