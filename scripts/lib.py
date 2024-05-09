#!/usr/bin/env python3

from datetime import datetime
from decimal import Decimal

import re
import requests
import socket

GENERIC_HTML_SEARCH = re.compile(r'<a href="(.+?)(?<!\/)">.+?<\/a> +(.+?) (.+?) +([0-9]+)')
FINAL_HTML_SEARCH = re.compile(r'<a href="(.+?)">.+?<\/a>.+?">(.+?) ([0-9:]+).*"> *(.*?) *<')
TRANSITIONAL_HTML_SEARCH = re.compile(r'<a href="(.+?)">.+?"right">([0-9-]+) ([0-9:]+).+"> *(.+?) *?<\/td>')

DATE_NUMBER_ONLY = "%Y-%m-%d %H:%M"
DATE_WITH_MONTH = "%d-%b-%Y %H:%M"

def wrapped_requests(url, headers={}, json=False):
    for i in range(1,4):
        try:
            r = requests.get(url,headers=headers, timeout=60)
    
            if r.status_code==200:
                # print("[+] Got %s successfully!"%(url))
                break
    
            if i==3:
                print("[!] Failed to get %s."%(url))
                exit(2)
    
            print("[!] Getting %s failed(%i/3)"%(url,i))

        except requests.exceptions.Timeout:
            print("[!] Timed out getting %s (%i/3)"%(url,i))

        except requests.exceptions.SSLError:
            return None
        
        except Exception as e:
            print(f"[!] Got exception {e}")
            return None
    
    if json is True:
        try:
            return r.json()
        except:
            print("[+] Converting response to dictionary failed")
            return
    else:
        return r.text
    
def download_file(url, fp, headers={}):
    for i in range(1,4):
        try:
            r = requests.get(url, headers=headers, stream=True, timeout=60)
    
            if r.status_code!=200:
                print("[!] Getting %s failed(%i/3)"%(url,i))
                continue
    
            if i==3:
                print("[!] Failed to get %s."%(url))
                exit(2)

            for chunk in r.iter_content(chunk_size=4096):
                fp.write(chunk)

            return True

        except requests.exceptions.Timeout:
            print("[!] Timed out getting %s (%i/3)"%(url,i))

        except requests.exceptions.SSLError:
            return False
        
        except Exception as e:
            print(f"[!] Got exception {e}")
            return False
            
def check_port(host, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(10)

    try:
        s.connect((host, port)) 
        return True
    
    except Exception:
        return False
    
def extract_serial(urls, name):
    current_serial_file = ""
    root_path = ""
    
    for i in urls:

        path = i.split("://", 1)[-1].split("/", 1)[1].rstrip("/")

        if "CURRENTSERIAL" in path:
            current_serial_file = path 

        elif path.endswith(".gz"):
            continue

        else:    
            root_path = path

    if not current_serial_file:
        current_serial_file = f"{root_path}/{name.upper()}.CURRENTSERIAL"
    
    return current_serial_file.lstrip("/")

def conv_suffix(number):
    if number.isnumeric():
        return int(number)
    
    number = number.lower()

    if number[-1] == "k":
        return int(Decimal(number[:-1]) * 10 ** 3)

    if number[-1] == "m":
        return int(Decimal(number[:-1]) * 10 ** 6)
    
    if number[-1] == "g":
        return int(Decimal(number[:-1]) * 10 ** 6)

    raise ValueError

def parse_ftp_list(dirlist, name):
    name = name.lower()

    filelist = {
        "source_files": [],
        "mirrored_files": [],
        "total_size": 0
    }

    for dirline in dirlist.decode().splitlines():
        fileinfo = [x for x in dirline.split(" ") if x]
        
        if fileinfo[0] == "total":
            continue

        if fileinfo[0] == "d":
            continue

        filename = fileinfo[8]

        if filename.lower().startswith("readme"):
            continue

        if fileinfo[7].isnumeric():
            date = int(datetime.timestamp(datetime.strptime(" ".join([fileinfo[5], fileinfo[6].zfill(2), fileinfo[7]]), "%b %d %Y")))
        else:
            date = int(datetime.timestamp(datetime.strptime(" ".join([fileinfo[5], fileinfo[6].zfill(2), fileinfo[7]]), "%b %d %H:%M").replace(year=datetime.today().year)))
        
        filesize = int(fileinfo[4])

        filelist["total_size"] += filesize

        if filename.split(".", 1)[0].lower().startswith(name):
            filelist["source_files"].append([filename, filesize, date])
        else:
            filelist["mirrored_files"].append([filename, filesize, date])

    return filelist

def parse_http_list(dirlist, name):
    name = name.lower()

    filelist = {
        "source_files": [],
        "mirrored_files": [],
        "total_size": 0
    }

    firstline = dirlist.split("\n", 1)[0]

    if "Final" in firstline:
        dirlist = FINAL_HTML_SEARCH.findall(dirlist)
    elif "Transitional" in firstline:
        dirlist = TRANSITIONAL_HTML_SEARCH.findall(dirlist)
    else:
        dirlist = GENERIC_HTML_SEARCH.findall(dirlist)

    if len(dirlist) == 0:
        print(f"[!] Unable to get directory listing from {name}")
        return False 

    date = " ".join(dirlist[0][1:3])
    
    for i in ["-", ":", " "]:
        date = date.replace(i, "")

    if date.isnumeric():
        dirlist = [[x[0], conv_suffix(x[3]), int(datetime.timestamp(datetime.strptime(" ".join(x[1:3]).strip(), DATE_NUMBER_ONLY)))] for x in dirlist if x[1]]
    else:
        dirlist = [[x[0], conv_suffix(x[3]), int(datetime.timestamp(datetime.strptime(" ".join(x[1:3]).strip(), DATE_WITH_MONTH)))] for x in dirlist if x[1]]

    for entry in dirlist:
        filename = entry[0]

        if filename.lower().startswith("readme"):
            continue

        filelist["total_size"] += entry[1]

        if filename.split(".", 1)[0].lower().startswith(name):
            filelist["source_files"].append([filename, entry[1], entry[2]])
        else:
            filelist["mirrored_files"].append([filename, entry[1], entry[2]])

    return filelist