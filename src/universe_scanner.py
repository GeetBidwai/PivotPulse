"""Universe scanning orchestration for PivotPulse."""

from datetime import date
from pathlib import Path

from src.config import load_config
from src.data.providers.csv_provider import CSVMarketDataProvider
from src.universe import passes_universe_filter


def scan_universe(
    symbols: list[str],
    data_directory: str | Path,
    start_date: date,
    end_date: date,
) -> list[str]:
    """Return symbols that pass the configured universe filters."""

    config = load_config()

    provider = CSVMarketDataProvider(data_directory)

    passed_symbols = []

    for symbol in symbols:
        try:
            df = provider.get_daily_data(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
            )

            if passes_universe_filter(
                df,
                min_price=config["universe"]["min_price"],
                min_average_turnover=config["universe"][
                    "min_average_turnover"
                ],
                average_period=config["volume"]["average_period"],
            ):
                passed_symbols.append(symbol)

        except (FileNotFoundError, ValueError):
            continue

    return passed_symbols