import sys
from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need
# fine tuning.
build_options = {'packages': [], 'excludes': []}

base = 'Win32GUI' if sys.platform=='win32' else None

executables = [
    Executable('src/client/run_client.py', base=base, target_name = 'run_client')
]


setup(
    name='gb-pychat-client',
    version = '0.1.1',
    description='JIM Client package',
    options = {'build_exe': build_options},
    executables = executables
)
