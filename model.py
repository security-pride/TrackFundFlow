MainnetStr2Num = {
    "eth":1,"poly":137,"bsc":56, "opt":10,"arb":42161, "avax":43114, "ftm": 250
}

ERC20TransferEvent = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
NativeTokenAddress = "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee"
ZeroTokenAddress = "0x0000000000000000000000000000000000000000"
WethAddress =  "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"
NativeName = "native"
WrappedTokenAddress = {
    "eth": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
    "arbitrum": "0x82af49447d8a07e3bd95bd0d56f35241523fbab1",
    "bsc": "0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c",
    "polygon": "0x0d500b1d8e8ef31e21c99d1db9a6444d3adf1270",
    "avalanche": "0x49d5c2bdffac6ce2bfdb6640f4f80f226bc10bab",
    "fantom": "0x21be370d5312f44cb42ce377bc9b8a0cef1a4c83",
    "optimism": "0x4200000000000000000000000000000000000006",
}

SynapseUSD = {
    "0x1b84765de8b7566e4ceaf4d0fd3c5af52d3dde4f": "0xdac17f958d2ee523a2206206994597c13d831ec7", # eth
    "0x2913e812cf0dcca30fb28e6cac3d2dcff4497688": "0xff970a61a04b1ca14834a43f5de4533ebddb5cc8", # arbitrum
    "0x23b891e5c62e0955ae2bd185990103928ab817b3": "0x8ac76a51cc950d9822d68b83fe1ad97b32cd580d", # bsc
    "0xed2a7edd7413021d440b09d654f3b87712abab66": "0x04068da6c83afcfa0e13ba15a6696662335d5b75", # fantom
    "0xcfc37a6ab183dd4aed08c204d1c2773c0b1bdf46": "0xb97ef9ef8734c71904d8002f8b6bc66dd9c48a6e", # avax
    "0xb6c473756050de474286bed418b77aeac39b02af": "0x2791bca1f2de4661ed88a30c99a7a9449aa84174", # polygon
    "0x809dc529f07651bd43a172e8db6f4a7a0d771036": "0x4200000000000000000000000000000000000006", # optimism
}

AnyWETH = {
    "eth": "0x0615dbba33fe61a31c7ed131bda6655ed76748b1",
    "arbitrum": "0x1Dd9e9e142f3f84d90aF1a9F2cb617C7e08420a4",
    "avalanche": "0xce3b0d4e4e4285e55c0bfb294112caf19682eb8a",
    "fantom": "0x6362496bef53458b20548a35a2101214ee2be3e0",
    "optimism": "0x965f84d915a9efa2dd81b653e3ae736555d945f4",
    "polygon": "0x3d913dc3c4ce1249c4997447d41a8694a82b4934",
}

from typing import Dict
from datetime import datetime
from web3.types import *

class ItemChange():
    def __init__(self, token:str, amount:float, value:float=None) -> None:
        self.token = token.lower()
        self.amount = amount
        self.value = value
        
# item_change dict structure:
# token_address : ItemChange
class BalanceChange():
    def __init__(self, address:str, item_changes:Dict[str, ItemChange]):
        self.address = address.lower()  # account address
        self.item_changes = item_changes

class FundFlow():
    def __init__(self, from_:str, to_:str, token:str, raw_amount:str, decimals:int=None, amount:float=None, price:str=None, value:str=None, token_name:str=None):
        self.from_:str = from_
        self.to_:str = to_
        self.token:str = token
        self.raw_amount:int = int(raw_amount) if raw_amount else None
        self.decimals:int = decimals
        self.amount:float = int(raw_amount) / (10**decimals) if decimals else None
        self.price:float = float(price) if price else None
        self.value:float = float(value) if price else None
        self.token_name:str = token_name

class TransToken():
    def __init__(self, token:str, raw_amount:int|str=0, decimals:int|str=None, token_name:str=None, token_symbol:str=None, ts:str|datetime = None):
        self.token:str = token.lower()
        self.raw_amount:int = int(raw_amount)
        self.decimals:int = int(decimals)
        self.token_name:str = token_name
        self.token_symbol:str =token_symbol
        self.ts:str | datetime = ts

class Swapped():
    def __init__(self, ori_token:str, ori_amount:str, dst_token:str, dst_amount:str, swap_contract:str) -> None:
        self.ori_token = ori_token
        self.ori_amount = ori_amount
        self.dst_token = dst_token
        self.dst_amount = dst_amount
        self.swap_contract = swap_contract

class OutTransfer():
    def __init__(self, to:str, transTokens:List[TransToken]):
        self.toAddress:str = to
        self.tokens:List[TransToken] = transTokens

class Record():
    def __init__(self, from_:str, outTransfers:List[OutTransfer], swapped:Swapped = None):
        self.fromAddress:str = from_
        self.swapped:Swapped = swapped
        self.transfers:List[OutTransfer] = outTransfers

class AddrCategories():
    def __init__(self) -> None:
        self.swap = "SWAP"
        self.phishing = "PHISHING"
        self.exploit = "EXPLOIT"
        self.scam = "SCAM"
        self.bridge = "BRIDGE"
        self.flashLoan = "FLASHLOAN"
        self.cex = "cex"

class AddrInfo():
    def __init__(self, chain:str, address:str, name:str, category:str, is_contract:bool):
        self.chain = chain
        self.address = address
        self.name = name
        self.category = category
        self.is_contract = is_contract

class PriceInfo():
    def __init__(self, chain:str, address:str, decimals:int, price:float, ts:Timestamp) -> None:
        self.chain = chain
        self.address = address
        self.decimals = decimals
        self.price = price
        self.ts = ts

class Maltransfer():
    def __init__(self, chain:str, project:str, txhash:str, from_address:str, ts:datetime|str, token:str, toke_name:str, amount:str|int, decimals:int, price: float|str) -> None:
        self.chain = chain
        self.project= project
        self.from_address = from_address
        self.txhash = txhash
        self.ts = ts
        self.token = token
        self.token_name = toke_name
        self.amount = amount
        self.decimals = decimals
        self.price = price
        self.value = int(amount) / (10**decimals) * price if price and decimals else 0
    

class InternalTx():
    def __init__(self, blockNumber:str, timeStamp:str, from_:str, to_:str, value:str, gas:str, gasUsed:str):
        if (type(timeStamp) == str and timeStamp != ''):
            ts = float(timeStamp)
            formatted_datetime = datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S UTC')
        else:
            formatted_datetime = ''
        self.blockNumber:int=int(blockNumber)
        self.timeStamp:str=formatted_datetime
        self.from_:str=from_.lower()
        self.to_:str=to_.lower()
        self.value:str=value
        self.gas:str=gas
        self.gasUsed:str=gasUsed

class Tx():
    def __init__(self, blockHash:str, blockNumber, from_:str, gas, gasPrice, hash:str, input:str, nonce, 
                 to:str, transactionIndex, value, internals:List[InternalTx], logs:List[LogReceipt]) -> None:
        self.blockHash=blockHash.lower()
        self.blockNumber=blockNumber
        self.from_=from_.lower()
        self.gas=gas
        self.gasPrice=gasPrice
        self.txhash=hash.lower()
        self.input=input
        self.nonce=nonce
        self.to=to.lower()
        self.transactionIndex=transactionIndex
        self.value=value
        self.internals:List[InternalTx]=internals
        self.logs:List[dict] = []
        for log in logs:
            log_dict = {k: convert_to_decimal_string(v) for k, v in log.items()}
            self.logs.append(log_dict)

def convert_to_decimal_string(data):
    decimal_string = data
    if isinstance(data, int):
        decimal_string = str(data)
    elif isinstance(data, str) and data[:2] == "0x" and len(data) != 42 and len(data) != 66:
        decimal_string = str(int(data, 16))
    elif isinstance(data, HexBytes):
        decimal_string = str(data.hex())
    elif isinstance(data, list):
        decimal_string = []
        for e in data:
            decimal_string.append(
                convert_to_decimal_string(e)
            )
    elif len(data) == 42 or len(data) == 66:
        decimal_string = data.lower()
    else:
        raise ValueError("Unsupported data type. Supported types: int, str, bytes", data)

    return decimal_string

def is_fund_flow_match(flow_1:List[TransToken], flow_2:List[TransToken])->bool:
    if len(flow_1) != len(flow_2):
        return False
    for i in flow_1:
        for j in flow_2:
            if i.from_ == j.from_ and i.to_ == j.to_ and i.token == j.token and i.amount == j.amount:
                flow_2.remove(j)
    return not flow_2



