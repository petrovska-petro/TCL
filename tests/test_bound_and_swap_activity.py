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
    swapAmt = [140857e18, 25e18][swapDirection] * [0.5, 2][whale]
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

    tickSpacing = 60
    tickLower = (tick_after - 5000) // tickSpacing * tickSpacing
    tickUpper = (tick_after + 5000) // tickSpacing * tickSpacing

    tcl.controlLiquidity(
        tickLower, tickUpper, boundRange, True, {"from": users[0]})

    # verify fees where sent succesfully to treasury address on burn&collect combo
    balance0_plus_fee = pool_tokens[0].balanceOf(users[3])
    balance1_plus_fee = pool_tokens[1].balanceOf(users[3])

    if swapDirection:
        assert balance0_plus_fee > 0
    else:
        assert balance1_plus_fee > 0


@pytest.mark.parametrize("swapDirection", [False, True])
def test_tcl_swaps_day(tcl, pool, swapper, pool_tokens, tcl_positions_info, users, lp_user, swapDirection):
    init_tcl(tcl, pool, pool_tokens, users)
    price = tickToPrice(pool)
    boundRange = 1

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
