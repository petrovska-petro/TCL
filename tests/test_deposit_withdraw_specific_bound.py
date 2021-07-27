from brownie import chain, reverts
import pytest


@pytest.mark.parametrize(
    "amount0Deploy,amount1Deploy",
    [[207197e18, 50e8], [414394e18, 100e8]],
)
def test_treasury_depositing(tcl, pool_tokens, manager, treasury, amount0Deploy, amount1Deploy):
    tickSpacing = tcl.tickSpacing()

    # Transfer from treasury to TCL
    pool_tokens[0].transfer(tcl, amount0Deploy)
    pool_tokens[1].transfer(tcl, amount1Deploy)

    assert pool_tokens[0].balanceOf(tcl) == amount0Deploy
    assert pool_tokens[1].balanceOf(tcl) == amount1Deploy

    # Reinstate action test
    tickLower = 1 * tickSpacing
    tickUpper = 12 * tickSpacing
    # middle bound
    boundRange = 1
    tx = tcl.reinstateBound(tickLower, tickUpper, amount0Deploy,
                            amount1Deploy, boundRange, {"from": manager})

    amountTotal0, amountTotal1 = tcl.getTreasuryAmountAtBound(boundRange)

    assert tx.events["ReinstateBound"] == {
        "boundRange": boundRange,
        "tickLower": tickLower,
        "tickUpper": tickUpper,
        "depositedAmount0": amountTotal0,
        "depositedAmount1": amountTotal1
    }


def test_reinstate_checks(tcl, pool_tokens, manager):
    tickSpacing = tcl.tickSpacing()
    pool_tokens[0].transfer(tcl, 19500e18)

    with reverts("tickLower>tickUpper"):
        tcl.reinstateBound(10 * tickSpacing, 2 * tickSpacing, 0,
                           0, 1, {"from": manager})
    with reverts("tickLower%tickSpacing"):
        tcl.reinstateBound(10, 2*tickSpacing, 0,
                           0, 1, {"from": manager})
    with reverts("tickUpper%tickSpacing"):
        tcl.reinstateBound(10 * tickSpacing, 2500, 0,
                           0, 1, {"from": manager})
    with reverts("balance0!"):
        tcl.reinstateBound(10 * tickSpacing, 20 * tickSpacing, 59000e18,
                           0, 1, {"from": manager})
    with reverts("balance1!"):
        tcl.reinstateBound(10 * tickSpacing, 20 * tickSpacing, 19500e18,
                           13e8, 1, {"from": manager})


@pytest.mark.parametrize(
    "amount0Deploy,amount1Deploy,pullOutAndIn",
    [[207197e18, 50e8, False], [414394e18, 100e8, True]],
)
def test_controlLiquidity(tcl, pool, pool_tokens, tcl_positions_info, manager, amount0Deploy, amount1Deploy, pullOutAndIn):
    # Transfer from treasury to TCL
    pool_tokens[0].transfer(tcl, amount0Deploy)
    pool_tokens[1].transfer(tcl, amount1Deploy)

    current_tick = pool.slot0()[1]

    tickSpacing = tcl.tickSpacing()
    tickLower = (current_tick - 20 * tickSpacing) // tickSpacing * tickSpacing
    tickUpper = (current_tick + 20 * tickSpacing) // tickSpacing * tickSpacing
    # middle bound
    boundRange = 1

    tcl.reinstateBound(tickLower, tickUpper, amount0Deploy,
                       amount1Deploy, boundRange, {"from": manager})

    print('reinstateBound(): ',  tcl.getTreasuryAmountAtBound(boundRange))

    tickLowerPullOut = (current_tick - 50 *
                        tickSpacing) // tickSpacing * tickSpacing
    tickUpperPullOut = (current_tick + 50 *
                        tickSpacing) // tickSpacing * tickSpacing

    tx_pullout = tcl.controlLiquidity(
        tickLowerPullOut, tickUpperPullOut, boundRange, pullOutAndIn, {"from": manager})

    mb = tcl.positions(boundRange)

    amountTotal0, amountTotal1 = tcl.getTreasuryAmountAtBound(boundRange)

    if pullOutAndIn:
        # Check proper records are stored in mapping
        assert mb[0] == tickLowerPullOut
        assert mb[1] == tickUpperPullOut
        assert mb[2] == True

        print(amountTotal0, amountTotal1)

        assert tx_pullout.events["ReinstateBound"] == {
            "boundRange": boundRange,
            "tickLower": tickLowerPullOut,
            "tickUpper": tickUpperPullOut,
            "depositedAmount0": amountTotal0,
            "depositedAmount1": amountTotal1
        }
    else:
        # Check if struct has been ´delete´ properly
        assert mb[0] == 0
        assert mb[1] == 0
        assert mb[2] == False

        print(amountTotal0, amountTotal1)

        assert tx_pullout.events["Snapshot"]["tick"] == current_tick


def test_controlLiquidity_checks(tcl, pool, manager):
    current_tick = pool.slot0()[1]
    tickSpacing = tcl.tickSpacing()
    tickLower = (current_tick - 2 * tickSpacing) // tickSpacing * tickSpacing
    tickUpper = (current_tick + 200 * tickSpacing) // tickSpacing * tickSpacing

    with reverts("positionsLength!"):
        tcl.controlLiquidity(
            tickLower, tickUpper, 10, False, {"from": manager})
    with reverts("_tickPositionLower!"):
        tcl.controlLiquidity(
            (current_tick + tickSpacing) // tickSpacing * tickSpacing, tickUpper, 1, False, {"from": manager})
    with reverts("_tickPositionUpper!"):
        tcl.controlLiquidity(
            tickLower, (current_tick - tickSpacing) // tickSpacing * tickSpacing, 1, False, {"from": manager})
    with reverts("tickLower<0.5x!"):
        tcl.controlLiquidity(
            (current_tick / 2) // tickSpacing * tickSpacing, current_tick // tickSpacing * tickSpacing, 0, False, {"from": manager})
    with reverts("tickUpper>2x"):
        tcl.controlLiquidity(
            current_tick * 1.02 // tickSpacing * tickSpacing, (current_tick * 2) // tickSpacing * tickSpacing, 2, False, {"from": manager})