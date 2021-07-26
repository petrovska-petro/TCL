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

#pm fixture provides access to packages install by manager!


@pytest.fixture
def pool(TestToken, pm, manager, users):
    Univ3Core = pm(UNISWAP_V3_CORE)

    # mocks BADGER - 18 decimals
    tokenA = manager.deploy(TestToken, "TEST_BADGER", "tBADGER", 18)
    # mocks WBTC - 8 decimals
    tokenB = manager.deploy(TestToken, "TEST_WBTC", "tWBTC", 8)

    factory = manager.deploy(Univ3Core.UniswapV3Factory)
    tx = factory.createPool(tokenA, tokenB, 3000, {"from": manager})
    pool = Univ3Core.interface.IUniswapV3Pool(tx.return_value)
    token0 = TestToken.at(pool.token0())
    token1 = TestToken.at(pool.token1())

    # initialize price to 38000
    price = int(sqrt(38000) * (1 << 96))
    pool.initialize(price, {"from": manager})

    for user in users:
        # mint 39k tBADGER
        token0.mint(user, 39000e18, {"from": manager})
        # mint 10 tWBTC
        token1.mint(user, 10e8, {"from": manager})

    yield pool


@pytest.fixture
def pool_tokens(TestToken, pool):
    return TestToken.at(pool.token0()), TestToken.at(pool.token1())


@pytest.fixture
def tcl(TCL, pool, tokens, manager, treasury):
    tcl = manager.deploy(TCL, pool)

    # approve treasury address to tx tokens
    tokens[0].approve(tcl, 39000e18, {"from": treasury})
    tokens[1].approve(tcl, 10e8, {"from": treasury})

    yield tcl


@pytest.fixture
def tcl_positions_info(pool, tokens):
    def method(tcl):
        # lower bound
        lb = tcl.positions[0]
        # middle bound
        mb = tcl.positions[1]
        # upper bound
        ub = tcl.positions[2]
        # keys
        lower_bound_key = computePositionKey(tcl, lb.tickLower, lb.tickUpper)
        middle_bound_key = computePositionKey(tcl, mb.tickLower, mb.tickUpper)
        upper_bound_key = computePositionKey(tcl, ub.tickLower, ub.tickUpper)
        # --- consoles ---
        print(f"Lower bound position: {pool.positions(lower_bound_key)}")
        print(f"Middle bound position: {pool.positions(middle_bound_key)}")
        print(f"Upper bound position: {pool.positions(upper_bound_key)}")
        # check idle tokens in TCL
        print(f"Idle balance 0:  {tokens[0].balanceOf(tcl)}")
        print(f"Idle balance 1:  {tokens[1].balanceOf(tcl)}")
    yield method


def computePositionKey(owner, tickLower, tickUpper):
    return Web3.solidityKeccak(
        ["address", "int24", "int24"], [str(owner), tickLower, tickUpper]
    )
