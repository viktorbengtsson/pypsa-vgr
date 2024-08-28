import sys
from pathlib import Path

root_path = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(root_path))

import paths

def delete_file(path):
    if path.exists():
        path.unlink()
    else:
        print(f"{path} does not exist")

