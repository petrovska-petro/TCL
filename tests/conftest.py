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
    # tickSpacing is retrieved from the fee -> 60
    tx = factory.createPool(tokenA, tokenB, 3000, {"from": manager})
    pool = Univ3Core.interface.IUniswapV3Pool(tx.return_value)
    token0 = TestToken.at(pool.token0())
    token1 = TestToken.at(pool.token1())

    # initialize price to 30k
    price = int(sqrt(30000) * (1 << 96))
    pool.initialize(price, {"from": manager})

    for user in users:
        # mint 100 tWBTC and approve pool
        token0.mint(user, 100e18, {"from": manager})
        token0.approve(swapper, 100e18, {"from": user})
        # mint 3000000 tBADGER and approve pool
        token1.mint(user, 3000000e18, {"from": manager})
        token1.approve(swapper, 3000000e18, {"from": user})

    yield pool


@pytest.fixture
def pool_tokens(TestToken, pool):
    return TestToken.at(pool.token0()), TestToken.at(pool.token1())


@pytest.fixture
def tcl(TCL, pool, pool_tokens, manager, treasury):
    tcl = manager.deploy(TCL, pool)

    # approve treasury address to tx tokens
    pool_tokens[0].approve(tcl, 100e18, {"from": treasury})
    pool_tokens[1].approve(tcl, 3000000e18, {"from": treasury})

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
        print("------------------------------------")
        print(f"Lower bound position: {pool.positions(lower_bound_key)}")
        print(f"Middle bound position: {pool.positions(middle_bound_key)}")
        print(f"Upper bound position: {pool.positions(upper_bound_key)}")
        # check idle tokens in TCL
        print(f"Idle balance 0:  {pool_tokens[0].balanceOf(tcl)}")
        print(f"Idle balance 1:  {pool_tokens[1].balanceOf(tcl)}")
        print("------------------------------------")
    yield method


def computePositionKey(owner, tickLower, tickUpper):
    return Web3.solidityKeccak(
        ["address", "int24", "int24"], [str(owner), tickLower, tickUpper]
    )
