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

- Swedish minicipals (GeoJSON)
https://data.opendatasoft.com/explore/dataset/georef-sweden-kommun%40public/map/?disjunctive.lan_code&disjunctive.lan_name&disjunctive.kom_code&disjunctive.kom_name&sort=year&location=8,56.03216,14.2218&basemap=jawg.streets

- Landuse (in data/geo/corine.tif): https://land.copernicus.eu/pan-european/corine-land-cover/clc2018?tab=download (License: Citation...)

