#!/usr/bin/bash

set -euxo pipefail

export PYTHONUNBUFFERED=1
./scripts/pull-sources.py
./scripts/test-dbs.py
./scripts/update-readme.py
USE_EXCLUDE=1 ./scripts/mirror-dbs.py
./scripts/update-asn.py