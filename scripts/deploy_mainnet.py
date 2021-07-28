from brownie import accounts, TCL
from brownie.network.gas.strategies import GasNowScalingStrategy


pool = ""


def main():
    manager = accounts.load("manager")

    gas_strategy = GasNowScalingStrategy()

    # Attempts to verify the source code on etherscan too
    tcl = manager.deploy(TCL, pool, publish_source=True,
                         gas_price=gas_strategy)

    print(f"TCL address: {tcl.address}")
