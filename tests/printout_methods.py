from brownie import Wei
from conftest import tickToPrice


def stateOfTCL(tcl, pool, tcl_positions_info, initialAmt0, initialAmt1):
    _, middle_info, _ = tcl_positions_info(tcl)

    endAmt0, endAmt1 = tcl.getTreasuryAmountAtBound(1)
    print('Post trading activity: ', endAmt0.to('ether'), endAmt1.to('ether'))
    after_activity_price = tickToPrice(pool)
    print('After activity price: ', after_activity_price)
    tick_after = pool.slot0()[1]
    print('Tick after activity: ', tick_after)
    # It does not account for idle capital in TCL on purpose of uniquely comparing the initial lp deposit and the final lp position
    # Despite of not including it, there are printout as well above, making easier to see if position ends up being + or -
    impermanent_loss_calc(initialAmt0, initialAmt1,
                          endAmt0, endAmt1, after_activity_price, middle_info[3], middle_info[4])


def impermanent_loss_calc(initial_token0, initial_token1, end_token0, end_token1, end_price, uncollected_fees0, uncollected_fees1):
    starting_position = initial_token0 * end_price + initial_token1
    end_lp_position = end_token0 * end_price + end_token1 + \
        uncollected_fees0 * end_price + uncollected_fees1

    # expressed in token1 denomination
    il = Wei(end_lp_position - starting_position).to('ether')

    print("IL denominated in token1: ", il)
