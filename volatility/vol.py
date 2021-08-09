import pandas as pd
import numpy as np
from plotly.subplots import make_subplots
import plotly.graph_objects as graph
import json
import requests

url = 'https://api.thegraph.com/subgraphs/name/ianlapham/uniswapv2'
# create at timestamp 1607011509 on univ2
initial_timestamp = 1607011509
# ~ "2021/08/05"
current_time = 1628118000
query = '''
query ($pairAddress: Bytes!, $date: Int!)  {
  pairDayDatas(where: { 
      pairAddress: $pairAddress,
      date_gt: $date}) 
  {
    reserve0
    reserve1
    date
  }
}
'''

times = np.arange(start=initial_timestamp, stop=current_time, step=8582091)
print(times)
df_pair_data = pd.DataFrame(columns=['date', 'reserve0', 'reserve1'])

for t in times:
    variables = {'pairAddress': '0xcd7989894bc033581532d2cd88da5db0a4b12859',
                 'date': int(t)}
    try:
        r = requests.post(url, json={'query': query, 'variables': variables})

        json_data = json.loads(r.text)
        df_data = json_data['data']["pairDayDatas"]
        df = pd.DataFrame(df_data)
        df_pair_data = df_pair_data.append(df, ignore_index=True)
    except Exception as e:
        print(f'Error was {e}')

# from string to numerics
df_pair_data["reserve0"] = pd.to_numeric(df_pair_data["reserve0"], downcast="float")
df_pair_data["reserve1"] = pd.to_numeric(df_pair_data["reserve1"], downcast="float")
# from timestamp to date
df_pair_data['date'] = pd.to_datetime(
    df_pair_data['date'], unit='s')

df_pair_data['price'] = df_pair_data['reserve0'] / df_pair_data['reserve1']

logreturn = np.log(df_pair_data['price']/df_pair_data['price'].shift(1))
df_pair_data["logreturn"] = logreturn
std_daily = logreturn.std()

log_plot = graph.Histogram(x=logreturn.dropna())

fig = graph.Figure(data=[log_plot], layout={"title":"wbtc:badger pair - log returns", "width": 800, "height": 600})

# visuals
fig.show()

window_swap = 15
df_pair_data["volatility"] = logreturn.rolling(window=window_swap).std() * np.sqrt(window_swap)

multiplot = make_subplots(rows=1, cols=2, subplot_titles=("Historical Volatility", "Price (BADGER/WBTC)"))
vol_plot = graph.Scatter(
        x=df_pair_data['date'], y=df_pair_data['volatility'], name="volatility", line={'color': 'LightSkyBlue'})
price_plot = graph.Scatter(
        x=df_pair_data['date'], y=df_pair_data['price'], name='badger/wbtc price', line={'color': 'red'})

multiplot.add_trace(vol_plot, row=1, col=1)
multiplot.add_trace(price_plot, row=1, col=2)

fig.update_layout(height=600, width=800)

multiplot.show()

# generate csv
df_pair_data.to_csv('wbtc_badger_data.csv', index = False, header=True)

