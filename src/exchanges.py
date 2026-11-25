"""
Работа с биржами через ccxt.

Задача модуля — подключиться к бирже и вернуть словарь тикеров
вида {'BTC/USDT': Ticker(...), 'ETH/USDT': Ticker(...)}.
"""
import ccxt

from .models import Ticker


def create_exchange(exchange_id: str, timeout_ms: int = 30000):
    """
    Создаёт объект биржи ccxt по её id.

    enableRateLimit — встроенный троттлинг, чтобы не получить бан от биржи
    timeout         — максимальное время ожидания ответа от API (мс)
    """
    if not hasattr(ccxt, exchange_id):
        raise ValueError(f"Exchange '{exchange_id}' is not supported by ccxt")

    exchange_class = getattr(ccxt, exchange_id)
    return exchange_class({
        "enableRateLimit": True,
        "timeout": timeout_ms,
    })


def fetch_tickers(exchange_id: str, quote: str = "USDT") -> dict[str, Ticker]:
    """
    Загружает все тикеры указанной биржи и фильтрует их:
      - только спотовые рынки (не фьючерсы)
      - только пары с нужной котируемой валютой (например, USDT)
      - только те, где есть bid/ask/last (иначе арбитраж не посчитать)
    """
    exchange = create_exchange(exchange_id)

    # Загружаем список рынков (нужен для проверки quote и типа рынка)
    exchange.load_markets()

    # Загружаем все тикеры одним запросом (быстрее, чем по одному)
    raw_tickers = exchange.fetch_tickers()

    result: dict[str, Ticker] = {}

    for symbol, ticker in raw_tickers.items():
        market = exchange.markets.get(symbol)
        if not market:
            continue

        # Пропускаем всё, что не в нужной котируемой валюте (например, /BTC)
        if market.get("quote") != quote:
            continue

        # Пропускаем фьючерсы/маржинальные рынки — оставляем только спот
        if not market.get("spot", False):
            continue

        bid = ticker.get("bid")
        ask = ticker.get("ask")
        last = ticker.get("last")

        # Если биржа не вернула одну из цен — такой тикер нам бесполезен
        if bid is None or ask is None or last is None:
            continue

        result[symbol] = Ticker(
            exchange=exchange_id,
            symbol=symbol,
            bid=float(bid),
            ask=float(ask),
            last=float(last),
        )

    return result
