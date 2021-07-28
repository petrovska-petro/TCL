def test_emergency_liquidity_removal_and_transfer_funds(tcl, pool, pool_tokens, manager, treasury):
    # Provide max liq aprox ~ 3M of tWBTC & 3M of tBADGER
    token0Amt = 100e18
    token1Amt = 3000000e18
    # Transfer from treasury to TCL
    pool_tokens[0].transfer(tcl, token0Amt, {"from": treasury})
    pool_tokens[1].transfer(tcl, token1Amt, {"from": treasury})

    # Deploy in middle bound
    current_tick = pool.slot0()[1]
    tickSpacing = tcl.tickSpacing()
    tickLower = (current_tick - 10 * tickSpacing) // tickSpacing * tickSpacing
    tickUpper = (current_tick + 10 * tickSpacing) // tickSpacing * tickSpacing
    boundRange = 1

    tcl.reinstateBound(tickLower, tickUpper, token0Amt,
                       token1Amt, boundRange, {"from": manager})

    amount0, amount1 = tcl.getTreasuryAmountAtBound(boundRange)

    assert amount0 > 0 and amount1 > 0

    tcl.emergencyLiquidityRemoval({"from": manager})

    amountAfterRemoval0, amountAfterRemovalamount1 = tcl.getTreasuryAmountAtBound(
        boundRange)

    assert amountAfterRemoval0 == amountAfterRemovalamount1 == pool_tokens[0].balanceOf(
        treasury) == pool_tokens[1].balanceOf(treasury) == 0

    tcl.transferLiquidity(treasury, {"from": manager})

    assert pool_tokens[0].balanceOf(
        treasury) > 0 and pool_tokens[1].balanceOf(treasury) > 0
