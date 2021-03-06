from brownie import chain
import pytest
from math import sqrt
from web3 import Web3

UNISWAP_V3_CORE = "Uniswap/uniswap-v3-core@1.0.0"


@pytest.fixture(scope="module")
def manager(accounts):
    yield accounts[0]


@pytest.fixture(scope="module")
def lp_user(accounts):
    yield accounts[1]


@pytest.fixture(scope="module")
def lp_second_user(accounts):
    yield accounts[2]


@pytest.fixture(scope="module")
def treasury(accounts):
    yield accounts[3]


@pytest.fixture(scope="module")
def users(manager, lp_user, lp_second_user, treasury):
    yield [manager, lp_user, lp_second_user, treasury]


@pytest.fixture(scope="module")
def swapper(TestSwapper, manager):
    yield manager.deploy(TestSwapper)

#pm fixture provides access to packages install by manager!


@pytest.fixture
def pool(TestToken, swapper, pm, manager, users):
    Univ3Core = pm(UNISWAP_V3_CORE)

    # mocks tBADGER
    tokenA = manager.deploy(TestToken, "TEST_WBTC", "tWBTC", 18)
    # mocks tWBTC
    tokenB = manager.deploy(TestToken, "TEST_BADGER", "tBADGER", 18)

    factory = manager.deploy(Univ3Core.UniswapV3Factory)
    #¬†tickSpacing is retrieved from the fee -> 60
    tx = factory.createPool(tokenA, tokenB, 3000, {"from": manager})
    pool = Univ3Core.interface.IUniswapV3Pool(tx.return_value)
    token0 = TestToken.at(pool.token0())
    token1 = TestToken.at(pool.token1())

    # initialize price as sqrt(amountToken1/amountToken0) Q64.96 value
    price = int(sqrt(285714/100) * (1 << 96))
    pool.initialize(price, {"from": manager})

    for user in users:
        # mint 100 tWBTC and approve pool - 100e18
        token0.mint(user, 100e18, {"from": manager})
        token0.approve(swapper, 100e18, {"from": user})
        # mint 285714 tBADGER and approve pool
        token1.mint(user, 285714e18, {"from": manager})
        token1.approve(swapper, 285714e18, {"from": user})

    yield pool


@pytest.fixture
def pool_tokens(TestToken, pool):
    return TestToken.at(pool.token0()), TestToken.at(pool.token1())


@pytest.fixture
def tcl(TCL, pool, pool_tokens, manager, treasury):
    tcl = manager.deploy(TCL, pool, treasury)

    # approve treasury address to tx tokens
    pool_tokens[0].approve(tcl, 100e18, {"from": treasury})
    pool_tokens[1].approve(tcl, 285714e18, {"from": treasury})

    yield tcl


@pytest.fixture
def tcl_positions_info(pool, pool_tokens):
    def method(tcl):
        # lower bound
        lb = tcl.positions(0)
        # middle bound
        mb = tcl.positions(1)
        # upper bound
        ub = tcl.positions(2)
        # keys
        lower_bound_key = computePositionKey(tcl, lb[0], lb[1])
        middle_bound_key = computePositionKey(tcl, mb[0], mb[1])
        upper_bound_key = computePositionKey(tcl, ub[0], ub[1])
        # --- consoles ---
        lower_info = pool.positions(lower_bound_key)
        middle_info = pool.positions(middle_bound_key)
        upper_info = pool.positions(upper_bound_key)
        print("------------------------------------")
        print(f"Lower bound position: {lower_info}")
        print(f"Middle bound position: {middle_info}")
        print(f"Upper bound position: {upper_info}")
        #¬†check idle tokens in TCL
        print(f"Idle balance 0:  {pool_tokens[0].balanceOf(tcl).to('ether')}")
        print(f"Idle balance 1:  {pool_tokens[1].balanceOf(tcl).to('ether')}")
        print("------------------------------------")
        return [lower_info, middle_info, upper_info]
    yield method


def computePositionKey(owner, tickLower, tickUpper):
    return Web3.solidityKeccak(
        ["address", "int24", "int24"], [str(owner), tickLower, tickUpper]
    )


def tickToPrice(pool):
    sqrtPrice = pool.slot0()[0] / (1 << 96)
    return sqrtPrice ** 2


def feeInsideToTokenOwned(fee, liquidity):
    return (fee * liquidity) / 2**128


def init_tcl(tcl, pool, pool_tokens, users):
    # Transfer from treasury to TCL
    amount0 = pool_tokens[0].balanceOf(users[3])
    amount1 = pool_tokens[1].balanceOf(users[3])
    pool_tokens[0].transfer(tcl, amount0, {"from": users[3]})
    pool_tokens[1].transfer(tcl, amount1, {"from": users[3]})

    current_tick = pool.slot0()[1]

    tickSpacing = tcl.tickSpacing()
    range_width = 4500
    tickLower = (current_tick - range_width) // tickSpacing * tickSpacing
    tickUpper = (current_tick + range_width) // tickSpacing * tickSpacing
    # middle bound
    boundRange = 1

    tcl.reinstateBound(tickLower, tickUpper, amount0,
                       amount1, boundRange, {"from": users[0]})
