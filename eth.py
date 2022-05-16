from decimal import Decimal
from binance.client import Client
import requests, json, time

with open('/root/passivbot/api-keys.json') as p:
    creds = json.load(p)

client = Client(creds['binance_01']['key'], creds['binance_01']['secret'])

while True:
    try:
        headers = {'coinglassSecret': '50f90ddcd6a8437992431ab0f1b698c1'}
        url = requests.get(
            "https://open-api.coinglass.com/api/pro/v1/futures/liquidation/detail/chart?symbol=ETH&timeType=9",
            headers=headers)
        text = url.text
        data = json.loads(text)

        long_signal = float(data['data'][90]['buyVolUsd'])
        if long_signal > 40000:
            print('fire_long')
            client.futures_create_order(symbol='ETHBUSD', side='BUY', positionSide='LONG', type='LIMIT', quantity=0.003,
                                        timeInForce='GTX')

            priceForCloseLongOrder = Decimal(client.futures_position_information(symbol='ETHBUSD')[1]['entryPrice'])
            amtForCloseLongOrder = Decimal(client.futures_position_information(symbol='ETHBUSD')[1]['positionAmt'])

            client.futures_create_order(symbol='ETHBUSD', side='SELL', positionSide='LONG', type='LIMIT',
                                        quantity=amtForCloseLongOrder,
                                        timeInForce='GTX', price=priceForCloseLongOrder)

            time.sleep(120)

        short_signal = float(data['data'][90]['sellVolUsd'])
        if short_signal > 40000:
            print('fire_short')

            priceForOpenShortOrder = Decimal(client.futures_coin_ticker(symbol='ETHUSD_PERP')[0]['lastPrice'])
            client.futures_create_order(symbol='ETHBUSD', side='SELL', positionSide='SHORT', type='LIMIT',
                                        timeInForce='GTX',
                                        quantity=0.003, price=priceForOpenShortOrder)

            priceForCloseShortOrder = Decimal(client.futures_position_information(symbol='ETHBUSD')[2]['entryPrice'])
            amtForCloseShortOrder = Decimal(client.futures_position_information(symbol='ETHBUSD')[2]['positionAmt'])

            client.futures_create_order(symbol='ETHBUSD', side='BUY', positionSide='SHORT', type='LIMIT',
                                        quantity=amtForCloseShortOrder,
                                        timeInForce='GTX', price=priceForCloseShortOrder)

            time.sleep(120)

    except Exception as e:
        print("Function errored out!", e)
        print("Retrying ... ")

