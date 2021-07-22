from brownie import chain
import pytest


@pytest.fixture(scope="module")
def manager(accounts):
    yield accounts[0]


@pytest.fixture(scope="module")
def lp_user(accounts):
    yield accounts[1]


@pytest.fixture(scope="module")
def users(manager, lp_user):
    yield [manager, lp_user]
