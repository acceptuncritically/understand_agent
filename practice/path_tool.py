from pathlib import Path
import os

def get_project_root():
    current_dir=os.path.dirname(os.path.abspath(__file__))
    current_root=os.path.dirname(current_dir)
    return current_root
def get_abs_path(relative_path):
    return str(Path(get_project_root())/relative_path.lstrip("/\\"))
