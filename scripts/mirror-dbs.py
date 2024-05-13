#!/usr/bin/env python3

import ftplib
import json
import os
import time

from io import BytesIO
from lib import wrapped_requests, extract_serial, parse_ftp_list, parse_http_list, download_file, test_gz

BASE_PATH = "sources/"

SOURCE_FILE = "registry-list.json"
RESOLVED_SOURCES_FILE = os.path.join(BASE_PATH, SOURCE_FILE)

REACHABLE_FILE = "reachable.json"
RESOLVED_REACHABLE_FILE = os.path.join(BASE_PATH, REACHABLE_FILE)

SERIAL_FILE = "serial-numbers.json"
RESOLVED_SERIAL_FILE = os.path.join(BASE_PATH, SERIAL_FILE)

EXCLUDE_FILE = "exclude.json"
RESOLVED_EXCLUDE_FILE = os.path.join(BASE_PATH, EXCLUDE_FILE)

DB_OUTPUT = os.path.join(BASE_PATH, "dbs")

reachable = json.load(open(RESOLVED_REACHABLE_FILE))
sources = json.load(open(RESOLVED_SOURCES_FILE))
serial_numbers = json.load(open(RESOLVED_SERIAL_FILE))

exclude = []

if "USE_EXCLUDE" in os.environ:
    print("[!] Using excludes")
    exclude = json.load(open(RESOLVED_EXCLUDE_FILE))

servers = []

def makedir_if_not_exists(path):
    if not os.path.isdir(path):
        os.makedirs(path)

def mirror_ftp(host, currentserial_file, name):
    
    try:
        serial_number = BytesIO()
        dirlist = BytesIO()
        base_path = None

        makedir_if_not_exists(os.path.join(DB_OUTPUT, name))

        if "/" in currentserial_file:
            base_path, currentserial_file = currentserial_file.rsplit("/", 1)

        ftp = ftplib.FTP(host, timeout=30)
        ftp.login()

        if base_path is not None:
            ftp.cwd(base_path)

        ftp.retrbinary("LIST", dirlist.write)
        dirlist = dirlist.getvalue()
        filelist = parse_ftp_list(dirlist, name)

        ftp.retrbinary(f'RETR {currentserial_file}', serial_number.write)
        serial_number = serial_number.getvalue().decode().strip()

        if name in serial_numbers.keys() and serial_numbers[name] == serial_number:
            print(f"[+] Skipping {name} as serial number matches")
            return True

        for entry in filelist["source_files"]:

            filename = entry[0]

            if filename.lower().endswith("currentserial"):
                continue

            print(f"[+] Downloading {filename} from {host} using ftp")

            f = open(os.path.join(DB_OUTPUT, name, filename), "wb")
            ftp.retrbinary(f'RETR {filename}', f.write)
            f.close()

            print(f"[+] Downloaded {filename} from {host} using ftp")

            serial_numbers[name] = serial_number

        return True

    except ConnectionError:
        print(f"[!] Connection error while getting from {host}")

    except Exception as e:
        print(f"[!] Error while getting from {host}")
        print(f"[!] {e}")

def mirror_https(host, currentserial_file, name):
    base_path = ""
    serial_number = ""

    makedir_if_not_exists(os.path.join(DB_OUTPUT, name))

    if "/" in currentserial_file:
        base_path, currentserial_file = currentserial_file.rsplit("/", 1)

    url = f"https://{host}/{base_path}"
    
    serial_number = wrapped_requests(f"{url}/{currentserial_file}")

    if serial_number is None:
        return False
    
    serial_number = serial_number.strip()

    if name in serial_numbers.keys() and serial_numbers[name] == serial_number:
        print(f"[+] Skipping {name} as serial number matches")
        return True
    
    html = wrapped_requests(url)

    if html is None:
        return False
    
    filelist = parse_http_list(html, name)

    for entry in filelist["source_files"]:

        filename = entry[0]

        if filename.lower().endswith("currentserial"):
            continue

        print(f"[+] Downloading {filename} from {host} using https")

        f = open(os.path.join(DB_OUTPUT, name, filename), "wb")
        download_file(f"{url}/{filename}", f)
        f.close()

        print(f"[+] Downloaded {filename} from {host} using https")

        serial_numbers[name] = serial_number

    return True

for source in sources:
    server = []
    name = source['name']
    mirrored = False

    if not source["ftp_site"]:
        print(f"[!] Skipping registry {name} as no ftp sites defined.")
        continue

    hostname = source["ftp_site"][0].split("://", 1)[-1].split("/", 1)[0]
    serialnumber_file = extract_serial(source["ftp_site"], name)

    if name in exclude:
        print(f"[!] Skipping {name} as it is in excludes")
        continue

    if reachable[name]["https_reachable"] is True:
        print(f'[+] Trying to mirror {name} through https')

        for i in range(1, 4):
            downloaded = mirror_https(hostname, serialnumber_file, name)
            valid = test_gz(name)

            if downloaded is True:
                if valid is not False:
                    mirrored = True
                    print(f'[+] Finished mirroring {name} through https')
                    break
                else:
                    print(f"[!] Mirrored {name} through https but downloaded files are invalid ({i}/3)")
            else:
                print(f'[+] Failed to mirror {name} through https ({i}/3)')
    
            time.sleep(5)

    if mirrored is False and reachable[name]["ftp_reachable"] is True:
        print(f'[+] Trying to mirror {name} through ftp')

        for i in range(1, 4):
            downloaded = mirror_ftp(hostname, serialnumber_file, name)
            valid = test_gz(name)

            if downloaded is True:
                if valid is not False:
                    mirrored = True
                    print(f'[+] Finished mirroring {name} through ftp')
                    break
                else:
                    print(f"[!] Mirrored {name} through ftp but downloaded files are invalid ({i}/3)")
            else:
                print(f'[+] Failed to mirror {name} through ftp ({i}/3)')

            time.sleep(5)

    if mirrored is False:
        print(f'[!] Unable to mirror with {name}')
        continue

    json.dump(serial_numbers, open(RESOLVED_SERIAL_FILE, "w"), indent=4)

    

    