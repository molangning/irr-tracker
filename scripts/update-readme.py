#!/usr/bin/python3

import os
import re
import json

print("[+] Readme updater")

CHECK_MARK_EMOJI=":white_check_mark:"
CROSS_MARK_EMOJI=":negative_squared_cross_mark:"
DETAILS_ANCHOR="<!--- details anchor -->"
DETAILS_ANCHOR_REGEX=r"%s.*?%s"%(DETAILS_ANCHOR,DETAILS_ANCHOR)
DETAILS_TABLE_HEADER="""
| Source | FTP available | HTTPS available | IRR DB available
| --- | --- | --- | --- |
"""
DETAILS_TABLE_FORMAT="| %s | %s | %s | %s |"

BASE_PATH = "sources/"

REACHABLE_FILE = "reachable.json"
RESOLVED_REACHABLE_FILE = os.path.join(BASE_PATH, REACHABLE_FILE)

reachable = json.load(open(RESOLVED_REACHABLE_FILE))

output_table = DETAILS_TABLE_HEADER

for i in reachable.keys():
    ftp = CROSS_MARK_EMOJI
    https = CROSS_MARK_EMOJI
    irr_avail = CROSS_MARK_EMOJI

    if reachable[i]["ftp_reachable"]:
        ftp = CHECK_MARK_EMOJI

    if reachable[i]["https_reachable"]:
        https = CHECK_MARK_EMOJI
    
    if reachable[i]["irr_db_available"]:
        irr_avail = CHECK_MARK_EMOJI

    output_table += DETAILS_TABLE_FORMAT % (i, ftp, https, irr_avail) + "\n"

output_table = DETAILS_ANCHOR + output_table + DETAILS_ANCHOR

readme_contents = open("README.md").read()

if not re.search(DETAILS_ANCHOR_REGEX,readme_contents,flags=re.DOTALL):
    print("[!] Error: No details anchor found!")
    exit(2)

readme_contents = re.sub(DETAILS_ANCHOR_REGEX,output_table,readme_contents,count=1,flags=re.DOTALL)
open("README.md","w").write(readme_contents)

print("[+] Wrote README.md!")