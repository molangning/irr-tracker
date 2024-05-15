#!/usr/bin/env python3

import gzip
import json
import os

from lib import parse_whois_entries

BASE_PATH = "sources/"
RESOLVED_IPV4_FILE = os.path.join(BASE_PATH, "asn_ipv4.json")
RESOLVED_IPV6_FILE = os.path.join(BASE_PATH, "asn_ipv6.json")
dbs = []

for root, _, files in os.walk("sources/dbs"):
    for i in files:
        if i.endswith(".db.gz") or i.endswith("route6.gz") or i.endswith("route.gz"):
            dbs.append(os.path.join(root, i))

def get_ranges(entries):
    if "origin" not in entries.keys():
        return "", "", ""
    
    v4 = ""
    v6 = ""
    
    if "route" in entries.keys():
        v4 = entries["route"].decode()

    if "route6" in entries.keys():
        v6 = entries["route6"].decode()

    return entries["origin"].decode(), v4, v6

buffer = []
ipv4 = {}
ipv6 = {}

for i in dbs:
    print(f"[+] Processing {i}")

    for line in gzip.open(i, "rb"):
        if line == b"\n":
            origin, v4, v6 = get_ranges(parse_whois_entries(buffer))
            if v4:
                if origin not in ipv4.keys():
                    ipv4[origin] = set()
                ipv4[origin].add(v4)

            if v6:
                if origin not in ipv6.keys():
                    ipv6[origin] = set()
                ipv6[origin].add(v6)

            buffer = []
            
        buffer.append(line)

for i in ipv4.keys():
    ipv4[i] = sorted(ipv4[i])

for i in ipv6.keys():
    ipv6[i] = sorted(ipv6[i])

json.dump(ipv4, open(RESOLVED_IPV4_FILE, "w"), indent=4)
json.dump(ipv6, open(RESOLVED_IPV6_FILE, "w"), indent=4)