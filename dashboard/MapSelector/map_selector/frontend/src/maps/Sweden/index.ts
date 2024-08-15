import React from 'react';
import { IMap, MapProps, ISection } from '../types';
import { sections, main_areas } from "./sections"
import MapComponent from "./MapComponent"

class MapSweden implements IMap {
  public Component: React.ComponentType<MapProps>;
  public mainGeo: string;
  public available_geo: string[];

  constructor(props: { mainGeo: string | undefined, available_geo: string[] }) {

    this.available_geo = props.available_geo
    this.mainGeo = props.mainGeo || "14"

    this.Component = MapComponent
  }

  private geoToSelection: (geo: string) => string[] = (geo: string) => {
    return geo === this.mainGeo ? [] : [geo]
  }
  private selectionToGeo: (selection: string[]) => string = (selection: string[]) => {
    return selection.length === 0 ? this.mainGeo : selection[0]
  }

  setMainGeo (newMainGeo: string) {
    this.mainGeo = newMainGeo
  }

  getSize () {
    switch (this.mainGeo) {
      case "14":
        return { width: 400, height: 300, viewBox: "0 460 110 110" }
    }

    return { width: 290, height: 700, viewBox: undefined }
  }
  

  selectAll () {
    return { geo: this.mainGeo, selection: [] }
  }
  
  getSelection (initial_geo: string | undefined) {
    return initial_geo ? this.geoToSelection(initial_geo) : []
  }

  getGeo (selection: string[]) {
    if (selection.length === 0) {
      return this.mainGeo;
    }
    return selection[0]
  }

  getSelectedSections (selection: string[]) {
    return sections
      .filter(g => selection.includes(g.section_code))
      .sort((s1, s2) => selection.findIndex(s => s === s1.section_code) - selection.findIndex(s => s === s2.section_code))
  }
}

export default MapSweden
