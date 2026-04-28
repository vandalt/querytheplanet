# Query the Planet

Query <whereistheplanet.com> from Python.

There is already [a Python version of whereistheplanet](https://github.com/semaphoreP/whereistheplanet),
but it is requires orbitize! and `git-lfs`, plus it is not available on PyPI.

This aims to be a lighter version with no dependencies that directly queries the website.
This means it does require a network connection.

## Installation

<!-- TODO: Add PyPI link -->
Install directly from PyPI:

```bash
python -m pip install querytheplanet
```

## Usage

### Command line

List available planets:

```bash
querytheplanet -l
```

Query one or more planet positions for today:

```bash
querytheplanet 51erib betapicb
```

Query the position of one or more planets for a given date:

```bash
querytheplanet 51erib betapicb --date 2026-05-01
```

Query the position of one or more planets for a multiple dates:

```bash
querytheplanet 51erib betapicb --date 2023-01-01 2026-05-01
```

Save the results to a CSV:

```bash
querytheplanet 51erib betapicb --date 2023-01-01 2026-05-01 --output results.csv
```

Display help:

```bash
querytheplanet -h
```

### From Python



## Development

To install for development, first clone the repository (or ideally your fork of it), e.g.:

```bash
git clone https://github.com/vandalt/querytheplanet.git
```

Then install with development dependencies in editable mode:

```bash
python -m pip install -e ".[dev]"
```

To run the tests, do:

```bash
python -m pytest
```
