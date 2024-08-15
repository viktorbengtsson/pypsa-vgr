import React, { Component } from 'react';
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
}

// Given a main geographical area within a specific country, we will return a geo that is the "key" used for the selection of the section within the geographical area

class MapSelector extends StreamlitComponentBase<State> {
  private map: IMap;

  public constructor(props: ComponentProps) {
    super(props)

    const initial_geo = this.props.args["initial_geo"] as string
    const country = this.props.args["country"] as string
    const available_geo = this.props.args["available_geo"] as string[]

    switch(country) {
      case "sweden":
        this.map = new SwedenMap({ mainGeo: this.props.args["main_geo"] as (string | undefined),  available_geo });
        break;
      default:
        throw new Error(`Country map ${country} does not exist`)
    }
    
    let selection: string[] = []
    console.log(initial_geo)
    selection = this.map.getSelection(initial_geo)

    this.state = { selection }
    Streamlit.setComponentValue(this.map.getGeo(selection))
  }

  private clear = (): void => {
    this.setState({ selection: [] }, () => {
      const geo = this.map.getGeo([]);
      Streamlit.setComponentValue(geo)
    })

  }
  private deSelect = (kom_code: string): void => {
    const { selection } = this.state
    const newSelection = [...selection]
    newSelection.splice(newSelection.indexOf(kom_code) , 1)

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
    const { selection } = this.state
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

        newSelection = [val]
      }
    })

    this.setState({ selection: newSelection }, () => {
      const value = this.map.getGeo(newSelection);
      Streamlit.setComponentValue(value)
    })
  }

  public render = (): React.ReactNode => {
    let { selection } = this.state

    const selectedSections = this.map.getSelectedSections(selection)
    const size = this.map.getSize()

    return (
      <>
        <style dangerouslySetInnerHTML={{__html:
        `  ${ `.map-selector .sections path.main-${this.map.mainGeo} { opacity: 0.2; stroke: black; }`}
           ${ selection.map(s => `.map-selector .sections path.section-${s} { fill: rgb(93, 156, 199) }`).join(" ") }
           ${ this.map.available_geo.filter(g => g.length > 2).map(g => `.map-selector .sections path.section-${g} { opacity: 1; pointer-events: auto; cursor: pointer }`).join(" ") }
        `}}
        />
        <this.map.Component onSelectionChanged={this.onSelectionChanged} width={size.width} height={size.height} viewBox={size.viewBox ?? ""} />
        <div className="sections">
          <div style={{ display: "flex", flexDirection: "row" }}>
            <div style={{ flex: 1, border: "1px solid rgba(0, 0, 0, 0.2)", borderRadius: "0.5rem 0 0 0.5rem", padding: "0.5rem", display: "flex", flexDirection: "row", gap: "0.5rem", flexWrap: "wrap", overflow: "auto", maxHeight: "5.5rem" }}>
              {selectedSections.map(i => {
                  return (<div key={`sel_${i.section_code}`} style={{ border: "1px solid rgba(0, 0, 0, 0.2)", borderRadius: "0.5rem", padding: "0.25rem 0.5rem", background: "rgb(93, 156, 199)", color: "white", cursor: "pointer" }} onClick={() => this.deSelect(i.section_code)}>{i.section_name}</div>)
              })}
            </div>
            <div style={{ display: "flex", flexDirection: "column", border: "1px solid rgba(0, 0, 0, 0.2)", borderWidth: "1px 1px 1px 0", borderRadius: "0 0.5rem 0.5rem 0", cursor: "pointer" }}>
              <div style={{ padding: "0.15em 0.5rem", fontSize: "12px", lineHeight: "2.5rem" }} onClick={this.clear}>Rensa</div>
              {/*<div style={{ padding: "0.15em 0.5rem", fontSize: "12px", borderTop: "1px solid rgba(0, 0, 0, 0.2)" }} onClick={this.selectAll}>Välj alla</div>*/}
            </div>
          </div>
        </div>
      </>
    )
  }
}

export default withStreamlitConnection(MapSelector)
