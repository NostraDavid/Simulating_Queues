# Simulating Queues

## Original README

This is some legacy code that I'm leaving up in case anyone wants it **but** you
should use [ciw](https://github.com/ciwpython/ciw) which has excellent
documentation here: http://ciw.readthedocs.io/en/latest/

## Python3 upgrade (2024-09-17)

The original code was Python2 (from around 2012), so I converted it to Python3.

I also added a `pyproject.toml` file to track the dependencies, using Astral's
`uv` (`0.4.10`) package manager.

## IDE

I'll presume you're running on `Linux` with `vscode` as editor, as it supports
Jupyter notebooks very well.

## Virtual Environment Setup

To create a virtual environment, just run `uv sync`. No need to install a
certain Python version; `uv` will take care of that.

Then you can just `source .venv/bin/activate` on the terminal, or `ctrl-shift-p`
-> `Python: Select Interpreter` and then select `./.venv/bin/python` as virtual
env within `vscode`.

## Run the code

### `MM1Q.py`

You should see some nice buttons above `# %%` (that's the magic incantation for
Jupyter notebooks, within a Python file; no need for actual `ipynb` files).
Click on them to run the code. Do note that only one of the code cells will run
at a time.

You can also `shift-enter` to run-and-go-to-the-next-cell, or `ctrl-enter` to run-and-stay-in-the-same-cell.

### `graphicalMM1.py`

You run this one as a regular script; There's should be a play button at the
upper right corner. There's a dropdown to select debug mode as well (make sure
to set some breakpoints). You can also press `F5` to run the file.
