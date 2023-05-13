INIT_COMMAND = (
    "`polyaxon init -p PROJECT_NAME [--polyaxonfile] [--git-connection] [--git-url]`"
)

DEFAULT_IGNORE_LIST = """
./.polyaxon
.git
.eggs
eggs
lib
lib64
parts
sdist
var
*.pyc
*.swp
.DS_Store
__pycache__/
.pytest_cache/
*.py[cod]
*$py.class
.mypy_cache/
.vscode/
.mr.developer.cfg
.pydevproject
.project
.settings/
.idea/
.DS_Store
# temp files
*~
# C extensions
*.so
# Distribution / packaging
.Python
dist/
pydist/
*.egg-info/
.installed.cfg
*.egg
# PyInstaller
*.manifest
*.spec
# IPython Notebook
.ipynb_checkpoints
# pyenv
.python-version
"""

INIT_FILE_PATH = "polyaxonfile.yaml"

INIT_FILE_TEMPLATE = """---
version: 1.1
kind: component
run:
  kind: job
  container:
    # image: # image to use
    # command: # Command to use
"""

INIT_FILE = "init"
DEBUG_FILE = "debug"
