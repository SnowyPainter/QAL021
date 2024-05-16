import datetime
import mojito
import math
import time
import MarketGap.learn as learn, stockdata
import numpy as np
import pprint
import tensorflow as tf
import json
import pandas as pd

from KEYS import *

def affordable_stocks(init_amount, stock_price, percent, affordables):
    n = math.floor((init_amount * percent) / stock_price)
    if n >= affordables:
        n = affordables
    return n
def buy_order(symbol, qty): #market price
    resp = broker.create_market_buy_order(
        symbol=symbol,
        quantity=qty
    )
    pprint.pprint(resp)
    time.sleep(1)
def sell_order(symbol, qty):
    resp = broker.create_market_sell_order(
        symbol=symbol,
        quantity=qty
    )
    pprint.pprint(resp)
    time.sleep(1)

def get_price(symbol):
    resp = broker.fetch_price(symbol)
    return int(resp['output']['stck_prpr'])
def create_prices(symbol1, symbol2):
    df = pd.DataFrame()
    p1 = get_price(symbol1)
    time.sleep(1)
    p2 = get_price(symbol2)
    df[symbol1+'.KS_Price'] = [p1]
    df[symbol2+'.KS_Price'] = [p2]
    df['Datetime'] = [pd.to_datetime(stockdata.today(), format="%Y-%m-%d %H:%M:%S%z")]
    df.set_index('Datetime', inplace=True)
    return df
def reshape(state):
    return np.reshape(state, [1, 1, 2])

broker = mojito.KoreaInvestment(api_key=KEY, api_secret=APISECRET, acc_no=ACCOUNT_NO, mock=True)
agent = tf.keras.models.load_model("./MarketGap/hmsk.keras")
resp = broker.fetch_balance()
current_amount = int(resp['output2'][0]['prvs_rcdl_excc_amt'])
symbols = ["042700", "000660"] #hanmi semiconductor / sk hynix
env = learn.MarketEnvironment(symbols[0]+".KS", symbols[1]+".KS", stockdata.today_before(14), stockdata.today(),"30m")

stocks_qty = {}
for stock in resp['output1']:
    stocks_qty[stock['pdno']] = int(stock['hldg_qty'])

symbol1_units = 0 if not symbols[0] in stocks_qty else stocks_qty[symbols[0]]
symbol2_units = 0 if not symbols[1] in stocks_qty else stocks_qty[symbols[1]]

trades = 0
fee = 0.005
net_wealths = list()

start_time = datetime.time(9, 0)
end_time = datetime.time(15, 30)

init_amount = current_amount
p = 0.1

print(f"평가 : {resp['output2'][0]['tot_evlu_amt']}")
print(f"예수금 : {current_amount}")
print(f"보유 종목 : {stocks_qty}")
while True:
    current_time = datetime.datetime.now().time()
    if start_time <= current_time <= end_time:
        prices = create_prices(symbols[0], symbols[1])
        env.append_raw(prices)
        state = reshape(np.array([env.get_last()]))
        symbol1_price = prices.iloc[0][0]
        symbol2_price = prices.iloc[0][1]
        
        action = np.argmax(agent.predict(state, verbose=0)[0, 0])
        if action == 0:
            print(stockdata.today(), "Holding")
        else:
            if action == 1:
                if symbol2_units > 0:
                    units = affordable_stocks(init_amount, symbol2_price, p, symbol2_units)
                    print(f"SOLD : {symbols[1]} - {units} / {symbol2_price}")
                    sell_order(symbols[1], units)
                    current_amount += units * symbol2_price
                    symbol2_units -= units
                    trades += 1
                symbol1_amount = math.floor(current_amount / symbol1_price)
                units = affordable_stocks(init_amount, symbol1_price, p, symbol1_amount)
                if symbol1_amount > 0:
                    print(f"BUY : {symbols[0]} - {units} / {symbol1_price}")
                    buy_order(symbols[0], units)
                    current_amount -= units * symbol1_price + units * fee
                    symbol1_units += units
                    trades += 1
            elif action == 2:
                if symbol1_units > 0:
                    units = affordable_stocks(init_amount, symbol1_price, p, symbol1_units)
                    print(f"SOLD : {symbols[0]} - {units} / {symbol1_price}")
                    sell_order(symbols[0], units)
                    current_amount += units * symbol1_price
                    symbol1_units -= units
                    trades += 1
                symbol2_amount = math.floor(current_amount / symbol2_price)
                units = affordable_stocks(init_amount, symbol2_price, p, symbol2_amount)
                if symbol2_amount > 0:
                    print(f"BUY : {symbols[1]} - {units} / {symbol2_price}")
                    buy_order(symbols[1], units)
                    current_amount -= units * symbol2_price + units * fee
                    symbol2_units += units
                    trades += 1
        net_wealths.append(symbol1_units * symbol1_price + symbol2_units * symbol2_price + current_amount)
        time.sleep(60*5)
    
    if current_time >= end_time:
        print(f"장 종료 : {trades}")
        print(net_wealths)
        break