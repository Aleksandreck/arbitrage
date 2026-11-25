"""
Точка входа: запуск из командной строки.

    python -m src.main --config config.yaml

Читает конфиг, грузит тикеры со всех бирж, ищет возможности,
печатает красивую таблицу и сохраняет результат в output/opportunities.csv.
"""
import argparse
from pathlib import Path

import pandas as pd
import yaml
from tabulate import tabulate

from .arbitrage import find_best_opportunities
from .exchanges import fetch_tickers


def load_config(path: str) -> dict:
    """Читает YAML-конфиг и возвращает словарь."""
    with open(path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def main() -> None:
    # --- 1. Парсинг аргументов командной строки ---
    parser = argparse.ArgumentParser(description="Crypto arbitrage scanner")
    parser.add_argument("--config", default="config.yaml", help="Путь до файла конфигурации")
    args = parser.parse_args()

    # --- 2. Загрузка конфига ---
    config = load_config(args.config)
    exchanges_config = config.get("exchanges", [])
    quote = config.get("quote", "USDT")
    min_net_profit_pct = float(config.get("min_net_profit_pct", 0.0))
    limit = int(config.get("limit", 20))
    whitelist = set(config.get("symbols_whitelist") or [])

    # --- 3. Загрузка тикеров со всех бирж ---
    tickers_by_exchange = {}
    fees = {}

    for exchange_config in exchanges_config:
        exchange_id = exchange_config["id"]
        fees[exchange_id] = float(exchange_config.get("fee_pct", 0.1))

        try:
            tickers = fetch_tickers(exchange_id, quote=quote)
            tickers_by_exchange[exchange_id] = tickers
            print(f"{exchange_id}: {len(tickers)} tickers loaded")
        except Exception as error:
            # Одна биржа упала — не критично, продолжаем со остальными
            print(f"{exchange_id}: failed to load tickers -> {error}")

    # Для арбитража нужны минимум две биржи
    if len(tickers_by_exchange) < 2:
        print("Need at least two exchanges with loaded data.")
        return

    # --- 4. Поиск возможностей ---
    opportunities = find_best_opportunities(
        tickers_by_exchange=tickers_by_exchange,
        fees=fees,
        min_net_profit_pct=min_net_profit_pct,
    )

    # Если задан whitelist — оставляем только символы из него
    if whitelist:
        opportunities = [item for item in opportunities if item.symbol in whitelist]

    # Ограничиваем количество строк
    opportunities = opportunities[:limit]

    if not opportunities:
        print("No arbitrage opportunities found for current filters.")
        return

    # --- 5. Вывод в консоль ---
    rows = [
        [
            item.symbol,
            item.buy_exchange,
            item.sell_exchange,
            f"{item.buy_price:.8g}",
            f"{item.sell_price:.8g}",
            f"{item.gross_spread_pct:.3f}%",
            f"{item.net_spread_pct:.3f}%",
        ]
        for item in opportunities
    ]

    headers = ["Symbol", "Buy on", "Sell on", "Buy ask", "Sell bid", "Gross %", "Net %"]
    print(tabulate(rows, headers=headers, tablefmt="github"))

    # --- 6. Сохранение в CSV ---
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / "opportunities.csv"

    dataframe = pd.DataFrame([item.__dict__ for item in opportunities])
    dataframe.to_csv(output_path, index=False)
    print(f"\nSaved to {output_path}")


if __name__ == "__main__":
    main()
