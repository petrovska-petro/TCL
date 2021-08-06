import pandas as pd

# we assume there is not trading fee
init_reserve0 = 3.6 * 10 ** 6
init_reserve1 = init_reserve0 * .52
# selling chunk amount ~ swap activity in an hour perhaps
max_selling_pressure = 1.4 * 10 ** 6
divisor = 200
chunks = max_selling_pressure / divisor
# dataframe struct
df_swap = pd.DataFrame(columns=['trade_count', 'reserve0', 'reserve1', 'kLast','price_usd'])

# init values for df_swap
kLast_init = init_reserve0 * init_reserve1
price_usd_init = init_reserve1 / init_reserve0
df_swap.loc[0] = [0, init_reserve0, init_reserve1, kLast_init, price_usd_init]

for i in range(1, divisor + 1):
    last_record = df_swap.iloc[-1]
    reserve0 = last_record['reserve0'] + chunks
    reserve1 = last_record['kLast']/ reserve0
    kLast = reserve0 * reserve1
    price = reserve1 / reserve0
    df_swap.loc[i] = [i, reserve0, reserve1, kLast, price]

df_swap.to_csv('swap_history.csv', index = False, header=True)
