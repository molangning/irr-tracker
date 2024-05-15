#!/usr/bin/env python3

import ftplib
import json
import os

from io import BytesIO
from lib import check_port, wrapped_requests, parse_ftp_list, extract_serial, parse_http_list

BASE_PATH = "sources/"

SOURCE_FILE = "registry-list.json"
RESOLVED_SOURCES_FILE = os.path.join(BASE_PATH, SOURCE_FILE)

REACHABLE_FILE = "reachable.json"
RESOLVED_REACHABLE_FILE = os.path.join(BASE_PATH, REACHABLE_FILE)

sources = json.load(open(RESOLVED_SOURCES_FILE))
servers = {}

def test_ftp(host, currentserial_file, name):
    
    try:
        dirlist = BytesIO()
    
        base_path = None
        if "/" in currentserial_file:
            base_path = currentserial_file.rsplit("/", 1)[0]

        ftp = ftplib.FTP(host, timeout=30)
        ftp.login()

        if base_path is not None:
            ftp.cwd(base_path)

        ftp.retrbinary("LIST", dirlist.write)
        dirlist = dirlist.getvalue()
        filelist = parse_ftp_list(dirlist, name)
        
        return bool(filelist["source_files"])

    except ConnectionError:
        print(f"[!] Connection error while getting from {host}")

    except Exception as e:
        print(f"[!] Error while getting from {host}")
        print(f"[!] {e}")

def test_https(host, currentserial_file, name):
        base_path = ""
        if "/" in currentserial_file:
            base_path = currentserial_file.rsplit("/", 1)[0]

        url = f"https://{host}/{base_path}"
        html = wrapped_requests(url)

        if html is None:
            return False

        filelist = parse_http_list(html, name)

        return bool(filelist["source_files"])

for source in sources:
    method = 0
    ftp_reachable = False
    https_reachable = False
    irr_avail = False
    name = source['name']

    if not source["ftp_site"]:
        print(f"[!] Skipping registry {source['name']} as no ftp sites defined.")
        continue

    hostname = source["ftp_site"][0].split("://", 1)[-1].split("/", 1)[0]
    serialnumber_file = extract_serial(source["ftp_site"], name)

    if check_port(hostname, 443):
        https_reachable = test_https(hostname, serialnumber_file, name)
    else:
        print(f'[!] {name} is NOT reachable through https port.')
    
    if https_reachable is False:
        print(f"[!] Unable to get https listing from {name}.")
    else:
        print(f'[+] {name} is available through https port, excellent.')

    if check_port(hostname, 21):
        ftp_reachable = test_ftp(hostname, serialnumber_file, name)
    else:
        print(f'[!] {name} is NOT reachable through ftp port.')

    if ftp_reachable is False:
        print(f"[!] Unable to get ftp listing from {name}.")
    else:
        print(f'[+] {name} is available through ftp port, excellent.')

    if https_reachable is not True and ftp_reachable is not True:
        print(f'[!] {name} has no reachable ports')

    servers.update({
        name: {
            "https_reachable": https_reachable,
            "ftp_reachable": ftp_reachable,
            "irr_db_available": https_reachable or ftp_reachable
        }
    })
    
json.dump(servers, open(RESOLVED_REACHABLE_FILE, "w"), indent=4)
print("[+] Wrote results to json file.")