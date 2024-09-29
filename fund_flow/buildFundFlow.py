from typing import List
from datetime import datetime
from config import *
from common import *
from model import *
import json
import geth
import random
import db
import os

RawTopicLen = 66
RawStrLen = 64

ERC20TransferEvent = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
NativeTokenAddress = "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee"
ZeroTokenAddress = "0x0000000000000000000000000000000000000000"
WethAddress =  "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"
NativeName = "native"

all_token_list = dict()
all_decimals_list = dict()
all_price_list = dict()
bypass_token = dict()
all_decimals_file_path = "the file recording all token decimals"
all_price_file_path = "the file recording all token prices"
bypass_token_file_path = "the file recording tokens "

WETHs = ["0xdebb1d6a2196f2335ad51fbde7ca587205889360", "0xbdc8fd437c489ca3c6da3b5a336d11532a532303", WethAddress, "0x121ab82b49b2bc4c7901ca46b8277962b4350204", "0xdeaddeaddeaddeaddeaddeaddeaddeaddead0000",
         "0xbd83010eb60f12112908774998f65761cf9f6f9a", "0x7ceb23fd6bc0add59e62ac25578270cff1b9f619", "0x0615dbba33fe61a31c7ed131bda6655ed76748b1", "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
         "0x74b23882a30290451a17c44f4f05243b6b58c76d", "0x965f84d915a9efa2dd81b653e3ae736555d945f4", "0x1dd9e9e142f3f84d90af1a9f2cb617c7e08420a4", "0x0230219b25395f14b84cf4dcd987e2daf5a71e4b", 
         "0x2ac03bf434db503f6f5f85c3954773731fc3f056", "0xb153fb3d196a8eb25522705560ac152eeec57901", "0x82af49447d8a07e3bd95bd0d56f35241523fbab1"]


class FundFlowBuilder:
    def __init__(self, config:Config, price_info: Dict[str, List[PriceInfo]]) -> None:
        self.config = config

    # return List fundflow & should update tokens
    def build_real_fund_flow(self, native_token_address:str, wrapped_native_token_address:str, e:Tx, chain:str, ts:str|datetime) -> (List[FundFlow], List[str]):
        res:List[FundFlow]=[]
        if int(e.value) != 0:
            e.internals.append(
                InternalTx(
                    e.blockNumber, "", e.from_, e.to, e.value, e.gas, e.gasPrice
                )
            )

        # Process native token
        ret = self.process_native_token(native_token_address, wrapped_native_token_address, e.internals)
        res.extend(ret)

        # Extract ERC20 token transfer event
        ret = self.process_erc20(wrapped_native_token_address, e.logs)
        res.extend(ret)

        should_update_tokens = List[str]
        for r in res:
            token = wrapped_native_token_address if r.token == NativeTokenAddress else r.token
            token = SynapseUSD.get(r.token) or token
            decimals, price, value, if2 = agg_transfer_things(self.config, r.raw_amount, chain, token, ts)
            r.value = value
            r.decimals = decimals
            r.price = price
            if if2:
                should_update_tokens.append(token)
        return res, should_update_tokens

    def process_native_token(self, native_token_address:str, wrapped_native_token_address:str, internal_txs:List[InternalTx])->List[FundFlow]:
        res:List[FundFlow]=[]
        for e in internal_txs:
            if int(e.value) == 0:
                continue
            raw_amount = int(e.value)
            res.append(
                FundFlow(
                    e.from_, e.to_, native_token_address, e.value, 18, token_name="native"
                )
            )
            # Special process for wrapped native token
            if  e.to_ == wrapped_native_token_address or e.from_ == wrapped_native_token_address:
                res.append(
                    FundFlow(
                        e.to_, e.from_, wrapped_native_token_address, raw_amount, 18
                    )
                )
        return res
    
    def process_erc20(self, wrapped_native_token_address, logs: List[dict])->List[FundFlow]:
        res:List[FundFlow]=[]
        for e in logs:
            if len(e["topics"]) != 3 or e["topics"][0] != ERC20TransferEvent:
                continue
            from_, to, token, raw_amount = self.extract_token_transfer_from_event(e["address"], e["topics"], e["data"])
            if not raw_amount or raw_amount == 0:
                continue
            if token == wrapped_native_token_address:
                if from_ == "0x":
                    from_ = wrapped_native_token_address
                elif to == "0x":
                    to = wrapped_native_token_address
            res.append(
                FundFlow(
                    from_, to, token, raw_amount
                )
            )
        return res
        
    @staticmethod
    def extract_token_transfer_from_event(token, topics:List[str], data):
        from_ = FundFlowBuilder.decode_address(topics[1])
        to = FundFlowBuilder.decode_address(topics[2])
        raw_amount = FundFlowBuilder.decode_amount(data)
        return from_, to, token, raw_amount
    
    @staticmethod
    def decode_address(raw):
        if len(raw) == 66:
            return f"0x{raw[26:]}"
        elif len(raw) == 64:
            return f"0x{raw[24:]}"
        return ""

    @staticmethod
    def decode_amount(raw):
        if len(raw) == 66:
            return int(raw[2:], 16)
        elif len(raw)  == 64:
            return int(raw, 16)
        else:
            return 0


# search for local decimals and price
def search_local_transfer_things(chain:str, token:str, day:Time|str) -> (int, float):
    if isinstance(day, Time):
        day = datetime.fromtimestamp(day).date().strftime("%Y-%m-%d")
    elif isinstance(day, str):
        day = day[:10]
    decimals, price = None, None
    if not all_decimals_list.get(chain).get(token) or not all_price_list.get(chain).get(token):
        return None, None
    decimals = all_decimals_list.get(chain).get(token)
    price = all_price_list.get(chain).get(token).get(day)
    return decimals, price


# return decimals, price, value, ifAddDecimals, ifAddPrice, ifAddBypass
def agg_transfer_things(conf:Config, raw_amount:int|str, chain, token:str, upts:str) -> (int, float, float, bool):
    if bypass_token[chain].get(token):
        return None, None, None, False

    if isinstance(upts, datetime):
        upts = upts.strftime("%Y-%m-%d %H:%M:%S")
    day = upts[:10] if len(upts) >= 10 else ""
    decimals, price = search_local_transfer_things(chain, token, day)
    if decimals and price:
        return decimals, price, (int(raw_amount) / 10**decimals) * float(price), False
    
    # query geth_decimals   
    urls = Web3Providers(conf).web3HttpUrl[chain]
    ifAddPrice = False
    decimals = search_for_decimals(chain, token, urls)
    if not decimals:
        return decimals, price, 0, ifAddPrice
    # query price from aml table
    c = chain
    if token in WETHs:
        chain = 'eth'
        token = WethAddress
    price = db.get_crawler_price(chain, token, upts)
    value = 0
    chain = c
    # update price list
    if float(price) > 0:
        if not all_price_list[chain].get(token):
            all_price_list[chain][token] = {}
        all_price_list[chain][token][day] = price
        value = (int(raw_amount) / 10**decimals) * float(price)
        ifAddPrice = True
    # add in bypass token
    else:
        bypass_token[chain][token] = 1

    return decimals, price, value, ifAddPrice

# return decimals, ifAddDecimals, ifAddBypass
def search_for_decimals(chain, token, urls:List[str]) -> int:
    if bypass_token[chain].get(token):
        return None
    decimals = all_decimals_list[chain].get(token)
    i = 0
    if not decimals:
        while true:
            url = random.choice(urls)
            if i > 5 or decimals:
                break
            try:
                decimals = geth.get_token_decimals(token, url)
            except Exception as e:
                i += 1
                if len(token) > 0:
                    print("web3 query failed", e)
        if decimals:
            all_decimals_list[chain][token] = decimals
    return decimals
    

def Build_Balance_Changes(fund_flow:List[FundFlow])->Dict[str, Dict[str, ItemChange]]:
    balance_changes: Dict[str, Dict[str, ItemChange]] = {}
    if type(fund_flow) != list:
        fund_flow = json.loads(fund_flow)
    for aa in fund_flow:
        a = aa
        if type(aa) != FundFlow:
            a = FundFlow(**dict(aa))

        if not balance_changes.get(a.from_):
            balance_changes[a.from_] = {}
        if not balance_changes[a.from_].get(a.token):
            balance_changes[a.from_][a.token] = ItemChange(a.token, 0, 0)
        balance_changes[a.from_][a.token].value -= a.value or 0
        balance_changes[a.from_][a.token].amount -= a.raw_amount or 0

        if not balance_changes.get(a.to_):
            balance_changes[a.to_] = {}
        if not balance_changes[a.to_].get(a.token):
            balance_changes[a.to_][a.token] = ItemChange(a.token, 0, 0)
        balance_changes[a.to_][a.token].value += a.value or 0
        balance_changes[a.to_][a.token].amount += a.raw_amount or 0
    
    # simplify balance changes
    to_remove = []
    for addr, changes in balance_changes.items():
            del_dict = {k: v for k, v in changes.items() if v.amount != 0}
            if not del_dict:
                    to_remove.append(addr)
            balance_changes[addr] = del_dict or {}
    for k in to_remove:
            del balance_changes[k]

    return balance_changes

def dump_all_lists(should_update_price_tokens:List[str], chain:str, ifAddDecimals, ifAddBypass):
    if ifAddDecimals:
        dump(all_decimals_list[chain], all_decimals_file_path.format(chain), 'w')
    if ifAddBypass:
        dump(bypass_token[chain], bypass_token_file_path.format(chain), 'w')
    if should_update_price_tokens:
        for token in should_update_price_tokens:
            dump(all_price_list[chain][token], all_price_file_path.format(chain, token), 'w')
    



def load_all_token_info(root_path:str="your project path"):
    for chain in os.listdir(root_path):
        folder_path = os.path.join(root_path, chain)
        # load prices
        if os.path.isdir(folder_path):
            price_list_path = os.path.join(folder_path, 'price_list')
            all_price_list[chain] = {}
            
            for token_name in os.listdir(price_list_path):
                file_path = os.path.join(price_list_path, token_name)
                if os.path.isfile(file_path):
                    with open(file_path, 'r') as file:
                        file_content = json.load(file)
                    all_price_list[chain][token_name] = file_content

            # load decimals
            with open(all_decimals_file_path.format(chain), 'r') as file:
                if not file:
                    all_price_list[chain] = {}
                all_decimals_list[chain] = json.load(file)
            # load bypass tokens
            with open(bypass_token_file_path.format(chain), 'r') as file:
                if not file:
                    bypass_token[chain] = {}
                bypass_token[chain] = json.load(file)
            all_token_list[chain] = {}
            

import aggregator as agg

if __name__ == "__main__":
    load_all_token_info()
    inhash = "0xbcf5160e1daefb5002eb77362c8503643d549d14bc4445308155101ae29cbc48"
    conf = Config("config.yaml")
    ts = "2023-12-26"
    inchain = "eth"
    tx = agg.get_complete_tx_with_hash(conf, inchain, inhash)
    builder = FundFlowBuilder(conf,[])
    fund_flow = builder.build_real_fund_flow(NativeTokenAddress, WethAddress, tx)
    out_balance_change = Build_Balance_Changes(conf, inchain, fund_flow, ts)
    for addr, c in out_balance_change.items():
        for token, cc in c.items():
            print(cc.__dict__)

    




