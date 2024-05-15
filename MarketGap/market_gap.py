import sys
sys.path.append('..')

import stockdata
import MarketGap.learn as learn
import MarketGap.backtest as backtest
import numpy as np
import matplotlib.pyplot as plt

tickers = ["042700.KS", "000660.KS"]
env = learn.MarketEnvironment("042700.KS", "000660.KS", stockdata.today_before(300), stockdata.today(),"1d")

def reshape(state):
    return np.reshape(state, [1, 1, 2])

def l():
    agent = learn.DQNAgent(env, 10000, 64)
    agent.learn(50)
    agent.save("./hmsk.keras")

def bt():
    amount = 100000000
    stgy = backtest.Strategy1(env, amount, 0.0025)
    stgy.test()
    print(stgy.net_wealths[-1] / amount)
    plt.plot(stgy.net_wealths)
    plt.show()

bt()