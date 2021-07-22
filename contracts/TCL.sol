//SPDX-License-Identifier: MIT
pragma solidity 0.7.6;

import "@openzeppelin/contracts/math/SafeMath.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/SafeERC20.sol";

import "@uniswap/v3-core/contracts/interfaces/IUniswapV3Pool.sol";
import "@uniswap/v3-core/contracts/interfaces/callback/IUniswapV3MintCallback.sol";
import "@uniswap/v3-core/contracts/libraries/TickMath.sol";

import "@uniswap/v3-periphery/contracts/libraries/PositionKey.sol";
import "@uniswap/v3-periphery/contracts/libraries/LiquidityAmounts.sol";

contract TCL is IUniswapV3MintCallback {
    using SafeERC20 for IERC20;
    using SafeMath for uint256;

    struct PositionInfo {
        int24 tickLower;
        int24 tickUpper;
        bool deployed;
    }

    // Uniswap v3 related variables
    IUniswapV3Pool public immutable pool;
    IERC20 public immutable token0;
    IERC20 public immutable token1;
    int24 public immutable tickSpacing;

    /*
     * 0: lower bound -> [lowerBoundLowerTick, lowerBoundUpperTick]
     * 1: middle bound -> [middleBoundLowerTick, middleBoundUpperTick]
     * 2: upper bound -> [upperBoundLowerTick, upperBoundUpperTick]
     */
    mapping(uint256 => PositionInfo) public positions;
    uint256 public positionsLength = 3;

    // Holds the ´virtual´ total fees accrued over time by this contract over time, it can help with performance tracking
    uint256 public accruedControlledFees0;
    uint256 public accruedControlledFees1;

    // Address with rights to control the liquidity
    address public manager;

    modifier onlyManager() {
        require(msg.sender == manager, "manager!");
        _;
    }

    event Snapshot(int24 tick, uint256 totalAmount0, uint256 totalAmount1);
    event ReinstateBound(
        uint256 boundRange,
        int24 tickLower,
        int24 tickUpper,
        uint256 depositedAmount0,
        uint256 depositedAmount1
    );
    event FeesEarned(uint256 feesLastPosition0, uint256 feesLastPosition1);

    /**
     * @param _pool Uniswap V3 pool
     **/
    constructor(address _pool) {
        pool = IUniswapV3Pool(_pool);
        token0 = IERC20(IUniswapV3Pool(_pool).token0());
        token1 = IERC20(IUniswapV3Pool(_pool).token1());
        tickSpacing = IUniswapV3Pool(_pool).tickSpacing();

        manager = msg.sender;
    }

    /**
     * @dev  Move liquidity to another range [_tickPositionLower, _tickPositionUpper] a specific bound
     * @param _tickPositionLower New lower tick
     * @param _tickPositionUpper New upper tick
     * @param _targetBound Liquidity bound to be targeted
     * @param _pullOutAndIn Liquidity will be pull out and in again if ´true´, otherwise uniquely pull out from prev ticks and keep it idle
     **/
    function controlLiquidity(
        int24 _tickPositionLower,
        int24 _tickPositionUpper,
        uint256 _targetBound,
        bool _pullOutAndIn
    ) external onlyManager {
        _controlLiquidity(
            _tickPositionLower,
            _tickPositionUpper,
            _targetBound,
            _pullOutAndIn
        );
    }

    /// @dev  Move all bounds liquidity simply out of the current ranges or deploy it to another range
    function controlAllLiquidity(
        int24[] memory _tickPositionsLower,
        int24[] memory _tickPositionsUpper,
        uint256[] memory _targetBounds,
        bool[] memory _pullsOutAndIn
    ) external onlyManager {
        for (uint256 i = 0; i < positionsLength; i++) {
            _controlLiquidity(
                _tickPositionsLower[i],
                _tickPositionsUpper[i],
                _targetBounds[i],
                _pullsOutAndIn[i]
            );
        }
    }

    function _controlLiquidity(
        int24 _tickPositionLower,
        int24 _tickPositionUpper,
        uint256 _targetBound,
        bool _pullOutAndIn
    ) internal {
        require(_targetBound <= positionsLength, "positionsLength!");
        _healthyRange(_tickPositionLower, _tickPositionUpper);

        (, int24 tick, , , , , ) = pool.slot0();
        // likely this ´require´ logic will be required to be tweak depending on the bound targeted(TOFIX!!)
        require(_tickPositionLower < tick, "_tickPositionLower!");
        require(_tickPositionUpper > tick, "_tickPositionUpper!");

        PositionInfo memory positionInfo = positions[_targetBound];

        (uint128 positionLiquidity, , , , ) = _positionKeyInfo(
            positionInfo.tickLower,
            positionInfo.tickUpper
        );

        _burnPositionAndFeeCollection(
            positionInfo.tickLower,
            positionInfo.tickUpper,
            positionLiquidity
        );

        uint256 balance0 = balanceToken0();
        uint256 balance1 = balanceToken1();

        if (_pullOutAndIn) {
            uint128 liquidity = _liquidityForAmounts(
                _tickPositionLower,
                _tickPositionUpper,
                balance0,
                balance1
            );

            _mintPosition(_tickPositionLower, _tickPositionUpper, liquidity);

            positions[_targetBound] = PositionInfo({
                tickLower: _tickPositionLower,
                tickUpper: _tickPositionUpper,
                deployed: true
            });

            emit ReinstateBound(
                _targetBound,
                _tickPositionLower,
                _tickPositionUpper,
                balance0,
                balance1
            );
        } else {
            delete positions[_targetBound];

            emit Snapshot(tick, balance0, balance1);
        }
    }

    /**
     * @dev  Reinstate a specific bound of liquidity
     * @param _tickPositionLower New lower tick
     * @param _tickPositionUpper New upper tick
     * @param _targetBound Liquidity bound to be targeted
     **/
    function reinstateBound(
        int24 _tickPositionLower,
        int24 _tickPositionUpper,
        uint256 _targetBound
    ) external onlyManager {
        _healthyRange(_tickPositionLower, _tickPositionUpper);

        require(positions[_targetBound].deployed != true, "true!");

        uint256 balance0 = balanceToken0();
        uint256 balance1 = balanceToken1();

        uint128 liquidity = _liquidityForAmounts(
            _tickPositionLower,
            _tickPositionUpper,
            balance0,
            balance1
        );

        _mintPosition(_tickPositionLower, _tickPositionUpper, liquidity);

        positions[_targetBound] = PositionInfo({
            tickLower: _tickPositionLower,
            tickUpper: _tickPositionUpper,
            deployed: true
        });

        emit ReinstateBound(
            _targetBound,
            _tickPositionLower,
            _tickPositionUpper,
            balance0,
            balance1
        );
    }

    /// @dev Checks in given ticks are healthy and (%) operation following tickSpacing from the pool
    function _healthyRange(int24 tickLower, int24 tickUpper) internal view {
        require(tickLower < tickUpper, "tickLower>tickUpper");
        require(tickLower % tickSpacing == 0, "tickLower%tickSpacing");
        require(tickUpper % tickSpacing == 0, "tickUpper%tickSpacing");
    }

    /// @dev Deposits liquidity in a range on the Uniswap pool.
    function _mintPosition(
        int24 tickLower,
        int24 tickUpper,
        uint128 liquidity
    ) internal {
        require(liquidity > 0, "liquidity!");
        pool.mint(address(this), tickLower, tickUpper, liquidity, "");
    }

    /// @dev Withdraws liquidity from pool and collect fees
    function _burnPositionAndFeeCollection(
        int24 tickLower,
        int24 tickUpper,
        uint128 liquidity
    ) internal returns (uint256 burned0, uint256 burned1) {
        require(liquidity > 0, "liquidity!");
        (burned0, burned1) = pool.burn(tickLower, tickUpper, liquidity);

        (uint256 amount0, uint256 amount1) = pool.collect(
            address(this),
            tickLower,
            tickUpper,
            type(uint128).max,
            type(uint128).max
        );

        uint256 feesLastPosition0 = amount0.sub(burned0);
        uint256 feesLastPosition1 = amount1.sub(burned1);

        accruedControlledFees0 = accruedControlledFees0.add(feesLastPosition0);
        accruedControlledFees1 = accruedControlledFees1.add(feesLastPosition1);

        emit FeesEarned(feesLastPosition0, feesLastPosition1);
    }

    /// @notice Balance of token0 idle, ideally none
    function balanceToken0() public view returns (uint256) {
        return token0.balanceOf(address(this));
    }

    /// @notice Balance of token1 idle, ideally none
    function balanceToken1() public view returns (uint256) {
        return token1.balanceOf(address(this));
    }

    /// @dev Token0 and Token1 amounts held by TCL in the pool
    function getTreasuryPositionAmounts()
        public
        view
        returns (uint256 amountTotal0, uint256 amountTotal1)
    {
        for (uint256 i = 0; i < positionsLength; i++) {
            PositionInfo memory positionInfo = positions[i];

            if (positionInfo.deployed) {
                (uint128 liquidity, , , , ) = _positionKeyInfo(
                    positionInfo.tickLower,
                    positionInfo.tickUpper
                );

                (uint256 amount0, uint256 amount1) = _amountsForLiquidity(
                    positionInfo.tickLower,
                    positionInfo.tickUpper,
                    liquidity
                );

                amountTotal0 = amountTotal0.add(amount0);
                amountTotal1 = amountTotal1.add(amount1);
            }
        }
    }

    /// @dev Wrapper around `IUniswapV3Pool.positions()`.
    function _positionKeyInfo(int24 tickLower, int24 tickUpper)
        internal
        view
        returns (
            uint128,
            uint256,
            uint256,
            uint128,
            uint128
        )
    {
        bytes32 positionKey = PositionKey.compute(
            address(this),
            tickLower,
            tickUpper
        );
        return pool.positions(positionKey);
    }

    /// @dev Wrapper around `LiquidityAmounts.getAmountsForLiquidity()`.
    function _amountsForLiquidity(
        int24 tickLower,
        int24 tickUpper,
        uint128 liquidity
    ) internal view returns (uint256, uint256) {
        (uint160 sqrtRatioX96, , , , , , ) = pool.slot0();
        return
            LiquidityAmounts.getAmountsForLiquidity(
                sqrtRatioX96,
                TickMath.getSqrtRatioAtTick(tickLower),
                TickMath.getSqrtRatioAtTick(tickUpper),
                liquidity
            );
    }

    /// @dev Wrapper around `LiquidityAmounts.getLiquidityForAmounts()`.
    function _liquidityForAmounts(
        int24 tickLower,
        int24 tickUpper,
        uint256 amount0,
        uint256 amount1
    ) internal view returns (uint128) {
        (uint160 sqrtRatioX96, , , , , , ) = pool.slot0();
        return
            LiquidityAmounts.getLiquidityForAmounts(
                sqrtRatioX96,
                TickMath.getSqrtRatioAtTick(tickLower),
                TickMath.getSqrtRatioAtTick(tickUpper),
                amount0,
                amount1
            );
    }

    /// @dev Any contract that calls IUniswapV3PoolActions#mint must implement this interface
    function uniswapV3MintCallback(
        uint256 amount0,
        uint256 amount1,
        bytes calldata data
    ) external override {
        require(msg.sender == address(pool));
        if (amount0 > 0) token0.safeTransfer(msg.sender, amount0);
        if (amount1 > 0) token1.safeTransfer(msg.sender, amount1);
    }

    /// @dev Removes available liquidity from TCL to another destination
    function transferLiquidity(address _destination) external onlyManager {
        uint256 balance0 = balanceToken0();
        uint256 balance1 = balanceToken1();

        token0.safeTransfer(_destination, balance0);
        token1.safeTransfer(_destination, balance1);
    }

    /// @dev Removes all liquidity from pool into contract
    function emergencyLiquidityRemoval(
        int24 tickLower,
        int24 tickUpper,
        uint128 liquidity
    ) external onlyManager {
        for (uint256 i = 0; i < positionsLength; i++) {
            PositionInfo memory positionInfo = positions[i];

            if (positionInfo.deployed) {
                pool.burn(
                    positionInfo.tickLower,
                    positionInfo.tickUpper,
                    liquidity
                );
                pool.collect(
                    address(this),
                    positionInfo.tickLower,
                    positionInfo.tickUpper,
                    type(uint128).max,
                    type(uint128).max
                );

                delete positions[i];
            }
        }
    }
}
