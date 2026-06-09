#!/bin/bash

set -euo pipefail

cd /home/morten/dev/livetree

python3 -m venv .venv
source .venv/bin/activate
pip install -e .
