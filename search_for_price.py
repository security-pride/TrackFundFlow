import time
import json
import requests
import datetime


base_CoinGeckoApi = "https://api.coingecko.com/api/v3/coins/"
all_price_list = {}

def search_for_price(chain:str, token:str, day):
    if(all_price_list.get(token.lower(), None) != None):
        token_price_list = all_price_list[token.lower()]
        if(token_price_list.get(day, None) != None):
            return token_price_list[day]
    
    return coingecko_price(chain, token, day)

def coingecko_price(chain:str, token:str, day):
    # search for local records first
    token_price_list = dict()   
    # search for coingecko
    url = "{}{}/contract/{}/market_chart/".format(base_CoinGeckoApi, convert_coingecko_chain(chain), token)
    query_params = "?vs_currency=usd&days={}".format(1000)
    url += query_params
    #proxies = {'http': "http://127.0.0.1:7890", 'https': "http://127.0.0.1:7890"}
    query_result = requests.get(url)#, proxies=proxies)
    time.sleep(5)
    price_list = json.loads(query_result.content)
    if(price_list.get("status", None) != None and price_list['status'].get("error_code", None) != None):
        print(price_list)
        time.sleep(60)
        query_result = requests.get(url)#, proxies=proxies)
        price_list = json.loads(query_result.content)
    if(price_list.get('error',None) != None):
        if(price_list['error'] == 'coin not found'):
            return None
    for element in price_list['prices']:
        time_stamp = datetime.fromtimestamp(element[0]/1000).date().strftime("%Y-%m-%d")
        price = element[1]
        token_price_list[time_stamp] = price
    with open(f"./blockchain/{chain}/price_list/" + token.lower(), "w") as f:   # replace the path with your local token file path
        json.dump(token_price_list, f)
    all_price_list[token.lower()] = token_price_list
    if(token_price_list.get(day, None) != None):
        return token_price_list[day]
    else:
        return None

def convert_coingecko_chain(chain):
    if chain in ["eth", "ethereum"]:
        return "ethereum"
