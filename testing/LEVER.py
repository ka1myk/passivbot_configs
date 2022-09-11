import BinanceHelper
import json

with open('variables.json') as v:
    variables = json.load(v)

coin = "LEVER"
currency = variables['currency']
symbol = coin + currency
greed = variables['greed']
multiplier = variables['LEVER']['multiplier']
long_profit_percentage = variables['LEVER']['long_profit_percentage']
short_profit_percentage = variables['LEVER']['short_profit_percentage']

BinanceHelper.BinanceHelper.do_profit(symbol, greed, multiplier, long_profit_percentage, short_profit_percentage)