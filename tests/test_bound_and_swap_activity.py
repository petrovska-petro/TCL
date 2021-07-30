import pytest
import random

from conftest import tickToPrice, feeInsideToTokenOwned, init_tcl


@pytest.mark.parametrize("swapDirection", [False, True])
@pytest.mark.parametrize("whale", [False, True])
def test_tcl_swaps(tcl, pool, swapper, pool_tokens, users, lp_user, swapDirection, whale):
    init_tcl(tcl, pool, pool_tokens, users)
    current_tick = pool.slot0()[1]
    boundRange = 1

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


@pytest.mark.parametrize("swapDirection", [False, True])
def test_tcl_swaps_day(tcl, pool, swapper, pool_tokens, tcl_positions_info, manager, users, lp_user, swapDirection):
    token0Amt = pool_tokens[0].balanceOf(users[3])
    token1Amt = pool_tokens[1].balanceOf(users[3])

    init_tcl(tcl, pool, pool_tokens, users)
    price = tickToPrice(pool)
    current_tick = pool.slot0()[1]

    print('Pre-swap price and tick: ', tickToPrice(pool), current_tick)

    print(tickToPrice(pool))
    tickSpacing = tcl.tickSpacing()
    range_width = 4000
    tickLower = (current_tick - range_width) // tickSpacing * tickSpacing
    tickUpper = (current_tick + range_width) // tickSpacing * tickSpacing
    boundRange = 1

    tcl.reinstateBound(tickLower, tickUpper, token0Amt,
                       token1Amt, boundRange, {"from": manager})

    print('Pre-swap activity: ', tcl.getTreasuryAmountAtBound(boundRange))

    for swap in range(15):
        if swapDirection:
            swapAmt = random.randint(1e18, 3e18)
        else:
            swapAmt = random.randint(300e18, 500e18)
        swapper.swap(pool, swapDirection, swapAmt, {"from": lp_user})

    # Update uncollected fees for inspection values in ´tcl_positions_info´ printouts
    tcl._uncollectedFeesUpdate(boundRange)
    _, middle_info, _ = tcl_positions_info(tcl)

    if swapDirection:
        assert tickToPrice(pool) < price
        print(
            f"Token0 fee owned: {feeInsideToTokenOwned(middle_info[1], middle_info[0])}")
    else:
        assert tickToPrice(pool) > price
        print(
            f"Token1 fee owned: {feeInsideToTokenOwned(middle_info[2], middle_info[0])}")

    print('After 15 swaps price: ', tickToPrice(pool))
    print('After 15 swaps activity: ', tcl.getTreasuryAmountAtBound(boundRange))
