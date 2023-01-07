import sys
from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need
# fine tuning.
build_options = {'packages': [], 'excludes': []}

base = 'console'
if sys.platform == "win32":
    base = "Win32GUI"

executables = [
    Executable('src/server/run_server_gui.py', base=base, target_name = 'run_server_gui'),
    Executable('src/server/run_server_cli.py', base=base, target_name = 'run_server_cli'),
]


setup(
    name='gb-pychat-server',
    version = '0.1.1',
    description='JIM Client package',
    options = {'build_exe': build_options},
    executables = executables
)
