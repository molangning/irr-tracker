#!/usr/bin/env python3

import json
import os

from lib import wrapped_requests

BASE_PATH = "sources/"

HISTORY_FILE = "history.json"
SOURCE_FILE = "registry-list.json"

RESOLVED_HISTORY_FILE = os.path.join(BASE_PATH, HISTORY_FILE)
RESOLVED_SOURCES_FILE = os.path.join(BASE_PATH, SOURCE_FILE)

IRR_NET_RAW_FILE = "https://raw.githubusercontent.com/irr-net/irr-net.github.io/main/src/content/registry-list.json"
IRR_NET_API_HASH_ENDPOINT = "https://api.github.com/repos/irr-net/irr-net.github.io/git/trees/main:src%2Fcontent%2F"

remote_file_hash = ""
history = {}

if os.path.isfile(RESOLVED_HISTORY_FILE):
    history = json.load(open(RESOLVED_HISTORY_FILE))     
else:
    print("[!] History file not found.")

print("[+] Checking registry list")
sources_hashes = wrapped_requests(IRR_NET_API_HASH_ENDPOINT, json=True)
print("[+] Got registry list hash")

for file in sources_hashes["tree"]:
    if file["path"] == SOURCE_FILE:
        remote_file_hash = file["sha"]

if remote_file_hash == "":
    print("[!] Unable to retrieve file hash from remote.")

if RESOLVED_SOURCES_FILE in history.keys() and history[RESOLVED_SOURCES_FILE] == remote_file_hash:
    print("[+] File exists and hashes matches! Nothing to do.")
    exit()

print("[+] Updating file from remote.")
open(RESOLVED_SOURCES_FILE, "w").write(wrapped_requests(IRR_NET_RAW_FILE)) 

history[RESOLVED_SOURCES_FILE] = remote_file_hash    
json.dump(history, open(RESOLVED_HISTORY_FILE, "w"), indent=4)
