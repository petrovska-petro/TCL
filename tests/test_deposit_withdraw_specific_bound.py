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

    assert tx.events["ReinstateBound"] == {
        "boundRange": boundRange,
        "tickLower": tickLower,
        "tickUpper": tickUpper,
        "depositedAmount0": amount0Deploy,
        "depositedAmount1": amount1Deploy
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

    print('balance0:', pool_tokens[0].balanceOf(tcl))
    print('balance1:', pool_tokens[1].balanceOf(tcl))

    current_tick = pool.slot0()[1]

    tickSpacing = tcl.tickSpacing()
    tickLower = (current_tick - 2 * tickSpacing) // tickSpacing * tickSpacing
    tickUpper = (current_tick + 2 * tickSpacing) // tickSpacing * tickSpacing
    # middle bound
    boundRange = 1

    tcl.reinstateBound(tickLower, tickUpper, amount0Deploy,
                       amount1Deploy, boundRange, {"from": manager})
    
    tcl_positions_info(tcl)

    tx_pullout = tcl.controlLiquidity(
        tickLower, tickUpper, boundRange, pullOutAndIn, {"from": manager})

    mb = tcl.positions(boundRange)

    if pullOutAndIn:
        # Check proper records are stored in mapping
        assert mb[0] == tickLower
        assert mb[1] == tickUpper
        assert mb[2] == True

        tcl_positions_info(tcl)
        """
        assert tx_pullout.events["ReinstateBound"] == {
            "boundRange": boundRange,
            "tickLower": tickLower,
            "tickUpper": tickUpper,
            "depositedAmount0": amount0Deploy,
            "depositedAmount1": amount1Deploy
        }
        """
    else:
        # Check if struct has been ´delete´ properly
        assert mb[0] == 0
        assert mb[1] == 0
        assert mb[2] == False

        tcl_positions_info(tcl)
        """
        assert tx_pullout.events["Snapshot"] == {
            "tick": boundRange,
            "totalAmount0": amount0Deploy,
            "totalAmount1": amount1Deploy
        }
        """


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
