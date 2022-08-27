import BinanceHelper
import json

with open('variables.json') as v:
    variables = json.load(v)

symbol = 'TRXBUSD'
greed = variables['greed']
multiplier = variables['TRX']['multiplier']
long_profit_percentage = variables['TRX']['long_profit_percentage']
short_profit_percentage = variables['TRX']['short_profit_percentage']

BinanceHelper.BinanceHelper.do_profit(symbol, greed, multiplier, long_profit_percentage, short_profit_percentage)