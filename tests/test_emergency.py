from conftest import init_tcl


def test_emergency_liquidity_removal_and_transfer_funds(tcl, pool, pool_tokens, users):
    init_tcl(tcl, pool, pool_tokens, users)

    amount0, amount1 = tcl.getTreasuryAmountAtBound(1)

    assert amount0 > 0 and amount1 > 0

    tcl.emergencyLiquidityRemoval({"from": users[0]})

    amountAfterRemoval0, amountAfterRemovalamount1 = tcl.getTreasuryAmountAtBound(
        1)

    assert amountAfterRemoval0 == amountAfterRemovalamount1 == 0

    assert pool_tokens[0].balanceOf(
        users[0]) > 0 and pool_tokens[1].balanceOf(users[0]) > 0

    tcl.transferLiquidity(users[3], {"from":  users[0]})

    assert pool_tokens[0].balanceOf(
        users[3]) > 0 and pool_tokens[1].balanceOf(users[3]) > 0
