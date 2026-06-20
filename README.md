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

After installation, close and reopen your terminal, then verify it works:

```bash
poetry --version
```

> On **Windows**, if `poetry` is not found after installing, you may need to add it to your PATH. The installer will tell you the exact path to add.

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

You do **not** need to run `pip install` manually — Poetry handles everything.

---

## Running the Project

To run any Python script inside the Poetry-managed environment, prefix your command with `poetry run`:

```bash
poetry run python src/cyberwave_hackaton/main.py
```

Or open an interactive shell inside the environment:

```bash
poetry shell
python src/cyberwave_hackaton/main.py
```

---

## Project Structure

```
cyberwave-hackaton/
├── src/
│   └── cyberwave_hackaton/   # Main package — put your code here
│       └── __init__.py
├── tests/                    # Put your tests here
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

---

## Troubleshooting

| Problem | Solution |
|---|---|
| `poetry: command not found` | Restart your terminal or follow the [Poetry docs](https://python-poetry.org/docs/#installation) for your OS |
| `python: command not found` | Install Python 3.10+ from [python.org](https://www.python.org/downloads/) |
| Wrong Python version in use | Run `poetry env use python3.10` to force the correct version |
