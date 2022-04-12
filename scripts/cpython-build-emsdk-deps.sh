

# ../../devices/x86_64/usr/bin/python3-wasm -mpip install .
# not working because python startup is skipped

export PYSETUP="$HOST_PREFIX/bin/python3-wasm setup.py install  --single-version-externally-managed --root=/"

