#!/usr/bin/env bash
set -euo pipefail

python -m analyser.cli init-db
python -m analyser.cli serve
