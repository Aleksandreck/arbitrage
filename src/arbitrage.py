"""
Поиск арбитражных возможностей.

Идея простая: для каждой пары, торгуемой минимум на двух биржах,
перебираем все комбинации «купить на бирже A — продать на бирже B».
Считаем спред и оставляем только те, что дают плюс после комиссий.
"""
import itertools

from .models import ArbitrageOpportunity, Ticker


def calculate_opportunity(
    symbol: str,
    buy_ticker: Ticker,
    sell_ticker: Ticker,
    buy_fee_pct: float,
    sell_fee_pct: float,
) -> ArbitrageOpportunity | None:
    """
    Считает одну возможность.

    Логика:
      gross_spread_pct = (sell.bid - buy.ask) / buy.ask * 100
      net_spread_pct   = gross_spread_pct - buy_fee_pct - sell_fee_pct

    Возвращает None, если спред «съеден» комиссиями или цены битые.
    """
    if buy_ticker.ask <= 0 or sell_ticker.bid <= 0:
        return None

    gross_spread_pct = (sell_ticker.bid - buy_ticker.ask) / buy_ticker.ask * 100.0

    # Вычитаем комиссию покупки и продажи
    net_spread_pct = gross_spread_pct - buy_fee_pct - sell_fee_pct

    # Отрицательная прибыль нам не интересна
    if net_spread_pct <= 0:
        return None

    return ArbitrageOpportunity(
        symbol=symbol,
        buy_exchange=buy_ticker.exchange,
        sell_exchange=sell_ticker.exchange,
        buy_price=buy_ticker.ask,
        sell_price=sell_ticker.bid,
        gross_spread_pct=round(gross_spread_pct, 4),
        net_spread_pct=round(net_spread_pct, 4),
    )


def find_best_opportunities(
    tickers_by_exchange: dict[str, dict[str, Ticker]],
    fees: dict[str, float],
    min_net_profit_pct: float = 0.0,
) -> list[ArbitrageOpportunity]:
    """
    Проходит по всем символам и всем парам бирж, где этот символ есть,
    возвращает отфильтрованный и отсортированный список возможностей.

    tickers_by_exchange — {'binance': {'BTC/USDT': Ticker, ...}, 'bybit': {...}}
    fees                — {'binance': 0.1, 'bybit': 0.1}
    min_net_profit_pct  — минимальный чистый спред для попадания в результат
    """
    # Собираем множество всех символов, которые есть хотя бы где-то
    all_symbols: set[str] = set()
    for tickers in tickers_by_exchange.values():
        all_symbols.update(tickers.keys())

    opportunities: list[ArbitrageOpportunity] = []

    for symbol in all_symbols:
        # Биржи, где торгуется этот символ
        available_exchanges = [
            exchange_id
            for exchange_id, tickers in tickers_by_exchange.items()
            if symbol in tickers
        ]

        # Если пара есть только на одной бирже — арбитраж невозможен
        if len(available_exchanges) < 2:
            continue

        # Перебираем упорядоченные пары (binance→bybit и bybit→binance — разные)
        for buy_exchange, sell_exchange in itertools.permutations(available_exchanges, 2):
            buy_ticker = tickers_by_exchange[buy_exchange][symbol]
            sell_ticker = tickers_by_exchange[sell_exchange][symbol]

            opportunity = calculate_opportunity(
                symbol=symbol,
                buy_ticker=buy_ticker,
                sell_ticker=sell_ticker,
                buy_fee_pct=fees.get(buy_exchange, 0.0),
                sell_fee_pct=fees.get(sell_exchange, 0.0),
            )

            if opportunity and opportunity.net_spread_pct >= min_net_profit_pct:
                opportunities.append(opportunity)

    # Сортируем от самой прибыльной к менее прибыльной
    opportunities.sort(key=lambda item: item.net_spread_pct, reverse=True)
    return opportunities
