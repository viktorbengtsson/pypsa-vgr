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
    getSelection: (initial_geo: string | undefined) => string[]
    getGeo: (selection: string[]) => string
    getSelectedSections: (selection: string[]) => {
        section_code: string,
        section_name: string,
    }[]
}

export type ISection = { 
    main_code: string,
    main_name: string,
    section_code: string,
    section_name: string
}