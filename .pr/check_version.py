import json
import sys
import tomllib

errors = []

with open("pyproject.toml", "rb") as f:
    pyproject =