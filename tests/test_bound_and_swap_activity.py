from brownie import reverts
import pytest


@pytest.mark.parametrize("swapDirection", [False, True])
@pytest.mark.parametrize("whale", [False, True])
def test_tcl_swaps(tcl, pool, swapper, pool_tokens, manager, treasury, lp_user, swapDirection, whale):

    token0Amt = 50e18
    token1Amt = 1500000e18
    # Transfer from treasury to TCL
    pool_tokens[0].transfer(tcl, token0Amt, {"from": treasury})
    pool_tokens[1].transfer(tcl, token1Amt, {"from": treasury})

    # Deploy in middle bound
    current_tick = pool.slot0()[1]
    print(current_tick)
    tickSpacing = tcl.tickSpacing()
    tickLower = (current_tick - 10 * tickSpacing) // tickSpacing * tickSpacing
    tickUpper = (current_tick + 10 * tickSpacing) // tickSpacing * tickSpacing
    boundRange = 1

    tcl.reinstateBound(tickLower, tickUpper, token0Amt,
                       token1Amt, boundRange, {"from": manager})

    print('Pre-swap: ', tcl.getTreasuryAmountAtBound(boundRange))

    # Swap action
    swapAmt = [750000e18, 25e18][swapDirection] * [0.5, 2][whale]
    print('swapAmt: ', swapAmt)
    print("pool_tokens[0]: ", pool_tokens[0].balanceOf(lp_user))
    print("pool_tokens[1]: ", pool_tokens[1].balanceOf(lp_user))
    swapper.swap(pool, swapDirection, swapAmt, {"from": lp_user})
    print("pool_tokens[0] swap: ", pool_tokens[0].balanceOf(lp_user))
    print("pool_tokens[1] swap: ", pool_tokens[1].balanceOf(lp_user))
    tick_after = pool.slot0()[1]
    print(tick_after)

    assert current_tick != tick_after

    print('Post-swap: ', tcl.getTreasuryAmountAtBound(boundRange))
