import yaml
from model import MainnetStr2Num

class Config:
    def __init__(self, config_file_path):
        self.config = self.loadConfig(config_file_path)

    def loadConfig(self, config_file_path):
        try:
            with open(config_file_path, 'r') as file:
                config = yaml.safe_load(file)
                return config
        except FileNotFoundError:
            print(f"Config file not found: {config_file_path}")
            return {}

    def get_proxy(self):
        return self.config.get("Proxy", None)
    
    def local_eth_url(self):
        return self.config["LocalEthUrl"]


class ChainProvider:
    def __init__(self, conf:Config, chain: str):
        self.chain = chain
        self.provider = conf.config.get("ChainProviders")[chain]
        self.scanUrl = self.provider["ScanUrl"]
        self.apiKeys = self.provider["ApiKeys"]
        self.node = self.provider["Node"]

class Web3Providers:
    def __init__(self, conf:Config):
        web3Http = {}
        web3Ws = {}
        alchemyHttpUrl = {}
        #extend getblock http & wss
        for key, value in conf.config.get("GetBlockHttp").items():
            web3Http.setdefault(key, []).extend(value)
        for key, value in conf.config.get("GetBlockWs").items():
            web3Ws.setdefault(key, []).extend(value)
        #extend alchemy nodes
        for key, value in conf.config.get("AlchemyHttp").items():
            web3Http.setdefault(key, []).extend(value)
            alchemyHttpUrl.setdefault(key, []).extend(value)
        #extend infura nodes
        for key, value in conf.config.get("InfuraHttp").items():
            web3Http.setdefault(key, []).extend(value)
            if 'eth' in key or 'poly' in key:
                ws = [v.replace("https", "wss") for v in value]
                web3Ws.setdefault(key, []).extend(ws)
                
        self.web3HttpUrl=web3Http
        self.web3LocalHttpUrl = conf.local_eth_url()
        self.web3WsUrl=web3Ws
        self.alchemyHttpUrl = alchemyHttpUrl
    
    def get_http_url(self, chain:str):
        if chain in ['eth', 'ethereum']:
            return [self.web3LocalHttpUrl]
        return self.web3HttpUrl[chain]
    
    def get_ws_url(self, chain:str):
        return self.web3WsUrl[chain]

def convert_config_chain(chain:str):
    if chain == "arb":
        return "arbitrum"
    if chain == "opt":
        return "optimism"
    if chain == "ftm":
        return "fantom"
    if chain == "poly":
        return "polygon"
    if chain == "avax":
        return "avalanche"
    return chain