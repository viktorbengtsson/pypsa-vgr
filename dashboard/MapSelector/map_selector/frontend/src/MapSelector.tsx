import React from 'react';
import SwedenMap from "./maps/Sweden/index"
import { IMap } from "./maps/types"

import {
  ComponentProps,
  withStreamlitConnection,
  StreamlitComponentBase,
  Streamlit,
} from "streamlit-component-lib"

interface State {
  selection: string[]
  geo_level: number
}

// Given a main geographical area within a specific country, we will return a geo that is the "key" used for the selection of the section within the geographical area

class MapSelector extends StreamlitComponentBase<State> {
  private map: IMap;
  private availableLevels: number[]
  private avalableLevel0Geos: string[]
  private avalableLevel1Geos: string[]
  private avalableLevel2Geos: string[]

  public constructor(props: ComponentProps) {
    super(props)

    let initial_geo: string | undefined = this.props.args["initial_geo"] as string
    const country = this.props.args["country"] as string
    let available_geo = (this.props.args["available_geo"] as string[])
    if (!initial_geo) {
      try {
        const urlParams = new URLSearchParams((window.top || window).location.search);
        debugger;
        initial_geo = urlParams.get('geo') ?? undefined;
      }
      catch {
        console.log("Could not access parent window")
      }
    }
    
    switch(country) {
      case "sweden":
        this.map = new SwedenMap({ mainGeo: this.props.args["main_geo"] as (string | undefined),  available_geo: available_geo });
        break;
      default:
        throw new Error(`Country map ${country} does not exist`)
    }
    
    this.availableLevels = []
    this.avalableLevel2Geos = available_geo.filter(g => g.length === 4)
    this.avalableLevel1Geos = available_geo.filter(g => g.length > 4)
    this.avalableLevel0Geos = available_geo.filter(g => g.length == 2)
    
    if (this.avalableLevel0Geos.length > 0) {
      this.availableLevels.push(0)
    }
    if (this.avalableLevel1Geos.length > 0) {
      this.availableLevels.push(1)
    }
    if (!!available_geo.find(g => g.length === 4)) {
      this.availableLevels.push(2)
    }

    const { selection, geo_level } = this.map.getSelection(initial_geo, this.availableLevels)

    this.state = { selection, geo_level: geo_level }
    const geo = this.map.getGeo(selection)
    Streamlit.setComponentValue(geo)
  }

  private clear = (): void => {
    const { geo_level } = this.state
    let newSelection: string[] = [] // = [this.map.mainGeo]
    if (geo_level === 1) {
      newSelection = [this.avalableLevel1Geos[0]] //.split("-")
    } else {
      newSelection = [this.avalableLevel2Geos[0]]
    }

    /*
    this.setState({ selection: newSelection }, () => {
      const geo = this.map.getGeo(newSelection);
      Streamlit.setComponentValue(geo)
    })
    */
    this.setState({ selection: newSelection }, () => {
      const geo = this.map.getGeo(newSelection);
      Streamlit.setComponentValue(geo);
    })

  }
  private deSelect = (code: string): void => {
    const { selection } = this.state
    const newSelection = [...selection]
    newSelection.splice(newSelection.indexOf(code) , 1)

    this.setState({ selection: newSelection }, () => {
      const geo = this.map.getGeo(newSelection);
      Streamlit.setComponentValue(geo)
    })

  }
  private selectAll = (): void => {
    const { geo, selection } = this.map.selectAll();

    this.setState({ selection: selection }, () => {
      Streamlit.setComponentValue(geo)
    })
  }

  private onSelectionChanged = (
    e: React.MouseEvent<SVGSVGElement, MouseEvent>
  ): void => {
    const { selection, geo_level } = this.state
    let newSelection = [...selection]
    const path = e.target as SVGPathElement
    path.classList.forEach((key, _) => {

      if (key.startsWith("section-")) {
        const val = key.substring("section-".length)

        /*const index = newSelection.indexOf(val);

        if (index === -1) {
          newSelection.push(val);
        } else {
          newSelection.splice(index, 1);
        }*/
        // Currently only selecting single item

        /*
        if (geo_level === 1) {
          const level1Area = this.avalableLevel1Geos.find(one => one.includes(val))
          if (level1Area) {
            newSelection = level1Area.split("-")
          }
        }
        else {
          newSelection = [val]
        }
        */
        if (geo_level === 0) {
          newSelection = [this.map.mainGeo];  // Ensure main geo is selected
        } else if (geo_level === 1) {
          const level1Area = this.avalableLevel1Geos.find((one) => one.includes(val));
          if (level1Area) {
            newSelection = level1Area.split("-"); // Select all Kommuner in the Förbund
          }
        } else {
          newSelection = [val];
        }        
      }
    })

    this.setState({ selection: newSelection }, () => {
      const geo = this.map.getGeo(newSelection);
      Streamlit.setComponentValue(geo)
    })
  }

  private onGeoLevelChanged = (
    e: React.ChangeEvent<HTMLSelectElement>
  ): void => {
    const newLevel = parseInt(e.target.value)
    let newSelection: string[] = [] // = [this.map.mainGeo]
    if (newLevel === 1) {
      newSelection = [this.avalableLevel1Geos[0]] //.split("-")
    } else if (newLevel === 2) {
      newSelection = [this.avalableLevel2Geos[0]]
    } else {
      newSelection = [this.map.mainGeo];  // Ensure main geo is selected when geo_level is 0
    }
    
    this.setState({ geo_level: newLevel, selection: newSelection }, () => {
      const geo = this.map.getGeo(newSelection);
      Streamlit.setComponentValue(geo)
    })
  }

  public render = (): React.ReactNode => {
    let { selection, geo_level } = this.state

    const selectedItems = this.map.getSelectionItems(selection, geo_level)
    const size = this.map.getSize()
    const levelSelector = geo_level === 0 ? "main" : "section"
    const MapComponent = this.map.Component

    return (
      <div style={{ position: "relative" }}>
        <style dangerouslySetInnerHTML={{__html:
        `  /* Make clear what is the main geo area */
           ${ `.map-selector .sections path.main-${this.map.mainGeo} { opacity: ${geo_level === 0 ? "1" : "0.2"}; stroke: black; }`}

           /* Make it clear what are the possible geo areas to select */
           ${ geo_level === 0 ? "" : (geo_level === 1 ? this.avalableLevel1Geos.map(g => g.split("-")).flat() : this.avalableLevel2Geos).map(g => `.map-selector .sections path.section-${g} { opacity: 1; pointer-events: auto; cursor: pointer }`).join(" ") }

           /* Mark the selected geo areas */
           ${ selection.map(s => {
                // Check if the selected item is the main geo (e.g., 14)
                if (s === this.map.mainGeo) {
                  return `.map-selector .sections path.main-${this.map.mainGeo} { fill: var(--primary-color); }`;
                }

                // Handle groups by splitting the string and generating selectors for each geo
                const parts = s.includes('-') ? s.split('-') : [s];
                return parts.map(part => `.map-selector .sections path.${levelSelector}-${part} { fill: var(--primary-color); }`).join(" ");
              }).join(" ") }
        `}}
        />
        <MapComponent onSelectionChanged={this.onSelectionChanged} width={size.width} height={size.height} viewBox={size.viewBox ?? ""} />
        <div className="sections" style={{ padding: "4px" }}>
          <div style={{ display: "flex", flexDirection: "row" }}>
            <div style={{ flex: 1, border: "1px solid rgba(0, 0, 0, 0.2)", borderRadius: "0.5rem", padding: "0.25rem", display: "flex", flexDirection: "row", gap: "0.25rem", flexWrap: "wrap", overflow: "auto", maxHeight: "5.5rem" }}>
              {selectedItems.map(i => {
                  return (<div key={`sel_${i.code}`} style={{ border: "1px solid rgba(0, 0, 0, 0.2)", borderRadius: "0.5rem", padding: "0.125rem 0.25rem", background: "var(--primary-color)", color: "white", cursor: "pointer" }} onClick={() => this.deSelect(i.code)}>{i.name}</div>)
              })}
            </div>
            {/*<div style={{ display: "flex", flexDirection: "column", border: "1px solid rgba(0, 0, 0, 0.2)", borderWidth: "1px 1px 1px 0", borderRadius: "0 0.5rem 0.5rem 0", cursor: "pointer" }}>
              <div style={{ padding: "0.15em 0.5rem", fontSize: "11px", lineHeight: "1.75rem" }} onClick={this.clear}>Rensa</div>
              <div style={{ padding: "0.15em 0.5rem", fontSize: "11px", borderTop: "1px solid rgba(0, 0, 0, 0.2)" }} onClick={this.selectAll}>Välj alla</div>
            </div>*/}
          </div>
        </div>
        {this.availableLevels.length > 0 && <select value={geo_level} style={{ position: "absolute", top: "0.75em", right: "1em", fontSize: "11px" }} onChange={this.onGeoLevelChanged}>
          {this.availableLevels.includes(0) && <option value="0">Län</option>}
          {this.availableLevels.includes(1) && <option value="1">Förbund</option>}
          {this.availableLevels.includes(2) && <option value="2">Kommun</option>}
        </select>
        }
      </div>
    )
  }
}

export default withStreamlitConnection(MapSelector)
