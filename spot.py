import argparse
import json

from binance.client import Client
from binance.helpers import round_step_size

from telegram_exception_alerts import Alerter

with open('variables.json') as v:
    variables = json.load(v)

parser = argparse.ArgumentParser()
parser.add_argument('--coin', type=str, required=True)
coin = parser.parse_args()

client = Client(variables['binance_01']['key'], variables['binance_01']['secret'])
symbol = coin.coin + variables['currency']

bot_token = variables['telegram']['bot_token']
bot_chatID = variables['telegram']['bot_chatID']
tg_alert = Alerter(bot_token=bot_token, chat_id=bot_chatID)

grid = [0.90, 0.85, 0.80]


def get_symbol_info():
    return client.get_symbol_info(symbol)


def get_avg_price():
    return float(client.get_avg_price(symbol=symbol)['price'])


# why 13440?
# 7 * 40 * 4 * 12 = 13440$ for 12 month with greed 1, greed increase only by int
# len(coins) * week budget in $ * weeks in month * amount of month continuous trade
def set_greed():
    if float(client.get_asset_balance(asset='BUSD')['free']) < 13440:
        greed = 1
    else:
        greed = round(float(client.get_asset_balance(asset='BUSD')['free']) / 13440)
    return int(greed)


def get_min_notional():
    for x in get_symbol_info()["filters"]:
        if x['filterType'] == 'MIN_NOTIONAL':
            return x['minNotional']


def get_tick_size():
    for x in get_symbol_info()["filters"]:
        if x['filterType'] == 'PRICE_FILTER':
            return x['tickSize']


def get_rounded_price(price):
    return round_step_size(price, get_tick_size())


def get_quote_order_qty() -> float:
    return float(get_min_notional()) * set_greed() * 1.3


def spot_create_market_buy():
    client.order_market_buy(symbol=symbol,
                            side='BUY',
                            type='MARKET',
                            quoteOrderQty=get_quote_order_qty())


def spot_create_grid_limit_buy(grid):
    for x in grid:
        client.order_limit(symbol=symbol,
                           quantity=float(client.get_all_orders(symbol=symbol)[-1]["origQty"]),
                           price=get_rounded_price(get_avg_price() * x),
                           side='BUY',
                           type='LIMIT',
                           timeInForce="GTC"
                           )


def cancel_orders():
    for x in client.get_open_orders(symbol=symbol):
        client.cancel_order(symbol=symbol, orderId=x["orderId"])


@tg_alert
def go_baby_spot():
    cancel_orders()
    spot_create_market_buy()
    spot_create_grid_limit_buy(grid)


go_baby_spot()
