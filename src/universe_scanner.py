"""Universe scanning orchestration for PivotPulse."""

from datetime import date
from pathlib import Path

from src.config import load_config
from src.data.providers.csv_provider import CSVMarketDataProvider
from src.scanner import scan_stock
from src.universe import passes_universe_filter


def scan_universe(
    symbols: list[str],
    data_directory: str | Path,
    start_date: date,
    end_date: date,
) -> dict[str, dict]:
    """Scan qualifying stocks through the PivotPulse VCP scanner."""

    config = load_config()

    provider = CSVMarketDataProvider(data_directory)

    results = {}

    for symbol in symbols:
        try:
            df = provider.get_daily_data(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
            )

            if not passes_universe_filter(
                df,
                min_price=config["universe"]["min_price"],
                min_average_turnover=config["universe"][
                    "min_average_turnover"
                ],
                average_period=config["volume"]["average_period"],
            ):
                continue

            scan_result = scan_stock(df)

            results[symbol] = {
                key: value
                for key, value in scan_result.items()
                if key != "data"
            }

        except (FileNotFoundError, ValueError):
            continue

    return results