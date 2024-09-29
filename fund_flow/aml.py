from config import *
from typing import *
import requests
from common import log
from model import AddrInfo, AddrCategories

amlBaseUrl = "https://aml.blocksec.com/api/aml/v2/addresses"
addrCategories = AddrCategories()
known_addr_path = "./addr_info/known/{}.log"
bypass_addr_path = "./addr_info/bypass/{}.log"

def query_aml(conf:Config, chain:str, address:List[str]):
    addresses = ",".join(address)
    query_url = f'{amlBaseUrl}/{chain}/{addresses}'
    headers = {
        'API-KEY':conf.config["AmlApiKey"]
    }
    try:
        response = requests.get(query_url, headers=headers)
        response.raise_for_status()
    except Exception as e:
        log("./aml_error.log", ERROR=e, URL=query_url)
        return []
    return response.json()["data"]

def extract_account_info(data:Dict) -> AddrInfo:
    if not data.get("is_address_valid") or not data.get("labels"):
        return None
    raw_labels = data.get("labels")
    name_tag = raw_labels.get("name_tag")
    category = None
    if not name_tag:
        if data.get("is_contract") and raw_labels.get("contract_info"):
            name_tag = raw_labels.get("contract_info").get("contract_name") or raw_labels.get("contract_info").get("token_name")
        elif raw_labels.get("others"):
            name_tag = raw_labels.get("others")[0].get("label")
        elif raw_labels.get("entity_info") and raw_labels.get("entity_info")[0].get("entity"):
            name_tag = raw_labels.get("entity_info")[0].get("entity")
            category = raw_labels.get("entity_info")[0].get("category")
        elif raw_labels.get("property_info") and raw_labels.get("property_info")[0].get("address_property"):
            name_tag = raw_labels.get("property_info")[0].get("address_property")
            category = raw_labels.get("property_info")[0].get("category")
        else:
            return None
    if not name_tag:
        return None
    if "swap" in name_tag.lower() or "1inch" in name_tag.lower() or "exchange" in name_tag.lower() or "curve" in name_tag.lower():
        category = addrCategories.swap   
    elif "bridge" in name_tag.lower():
        category = addrCategories.bridge
    elif "phish" in name_tag.lower():
        category = addrCategories.phishing

    return AddrInfo(data.get("chain").lower(), data.get("address").lower(), name_tag, category, data.get("is_contract"))

import json
import time
from common import dump
import os
def check_accounts(dir_path:str):
    conf = Config("config.yaml")
    file_list = sorted(os.listdir(dir_path))
    if "Stargate" in dir_path:
        file_list = file_list[1:]
    for file_path in file_list:
        info_file_path = "./addr_info/known/eth.log"  # replace the path with your local address info file.
        # load exsiting addrs
        exist_addresses = load_exist_addr()

        records_file_path = os.path.join(dir_path, file_path)
        # load raw data
        with open(records_file_path, "r") as file:
            lines = file.readlines()

        # delete the first "["
        if lines and lines[0].startswith("[["):
            lines[0] = lines[0][1:]
        modified = ''.join(lines)
        data = json.loads(modified)

        # extract toAddress
        to_addresses = []
        for entry in data:
            transfers = entry.get("transfers", [])
            for transfer in transfers:
                to_address = transfer.get("toAddress")
                if to_address:
                    to_addresses.append(to_address)
        to_addresses = list(set(to_addresses)-set(exist_addresses))
        infos = {}
        for i in range(0, len(to_addresses), 3):
            batch = to_addresses[i:i+3]
            data = query_aml(conf, "eth", batch)
            for d in data:
                if extracted := extract_account_info(d):
                    infos[extracted.address] = extracted
            time.sleep(5)
        if len(infos) > 0:
            dump(infos, info_file_path)

def load_exist_addr(info_file_path:str = "./addr_infos.log") -> Set:
    index = -1
    with open(info_file_path, "r") as file:
        try:
            f = json.load(file)
        except Exception as e:
            if json.decoder.JSONDecodeError:
                index = int(str(e).split()[3])
    if index > -1:
        with open(info_file_path, "r") as file:
            lines = file.readlines()
        if index < len(lines):
            del lines[index-1]
            lines[index - 2] = lines[index - 2].rstrip() + ",\n"

        with open(info_file_path, 'w') as file:
            file.writelines(lines)
        f = json.loads(''.join(lines))
    return set(f.keys())
    
# return swap, known, bypass
def load_known_addrs(chain="", info_file_path:str = "./addr_info/known/{}.log", bypass_addr_file="./addr_info/bypass/{}.log") -> (Set, Set, Set):
    info_file_path = info_file_path.format(f'{chain}')
    bypass_addr_file = bypass_addr_file.format(f'{chain}')
    swap_addresses,known_addresses, bypass_addrs = set(), dict(), set()
    if os.path.isfile(info_file_path):
        with open(info_file_path, "r") as file:
            f = json.load(file)
        known_addresses = f
        swap_addresses = set([addr_info["address"] for addr_info in f.values() if addr_info.get("category") == addrCategories.swap])
    if os.path.isfile(bypass_addr_file):
        with open(info_file_path, "r") as file:
            f = json.load(file)
        bypass_addrs = set(f)
    return swap_addresses, known_addresses, bypass_addrs

