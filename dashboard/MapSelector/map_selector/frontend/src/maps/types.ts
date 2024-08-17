export interface MapProps {
    onSelectionChanged: (e: React.MouseEvent<SVGSVGElement, MouseEvent>) => void;
    width: number;
    height: number;
    viewBox: string;
}

export interface IMap {
    Component: React.ComponentType<MapProps>;
    mainGeo: string;
    available_geo: string[];
    setMainGeo: (newMainGeo: string) => void;
    getSize: () => { width: number, height: number, viewBox: string | undefined }
    selectAll: () => { geo: string, selection: string[] }
    getSelection: (initial_geo: string | undefined, availableLevels : number[]) => { selection: string[], geo_level: number }
    getGeo: (selection: string[]) => string
    getSelectionItems: (selection: string[], geo_level: number) => {
        code: string,
        name: string,
    }[]
}

export type ISection = { 
    main_code: string,
    main_name: string,
    section_code: string,
    section_name: string
}