#!/usr/bin/bash

set -euxo pipefail

PYTHONUNBUFFERED=1 
./scripts/pull-sources.py
./scripts/test-dbs.py
./scripts/update-readme.py
./scripts/mirror-dbs.py