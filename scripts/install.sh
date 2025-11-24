#!/usr/bin/env bash
set -e

python -m pip install --upgrade pip

pip install -r data_pipeline/requirements.txt
pip install -r api/requirements.txt

echo "✅ Dependencies installed."
