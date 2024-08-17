import React from 'react';
import { IMap, MapProps, ISection } from '../types';
import { sections, main_areas, level1_areas } from "./sections"
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
  
  getSelection (initial_geo: string | undefined, availableLevels: number[]) {
    if (initial_geo) {
      const selection = [initial_geo]
      return { selection, geo_level: selection.length === 0 ? (availableLevels[0] ?? 0) : selection[0].length > 7 ? 1 : 0 }
    }
    else {
      return { selection: [this.mainGeo], geo_level: 0 }
    }
  }

  getGeo (selection: string[]) {
    if (selection.length === 0) {
      return this.mainGeo;
    }
    else if (selection.length > 1) {
      return this.mainGeo + "-" + selection.join("-")
    }
    else if (this.mainGeo === selection[0]) {
      return this.mainGeo
    }

    return this.mainGeo + "-" + selection[0]
  }

  getSelectionItems (selection: string[], geo_level: number) {
    switch (geo_level) {
      case 0:
        const mainGeoName = main_areas.find(a => a.code === this.mainGeo)?.name ?? "Unknown"
        return [{ code: this.mainGeo, name: mainGeoName }]
      case 1:
        const code = selection.join("-")
        const level1GeoName = level1_areas.find(a => a.code === code)?.name ?? "Unknown"
        return [{ code: code, name: level1GeoName }]
      case 2:
        return sections
          .filter(g => selection.includes(g.section_code))
          .sort((s1, s2) => selection.findIndex(s => s === s1.section_code) - selection.findIndex(s => s === s2.section_code))
          .map(x => ({ code: x.section_code, name: x.section_name }))
      default:
        return []
    }
  }
}

export default MapSweden
