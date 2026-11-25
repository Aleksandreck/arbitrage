"""
Структуры данных проекта.

Здесь описаны «модели» — простые контейнеры для тикеров и найденных
арбитражных возможностей. Используем dataclass, чтобы не писать
__init__ руками и получить читаемый вывод при печати.
"""
from dataclasses import dataclass


@dataclass
class Ticker:
    """
    Снимок цен по одной паре на одной бирже.

    exchange — id биржи (например, 'binance')
    symbol   — торговая пара (например, 'BTC/USDT')
    bid      — лучшая цена покупки (сколько готовы заплатить)
    ask      — лучшая цена продажи (сколько просят)
    last     — цена последней сделки
    """
    exchange: str
    symbol: str
    bid: float
    ask: float
    last: float


@dataclass
class ArbitrageOpportunity:
    """
    Одна найденная арбитражная возможность.

    Логика: купить по ask на одной бирже, продать по bid на другой.
    gross_spread_pct — «сырой» спред без учёта комиссий, в процентах.
    net_spread_pct   — спред после вычета комиссий обеих бирж, в процентах.
    """
    symbol: str
    buy_exchange: str
    sell_exchange: str
    buy_price: float
    sell_price: float
    gross_spread_pct: float
    net_spread_pct: float
