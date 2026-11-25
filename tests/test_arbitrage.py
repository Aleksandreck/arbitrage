"""
Unit-тесты для логики расчёта арбитражного спреда.

Запуск:  pytest -v
"""
from src.arbitrage import calculate_opportunity
from src.models import Ticker


def test_positive_arbitrage_after_fees():
    """
    Ситуация: на Binance ask=100, на Bybit bid=101.
    Валовый спред = 1%, комиссии по 0.1% с каждой стороны => чистыми 0.8%.
    Ожидаем, что функция вернёт возможность с net_spread_pct == 0.8.
    """
    buy_ticker = Ticker(exchange="binance", symbol="BTC/USDT", bid=100.0, ask=100.0, last=100.0)
    sell_ticker = Ticker(exchange="bybit", symbol="BTC/USDT", bid=101.0, ask=101.0, last=101.0)

    opportunity = calculate_opportunity(
        symbol="BTC/USDT",
        buy_ticker=buy_ticker,
        sell_ticker=sell_ticker,
        buy_fee_pct=0.1,
        sell_fee_pct=0.1,
    )

    assert opportunity is not None
    assert opportunity.gross_spread_pct == 1.0
    assert opportunity.net_spread_pct == 0.8


def test_no_arbitrage_when_fees_eat_spread():
    """
    Ситуация: спред всего 0.05%, а комиссии суммарно 0.2%.
    Чистая прибыль отрицательная => функция должна вернуть None.
    """
    buy_ticker = Ticker(exchange="binance", symbol="BTC/USDT", bid=100.0, ask=100.0, last=100.0)
    sell_ticker = Ticker(exchange="bybit", symbol="BTC/USDT", bid=100.05, ask=100.05, last=100.05)

    opportunity = calculate_opportunity(
        symbol="BTC/USDT",
        buy_ticker=buy_ticker,
        sell_ticker=sell_ticker,
        buy_fee_pct=0.1,
        sell_fee_pct=0.1,
    )

    assert opportunity is None
