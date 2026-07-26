# Openmanic Docker Image


### Building the Source
Before building the image, you need to have built the unmanic python package (the Python package/import name stays `unmanic` for compatibility - see [metadata.py](../unmanic/metadata.py)):
```bash
rm -rfv ./build && rm -fv ./dist/unmanic-*
python3 -m build --no-isolation --skip-dependency-check --wheel
python3 -m build --no-isolation --skip-dependency-check --sdist
```


### Building the image
Simply run this command from the root of the project:
```bash
docker build -f ./docker/Dockerfile -t openmanic/openmanic:staging -t ghcr.io/nyakuoff/openmanic:staging .
```
