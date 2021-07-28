## Treasury Controlled Liquidity

The scope of the contracts is to manage the liquidity provided by the treasury in Uniswap v3 pool.

## Requirements

`brownie pm clone OpenZeppelin/openzeppelin-contracts@3.4.0`

`brownie pm clone Uniswap/uniswap-v3-core@1.0.0`

`brownie pm clone Uniswap/uniswap-v3-periphery@1.0.0`

## Research Ranges

Running: `python3 research_ranges/ranges.py` will grab the ticks since 5th May to 4th June from the Uniswap v3 pool WBTC / USDC, which would be used to define the OHLC tick candles.

The idea is to provide a possible approach on how to define the middle bound interval, where liquidity would be provided accordangly to relantionship between Bollinger Bands and Keltner Channel, which is possibly the range where more swapping will occur.

Periods of low volatily will be define by the following method, which when the conditions is satisfied, it could allow narrower ranges as spikes are not much expected:

````
def low_volatility(df):
    return df['lower_bollinger'] > df['lower_keltner'] and df['upper_bollinger'] < df['upper_keltner']
````

Then, ranges would be define depending on the level of volatility.

High volatility: `[daily['lower_bollinger'] * 0.97, daily['upper_bollinger'] * 1.03]`

Low volatility: `[daily['lower_bollinger'] * 0.985, daily['upper_bollinger'] * 1.015]`

## Documentation

You can read further details of the mechanism of TCL contract on [notion_notes](https://www.notion.so/).

## Credits

Charm finance protocol repository has been really valuable while reading their contracts and tests to have a better picture
on how to manage liquidity in Uniswap v3, since they are one of the few protocol making profit in this game.