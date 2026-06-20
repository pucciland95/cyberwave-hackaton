# Cyberwave Hackaton

A Python project built with [Poetry](https://python-poetry.org/) using the [cyberwave](https://pypi.org/project/cyberwave/) library.

---

## Prerequisites

Make sure you have the following installed on your machine before starting:

- **Python 3.10 or higher** — [Download here](https://www.python.org/downloads/)
- **Poetry** — Python dependency and packaging manager

### Installing Poetry

Open a terminal and run:

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

---

## Getting the Project

Clone this repository:

```bash
git clone https://github.com/Pucciland95/cyberwave-hackaton.git
cd cyberwave-hackaton
```

---

## Installing the Project

From inside the project folder, run:

```bash
poetry install
```

This will:
1. Create an isolated virtual environment automatically
2. Install all dependencies (including `cyberwave`) at the exact versions locked in `poetry.lock`

---

## Running the Project

To run any Python script inside the Poetry-managed environment, prefix your command with `poetry run`:

```bash
poetry run python src/cyberwave_hackaton/main.py
```

Or activate the virtual environment with:

```bash
eval $(poetry env activate)
```

---

## Project Structure

```
cyberwave-hackaton/
├── src/
│   └── cyberwave_hackaton/   # Main package — put your code here
│       └── __init__.py
├── pyproject.toml            # Project configuration and dependencies
├── poetry.lock               # Locked dependency versions (do not edit manually)
└── README.md
```

---

## Adding New Dependencies

If you need to add a new library, run:

```bash
poetry add <library-name>
```

Then commit both `pyproject.toml` and `poetry.lock` so everyone gets the same versions.
