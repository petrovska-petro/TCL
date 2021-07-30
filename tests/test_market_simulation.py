import random
from printout_methods import stateOfTCL
from conftest import init_tcl


def test_passive_bound_low_vol(tcl, pool, swapper, tcl_positions_info, pool_tokens, users):
    init_tcl(tcl, pool, pool_tokens, users)
    initial_tick = pool.slot0()[1]

    print(initial_tick)
    initialAmt0, initialAmt1 = tcl.getTreasuryAmountAtBound(1)

    print('Pre-swap activity: ', initialAmt0.to('ether'), initialAmt1.to('ether'))

    # sort of ~220k USD volume/day
    for day in range(15):
        for swap_activity in range(65):
            swapDirection = random.choice([True, False])
            if swapDirection:
                swapAmt = random.randint(0.05e18, 0.1e18)
            else:
                swapAmt = random.randint(100e18, 200e18)
            swapper.swap(pool, swapDirection, swapAmt, {"from": users[1]})
            swapper.swap(pool, swapDirection, swapAmt, {"from": users[2]})

    tcl._uncollectedFeesUpdate(1)

    stateOfTCL(tcl, pool, tcl_positions_info, initialAmt0, initialAmt1)


def test_passive_bound_high_vol(tcl, pool, pool_tokens, swapper, tcl_positions_info, users):
    init_tcl(tcl, pool, pool_tokens, users)
    initial_tick = pool.slot0()[1]

    print(initial_tick)
    initialAmt0, initialAmt1 = tcl.getTreasuryAmountAtBound(1)

    print('Pre-swap activity: ', initialAmt0.to('ether'), initialAmt1.to('ether'))

    # mint plenty so all swapping activity is supported
    pool_tokens[0].mint(users[1], 100000e18, {"from": users[0]})
    pool_tokens[0].mint(users[2], 100000e18, {"from": users[0]})
    pool_tokens[1].mint(users[1], 43000000e18, {"from": users[0]})
    pool_tokens[1].mint(users[2], 43000000e18, {"from": users[0]})

    # sort of ~3MUSD volume/day during a 6d
    for day in range(6):
        for swap_activity in range(65):
            swapDirection = random.choice([True, False])
            if swapDirection:
                swapAmt = random.randint(0.2e18, 0.5e18)
            else:
                swapAmt = random.randint(80e18, 146e18)
            swapper.swap(pool, swapDirection, swapAmt, {"from": users[1]})
            swapper.swap(pool, swapDirection, swapAmt, {"from": users[2]})

    tcl._uncollectedFeesUpdate(1)

    stateOfTCL(tcl, pool, tcl_positions_info, initialAmt0, initialAmt1)
