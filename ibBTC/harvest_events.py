from web3 import Web3
import pandas as pd
from datetime import datetime
from abi import abi_strat
from plotly.subplots import make_subplots
import plotly.graph_objects as graph

# from example
ibBTC_tokenyield_retain_pct = 0.5
ibBTC_excesstokenyield_to_DAO_pct = 0.5
max_partnerttoken_sell_pct = 0.2
performance_fee_pct = 0.2
ibBTC_tokenyield_pct = 0.15

CVX_USD_PRICE = 5
BTC_USD_PRICE = 40000

RATIO = CVX_USD_PRICE / BTC_USD_PRICE

w3 = Web3(
    Web3.HTTPProvider("https://mainnet.infura.io/v3/d254f1cdd9454d5b9dba75a6b68f12d2")
)

cvx_strat = "0xBCee2c6CfA7A4e29892c3665f464Be5536F16D95"

strat_contract = w3.eth.contract(address=cvx_strat, abi=abi_strat)

ev = strat_contract.events.Tend

last_block = w3.eth.block_number

events = ev.getLogs(fromBlock=12691828, toBlock=last_block)

values = []
df = pd.DataFrame(
    columns=[
        "transactionHash",
        "date",
        "harvested_amount",
        "tokens_to_depositors",
        "tokens_to_dao",
        "wbtc_to_ibBTC_new",
        "ibBTC_to_depositors_new",
        "tokens_to_dao_new",
        "tokens_to_depositors_new",
    ]
)

for i in range(len(events)):
    harvested_tokens = int(events[i].args.tended) / 10 ** 18
    tokens_to_dao = harvested_tokens * 0.1
    tokens_to_depositors = harvested_tokens - tokens_to_dao

    # new distribution
    wbtc_to_ibBTC_new = (
        (ibBTC_tokenyield_pct * ibBTC_tokenyield_retain_pct) * harvested_tokens * RATIO
    )
    ibBTC_to_depositors_new = (
        (
            max_partnerttoken_sell_pct
            - (ibBTC_tokenyield_retain_pct * ibBTC_tokenyield_pct)
        )
        * harvested_tokens
        * RATIO
    )
    tokens_to_dao_new = (
        performance_fee_pct
        + (
            ibBTC_tokenyield_pct
            * ibBTC_tokenyield_retain_pct
            * ibBTC_excesstokenyield_to_DAO_pct
        )
    ) * harvested_tokens

    tokens_to_depositors_new = (
        (1 - (max_partnerttoken_sell_pct + performance_fee_pct))
        - (
            ibBTC_tokenyield_pct
            * ibBTC_tokenyield_retain_pct
            * (1 - ibBTC_excesstokenyield_to_DAO_pct)
        )
    ) * harvested_tokens

    block_to_ts = w3.eth.getBlock(events[i].blockNumber).timestamp
    date = datetime.fromtimestamp(block_to_ts)

    df.loc[i + 1] = [
        events[i].transactionHash.hex(),
        date,
        harvested_tokens,
        tokens_to_depositors,
        tokens_to_dao,
        wbtc_to_ibBTC_new,
        ibBTC_to_depositors_new,
        tokens_to_dao_new,
        tokens_to_depositors_new,
    ]

df["cum_tokens_to_depositors"] = df["tokens_to_depositors"].cumsum()
df["cum_tokens_to_dao"] = df["tokens_to_dao"].cumsum()

# cumulative sum for new distributions
df["cum_wbtc_to_ibBTC_new"] = df["wbtc_to_ibBTC_new"].cumsum()
df["cum_ibBTC_to_depositors_new"] = df["ibBTC_to_depositors_new"].cumsum()
df["cum_tokens_to_dao_new"] = df["tokens_to_dao_new"].cumsum()
df["cum_tokens_to_depositors_new"] = df["tokens_to_depositors_new"].cumsum()

df.to_csv("harvest_history.csv", index=False, header=True)

multiplot = make_subplots(
    rows=1,
    cols=3,
    subplot_titles=(
        "Old distribution - harvest - CVX",
        "New distribution - harvest - CVX",
        "New distribution - harvest - WBTC",
    ),
)

cum_depositors = graph.Scatter(
    x=df["date"],
    y=df["cum_tokens_to_depositors"],
    name="Cumulative tokens to depositors",
    line={"color": "red"},
)
cum_dao = graph.Scatter(
    x=df["date"],
    y=df["cum_tokens_to_dao"],
    name="Cumulative tokens to DAO",
    line={"color": "blue"},
)

multiplot.add_trace(cum_depositors, row=1, col=1)
multiplot.add_trace(cum_dao, row=1, col=1)

# plots - cumulative sum for new distributions
cum_dao_new = graph.Scatter(
    x=df["date"],
    y=df["cum_tokens_to_dao_new"],
    name="Cumulative tokens to DA0",
    line={"color": "magenta"},
)
cum_depositors_new = graph.Scatter(
    x=df["date"],
    y=df["cum_tokens_to_depositors_new"],
    name="Cumulative tokens to depositors",
    line={"color": "orange"},
)

multiplot.add_trace(cum_dao_new, row=1, col=2)
multiplot.add_trace(cum_depositors_new, row=1, col=2)

cum_wbtc_to_ibBTC = graph.Scatter(
    x=df["date"],
    y=df["cum_wbtc_to_ibBTC_new"],
    name="Cumulative WBTC to ibBTC",
    line={"color": "yellowgreen"},
)
cum_ibBTC_to_depositors = graph.Scatter(
    x=df["date"],
    y=df["cum_ibBTC_to_depositors_new"],
    name="Cumulative ibBTC to depositors",
    line={"color": "steelblue"},
)

multiplot.add_trace(cum_wbtc_to_ibBTC, row=1, col=3)
multiplot.add_trace(cum_ibBTC_to_depositors, row=1, col=3)

multiplot.show()
