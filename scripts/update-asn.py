#!/usr/bin/env python3

import gzip
import os

dbs = []

for root, _, files in os.walk("sources/dbs"):
    for i in files:
        if i.endswith(".db.gz") or i.endswith("route6.gz") or i.endswith("route.gz"):
            dbs.append(os.path.join(root, i))

for i in dbs:
    with gzip.open(i, "rb") as f:
        print(f.read(10))
    exit()