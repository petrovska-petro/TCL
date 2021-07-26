import pandas as pd
import numpy as np
import plotly.graph_objects as graph
import json
import requests

url = "https://api.thegraph.com/subgraphs/name/ianlapham/uniswap-v3-prod"
# wbtc:usdc pool v3 (0x99ac8ca7087fa4a2a1fb6357269965a2014abc35)
# wbtc:badger v2 (0xcd7989894bc033581532d2cd88da5db0a4b12859)
query = '''
query($pool: String, $time: Int!) {
    poolHourDatas(
        where: {
            pool: $pool, 
            periodStartUnix_gt: $time
        }
    ){
        periodStartUnix
        tick
    }
}
'''

times = np.arange(start=1619650800, stop=1625094000, step=360000)
df_final = pd.DataFrame(columns=['periodStartUnix', 'tick'])
for t in times:
    variables = {'pool': '0x99ac8ca7087fa4a2a1fb6357269965a2014abc35',
                 'time': int(t)}

    # Response seems limited to 100 entries, workaround by looping...
    try:
        r = requests.post(url, json={'query': query, 'variables': variables})

        json_data = json.loads(r.text)
        df_data = json_data['data']["poolHourDatas"]
        df = pd.DataFrame(df_data)
        df_final = df_final.append(df, ignore_index=True)
    except Exception as e:
        print(e)

df_final['periodStartUnix'] = pd.to_datetime(
    df_final['periodStartUnix'], unit='s')
df_final["tick"] = pd.to_numeric(df_final["tick"], downcast="float")

df_indexed = df_final.set_index('periodStartUnix')

# Resample the hourly data into daily as OHLC candless
daily = df_indexed['tick'].resample('1D').ohlc()

# Standard deviation & Simple Moving Average
daily['stddev'] = daily['close'].rolling(window=20).std()
daily['20sma'] = daily['close'].rolling(window=20).mean()

# Bollinger bands
daily['lower_bollinger'] = daily['20sma'] - (2 * daily['stddev'])
daily['upper_bollinger'] = daily['20sma'] + (2 * daily['stddev'])

# Average true range - volatility
daily['TR'] = abs(daily['high'] - daily['low'])
daily['ATR'] = daily['TR'].rolling(window=20).mean()

# Keltner channels
daily['lower_keltner'] = daily['20sma'] - (daily['ATR'] * 1.5)
daily['upper_keltner'] = daily['20sma'] + (daily['ATR'] * 1.5)


def low_volatility(df):
    return df['lower_bollinger'] > df['lower_keltner'] and df['upper_bollinger'] < df['upper_keltner']


daily['low_volatility'] = daily.apply(low_volatility, axis=1)

# 2021-06-14 00:00:00 fits on low_volatility checkup, which it could narrow down the liq range
print(daily['low_volatility']
      [daily['low_volatility'] == True].last_valid_index())

daily['upper_range_liq'] = np.where(
    daily['low_volatility'] == True, daily['upper_bollinger'] * 1.015, daily['upper_bollinger'] * 1.03)
daily['low_range_liq'] = np.where(daily['low_volatility'] == True,
                                  daily['lower_bollinger'] * 0.985, daily['lower_bollinger'] * 0.97)

# Reset otherwise cannot plot
daily.reset_index(level=0, inplace=True)


def plot(df):
    candlestick = graph.Candlestick(
        x=df['periodStartUnix'], open=df['open'], high=df['high'], low=df['low'], close=df['close'])
    upper_liq = graph.Scatter(
        x=df['periodStartUnix'], y=df['upper_range_liq'], name='Uniswap_v3_upper_range', line={'color': 'LightSkyBlue'})
    lower_liq = graph.Scatter(
        x=df['periodStartUnix'], y=df['low_range_liq'], name='Uniswap_v3_lower_range', line={'color': 'LightSkyBlue'})
    upper_bollinger = graph.Scatter(
        x=df['periodStartUnix'], y=df['upper_bollinger'], name='Upper Bollinger Band', line={'color': 'red'})
    lower_bollinger = graph.Scatter(
        x=df['periodStartUnix'], y=df['lower_bollinger'], name='Lower Bollinger Band', line={'color': 'red'})
    upper_keltner = graph.Scatter(
        x=df['periodStartUnix'], y=df['upper_keltner'], name='Upper Keltner Channel', line={'color': 'blue'})
    lower_keltner = graph.Scatter(
        x=df['periodStartUnix'], y=df['lower_keltner'], name='Lower Keltner Channel', line={'color': 'blue'})

    fig = graph.Figure(data=[candlestick, upper_bollinger,
                       lower_bollinger, upper_keltner, lower_keltner, upper_liq, lower_liq])

    # Historical insight between which bands liquidity could be provided accounting for volatility (relantionship between bollinger-keltner)
    fig.show()


plot(daily)
