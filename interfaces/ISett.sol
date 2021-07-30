//SPDX-License-Identifier: MIT
pragma solidity 0.7.6;

interface ISett {
    function deposit(uint256 _amount) external;

    function withdraw(uint256 _shares) external;
}
