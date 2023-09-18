import re, math, secrets, argparse, functools, time

from binance.client import Client
from binance.helpers import round_step_size

client = Client("Ny8b20OD7T3dXm96SVKmpbtJQA9rxmeh26BclnXGYYV3GDjktrVTAsJcLOqRIp2V",
                "Nu4UemnKHnjwOx05ZFg9oT8NTV8ull95X7n7Oa8jZ9M9bT6e6DZJPD9YJagbAkGe")

asset = "USDT"
# default = 6; min_notional can be extended #
min_notional = 10
# default = 1.2; min_notional_corrector needs to correct error of not creating close orders #
min_notional_corrector = 1.2

# for short #
# without fee deduction #
short_base_percentage_futures_close = 0.999
# if position starts pump #
short_percentage_futures_open_exist_position = 1.25
# if no position and like fishnet #
short_percentage_futures_open_new_position = 1.004

# for long #
# without fee deduction #
long_base_percentage_futures_close = 1.001
# if position starts pump #
long_percentage_futures_open_exist_position = 0.75
# if no position and like fishnet #
long_percentage_futures_open_new_position = 0.996

percentage_of_open_position = 0.15

# new order will be opened after to_the_moon_cooldown. Last digit is for hours  #
to_the_moon_cooldown = 1000 * 60 * 60 * 48
# new order will be canceled only after cooldown_to_cancel_order_without_position. Last digit is for hours  #
cooldown_to_cancel_order_without_position = 1000 * 60 * 60 * 0.5

# last digit is for days #
deltaTime = 1000 * 60 * 60 * 24 * 14
# most likely, it will not fall less than 0.79, so lower limit orders will be cancelled after deltaTime #
percentage_spot_open = [0.97, 0.94, 0.91, 0.85, 0.79, 0.73]

futures_ticker = client.futures_ticker()
futures_account = client.futures_account()
symbol_info = client.futures_exchange_info()
serverTime = client.get_server_time()['serverTime']
futures_account_balance = client.futures_account_balance()
futures_position_information = client.futures_position_information()


def timeit(func):
    @functools.wraps(func)
    def new_func(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        elapsed_time = time.time() - start_time
        print('function [{}] finished in {} ms'.format(
            func.__name__, int(elapsed_time * 1_000)))
        return result

    return new_func


def set_futures_change_leverage():
    for x in futures_ticker:
        try:
            print(client.futures_change_leverage(symbol=x["symbol"], leverage=1))
        except Exception as e:
            print("fail to set_futures_change_leverage of", x["symbol"], e)


def set_futures_change_multi_assets_mode():
    try:
        print(client.futures_change_multi_assets_mode(multiAssetsMargin="True"))
    except Exception as e:
        print("fail to set_futures_change_multi_assets_mode", e)


def get_notional(symbol):
    try:
        for x in symbol_info['symbols']:
            if x['symbol'] == symbol:
                for y in x['filters']:
                    if y['filterType'] == 'MIN_NOTIONAL':
                        return y['notional']
    except Exception as e:
        print("fail to get_notional for", symbol, e)


def get_tick_size(symbol):
    try:
        for x in symbol_info['symbols']:
            if x['symbol'] == symbol:
                for y in x['filters']:
                    if y['filterType'] == 'PRICE_FILTER':
                        return y['tickSize']
    except Exception as e:
        print("fail to get_tick_size for", symbol, e)


def get_step_size(symbol):
    try:
        for x in symbol_info['symbols']:
            if x['symbol'] == symbol:
                for y in x['filters']:
                    if y['filterType'] == 'MARKET_LOT_SIZE':
                        return y['stepSize']
    except Exception as e:
        print("fail to get_step_size for", symbol, e)


def get_quantity_precision(symbol):
    try:
        for x in symbol_info['symbols']:
            if x['symbol'] == symbol:
                return x["quantityPrecision"]
    except Exception as e:
        print("fail to get_quantity_precision for", symbol, e)


def get_quantity(symbol):
    try:
        quantity = round(
            (float(get_notional(symbol)) * set_greed())
            / float(client.futures_mark_price(symbol=symbol)["markPrice"]),
            get_quantity_precision(symbol)
        )

    except Exception as e:
        print("fail to get_quantity for", symbol, e)
    return quantity


@timeit
def get_futures_tickers():
    # exclude balance_asset tickers #
    futures_account_balance_asset = []
    for x in futures_account_balance:
        futures_account_balance_asset.append(x["asset"] + asset)

    # exclude BUSD and quarterly tickers #
    all_tickers = []
    for x in futures_ticker:
        remove_quarterly_contract = re.search('^((?!_).)*$', x["symbol"])
        remove_busd_contract = re.search('^.*USDT$', x["symbol"])
        if remove_quarterly_contract and remove_busd_contract:
            all_tickers.append(x["symbol"])

    # exclude tickers with onboardDate < deltaTime #
    onboardDate = []
    for x in symbol_info["symbols"]:
        if float(x["onboardDate"]) > serverTime - deltaTime:
            onboardDate.append(x["symbol"])

    tickers_after_excluding = set(all_tickers) - set(futures_account_balance_asset) - set(onboardDate)

    return list(tickers_after_excluding)


@timeit
def short_get_futures_tickers():
    # exclude short_exist_positions tickers #
    short_exist_positions = []
    for x in futures_position_information:
        if float(x["positionAmt"]) < 0:
            short_exist_positions.append(x["symbol"])

    short_tickers_after_excluding = set(get_futures_tickers()) - set(short_exist_positions)

    return list(short_tickers_after_excluding)


def long_get_futures_tickers():
    # exclude long_exist_positions tickers #
    long_exist_positions = []
    for x in futures_position_information:
        if float(x["positionAmt"]) > 0:
            long_exist_positions.append(x["symbol"])

    long_tickers_after_excluding = set(get_futures_tickers()) - set(long_exist_positions)

    return list(long_tickers_after_excluding)


def set_greed():
    try:
        # set base_greed #
        base_greed = math.ceil(((float(futures_account['totalWalletBalance']) * min_notional_corrector) / (
                len(futures_ticker) * min_notional)))

    except Exception as e:
        print("fail to set_greed", e)

    return base_greed


def short_create_open_limit(symbol):
    try:
        client.futures_create_order(symbol=symbol,
                                    quantity=get_quantity(symbol),
                                    price=round_step_size(float(
                                        client.futures_position_information(symbol=symbol)[1]["markPrice"])
                                                          * short_percentage_futures_open_exist_position,
                                                          get_tick_size(symbol)),
                                    side='SELL',
                                    positionSide='SHORT',
                                    type='LIMIT',
                                    timeInForce="GTC"
                                    )
    except Exception as e:
        print("fail to short_create_open_limit", symbol, e)


def long_create_open_limit(symbol):
    try:
        client.futures_create_order(symbol=symbol,
                                    quantity=get_quantity(symbol),
                                    price=round_step_size(float(
                                        client.futures_position_information(symbol=symbol)[0]["markPrice"])
                                                          * long_percentage_futures_open_exist_position,
                                                          get_tick_size(symbol)),
                                    side='BUY',
                                    positionSide='LONG',
                                    type='LIMIT',
                                    timeInForce="GTC"
                                    )
    except Exception as e:
        print("fail to long_create_open_limit", symbol, e)


def short_create_close_limit(symbol):
    try:
        client.futures_create_order(symbol=symbol,
                                    quantity=round_step_size(abs((float(
                                        client.futures_position_information(symbol=symbol)[1]["positionAmt"]))),
                                        get_step_size(symbol)),
                                    price=round_step_size(float(
                                        client.futures_position_information(symbol=symbol)[1]["entryPrice"])
                                                          * short_base_percentage_futures_close,
                                                          get_tick_size(symbol)),
                                    side='BUY',
                                    positionSide='SHORT',
                                    type='LIMIT',
                                    timeInForce="GTC"
                                    )
    except Exception as e:
        print("fail to short_create_close_limit for", symbol, e)


def long_create_close_limit(symbol):
    try:
        client.futures_create_order(symbol=symbol,
                                    quantity=round_step_size(abs((float(
                                        client.futures_position_information(symbol=symbol)[0]["positionAmt"]))),
                                        get_step_size(symbol)),
                                    price=round_step_size(float(
                                        client.futures_position_information(symbol=symbol)[0]["entryPrice"])
                                                          * long_base_percentage_futures_close,
                                                          get_tick_size(symbol)),
                                    side='SELL',
                                    positionSide='LONG',
                                    type='LIMIT',
                                    timeInForce="GTC"
                                    )
    except Exception as e:
        print("fail to long_create_close_limit", symbol, e)


@timeit
def close_exist_positions():
    try:
        for x in futures_position_information:
            if float(x["positionAmt"]) < 0:
                symbol = x["symbol"]

                count_buy_orders = 0
                count_sell_orders = 0

                for x in client.futures_get_open_orders(symbol=symbol):
                    if x["side"] == "BUY":
                        count_buy_orders = count_buy_orders + 1

                    if x["side"] == "SELL":
                        count_sell_orders = count_sell_orders + 1

                if count_buy_orders == 0:
                    short_create_close_limit(symbol)

                if count_sell_orders == 0 and x["updateTime"] < serverTime - to_the_moon_cooldown:
                    short_create_open_limit(symbol)

        for x in futures_position_information:
            if float(x["positionAmt"]) > 0:
                symbol = x["symbol"]

                count_buy_orders = 0
                count_sell_orders = 0

                for x in client.futures_get_open_orders(symbol=symbol):
                    if x["side"] == "BUY":
                        count_buy_orders = count_buy_orders + 1

                    if x["side"] == "SELL":
                        count_sell_orders = count_sell_orders + 1

                if count_sell_orders == 0:
                    long_create_close_limit(symbol)

                if count_buy_orders == 0 and x["updateTime"] < serverTime - to_the_moon_cooldown:
                    long_create_open_limit(symbol)
    except Exception as e:
        print("fail to close_exist_positions", symbol, e)


@timeit
def cancel_close_order_if_filled():
    try:
        for x in futures_position_information:
            if float(x["positionAmt"]) < 0:
                symbol = x["symbol"]

                for x in client.futures_get_open_orders(symbol=symbol):
                    if x["side"] == "BUY" and abs(float(x["positionAmt"])) != float(x["origQty"]):
                        client.futures_cancel_order(symbol=symbol, orderId=x["orderId"])

        for x in futures_position_information:
            if float(x["positionAmt"]) > 0:
                symbol = x["symbol"]

                for x in client.futures_get_open_orders(symbol=symbol):
                    if x["side"] == "SELL" and abs(float(x["positionAmt"])) != float(x["origQty"]):
                        client.futures_cancel_order(symbol=symbol, orderId=x["orderId"])

    except Exception as e:
        print("fail to cancel_close_order_if_filled", symbol, e)


@timeit
def cancel_open_orders_without_position():
    try:
        for x in client.futures_get_open_orders():
            if not x["reduceOnly"] and serverTime > float(x["updateTime"]) + cooldown_to_cancel_order_without_position:
                client.futures_cancel_order(symbol=x["symbol"], orderId=x["orderId"])

    except Exception as e:
        print("fail to cancel_open_orders_without_position", x, e)


# end try to remove #


def transfer_free_USD_to_spot():
    try:
        for x in futures_account_balance:
            select_USD_asset = re.search('^((?!USD).)*$', x["asset"])
            if not select_USD_asset and float(x["withdrawAvailable"]) > 0:
                try:
                    client.futures_account_transfer(asset=x["asset"],
                                                    amount=float(x["withdrawAvailable"]),
                                                    type=2,
                                                    timestamp=serverTime)
                except Exception as e:
                    print("fail transfer", x["asset"], "to spot", e)
    except Exception as e:
        print("fail transfer_free_USD_to_spot", e)


def buy_coins_on_spot():
    symbol = "BTCUSDT"

    for x in client.get_open_orders(symbol=symbol):
        try:
            if x["time"] < serverTime - deltaTime:
                client.cancel_order(symbol=symbol, orderId=x["orderId"])
        except Exception as e:
            print("fail to cancel orders older (serverTime - deltaTime)", e)

    if 10 < float(client.get_asset_balance(asset=asset)['free']) < 20:
        try:
            client.create_order(symbol=symbol,
                                side='BUY',
                                type='MARKET',
                                quoteOrderQty=math.floor(float(client.get_asset_balance(asset=asset)['free'])))
        except Exception as e:
            print("fail to buy market BTC for", asset, e)

    if float(client.get_asset_balance(asset=asset)['free']) > 20:
        try:
            client.create_order(symbol=symbol,
                                side='BUY',
                                type='MARKET',
                                quoteOrderQty=math.floor(float(client.get_asset_balance(asset=asset)['free']) * 0.5))

            client.order_limit(symbol=symbol,
                               quantity=client.get_all_orders(symbol=symbol)[-1]["origQty"],
                               price=round_step_size(
                                   float(client.get_avg_price(symbol=symbol)['price'])
                                   * secrets.choice(percentage_spot_open),
                                   get_tick_size(symbol=symbol)),
                               side='BUY',
                               type='LIMIT',
                               timeInForce="GTC"
                               )

        except Exception as e:
            print("fail to buy limit BTC for", asset, e)

    try:
        client.transfer_dust(asset=asset)
    except Exception as e:
        print("fail to dust", asset, "to BNB", e)


def transfer_free_spot_coin_to_futures():
    try:
        for x in futures_account_balance:
            select_USD_asset = re.search('^((?!USD).)*$', x["asset"])
            if select_USD_asset and float(client.get_asset_balance(asset=x["asset"])["free"]) > 0:
                try:
                    client.futures_account_transfer(asset=x["asset"],
                                                    amount=float(client.get_asset_balance(asset=x["asset"])["free"]),
                                                    type=1,
                                                    timestamp=serverTime)
                except Exception as e:
                    print("fail transfer", x["asset"], "to futures", e)
    except Exception as e:
        print("fail transfer_free_spot_coin_to_futures", e)


# --function open_for_profit #

def short_open_for_profit(symbol):
    try:
        client.futures_create_order(symbol=symbol,
                                    quantity=get_quantity(symbol),
                                    price=round_step_size(
                                        float(client.futures_mark_price(symbol=symbol)["markPrice"])
                                        * short_percentage_futures_open_new_position,
                                        get_tick_size(symbol)),
                                    side='SELL',
                                    positionSide='SHORT',
                                    type='LIMIT',
                                    timeInForce="GTC")
    except Exception as e:
        print("fail short_open_for_profit", symbol, e)


def long_open_for_profit(symbol):
    try:
        client.futures_create_order(symbol=symbol,
                                    quantity=get_quantity(symbol),
                                    price=round_step_size(
                                        float(client.futures_mark_price(symbol=symbol)["markPrice"])
                                        * long_percentage_futures_open_new_position,
                                        get_tick_size(symbol)),
                                    side='BUY',
                                    positionSide='LONG',
                                    type='LIMIT',
                                    timeInForce="GTC")
    except Exception as e:
        print("fail long_open_for_profit", symbol, e)


# --function close_with_profit #
@timeit
def close_with_profit():
    cancel_close_order_if_filled()
    cancel_open_orders_without_position()
    close_exist_positions()


# --function transfer_profit #
@timeit
def transfer_profit():
    transfer_free_USD_to_spot()
    buy_coins_on_spot()
    transfer_free_spot_coin_to_futures()


@timeit
def count_open_positions_and_start():
    long_positions = 0
    for x in futures_position_information:
        if float(x["positionAmt"]) > 0:
            long_positions = long_positions + 1

    short_positions = 0
    for x in futures_position_information:
        if float(x["positionAmt"]) < 0:
            short_positions = short_positions + 1

    if (round((long_positions + short_positions) / (len(get_futures_tickers()) * 2), 2)) < percentage_of_open_position:
        for symbol in long_get_futures_tickers():
            long_open_for_profit(symbol)
            time.sleep(0.1)

        for symbol in short_get_futures_tickers():
            short_open_for_profit(symbol)
            time.sleep(0.1)


parser = argparse.ArgumentParser()
parser.add_argument('--function', type=str, required=True)

if parser.parse_args().function == "open":
    count_open_positions_and_start()
if parser.parse_args().function == "close":
    close_with_profit()
if parser.parse_args().function == "transfer":
    transfer_profit()
if parser.parse_args().function == "initialized":
    set_futures_change_multi_assets_mode()
    set_futures_change_leverage()
