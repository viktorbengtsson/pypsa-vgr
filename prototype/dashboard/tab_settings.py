import os
import sys
from data_loading import _read_config_definition, _read_constants, _update_constants

parent_directory = os.path.abspath('..')
sys.path.append(parent_directory)

from scenarios import load_config_scenarios

def _option_changed(CONFIG_NAME, code, value):
    _update_constants(CONFIG_NAME, code, value)

def render_settings(st_obj, CONFIG_NAME):
    st_obj.write(f"Config file used: {CONFIG_NAME}.json")

    CONFIG_DEFINITION = _read_config_definition(CONFIG_NAME)
    CONSTANTS = _read_constants(CONFIG_NAME)
    
    [combinations, keys] = load_config_scenarios(CONFIG_DEFINITION.pop("scenarios", None))

    st_obj.header("Konstanter")
    for idx, combination in enumerate(combinations):
        code = keys[idx]["code"]
        current = CONSTANTS.get(code)

        if current is not None:
            st_obj.subheader(code)
            for option in combination:
                checked = str(option) == str(current)
                st_obj.checkbox(f"{str(option)}", value=checked, key=f"{code}:{option}", on_change=_option_changed, args=(CONFIG_NAME, code, str(option)))
