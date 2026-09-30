from pathlib import Path

from src.config import load_config
from src.data_loader import load_ohlcv_csv
from src.indicators import add_indicators


PROJECT_ROOT = Path(__file__).resolve().parent


def main():
    config = load_config()

    print("=" * 60)
    print("PivotPulse - Stage 1A")
    print("=" * 60)

    print(f"Project: {config['project']['name']}")
    print(f"Timeframe: {config['project']['timeframe']}")

    data_file = (
        PROJECT_ROOT
        / "data"
        / "raw"
        / "sample.csv"
    )

    print(f"\nLoading: {data_file}")

    df = load_ohlcv_csv(data_file)

    print(f"Rows loaded: {len(df):,}")
    print(f"First date: {df['Date'].min()}")
    print(f"Last date:  {df['Date'].max()}")

    df = add_indicators(
        df,
        fast_sma=config["trend"]["fast_sma"],
        slow_sma=config["trend"]["slow_sma"],
        atr_period=config["volatility"]["atr_period"],
        volume_period=config["volume"]["average_period"],
    )

    print("\nIndicators calculated:")
    print(
        df[
            [
                "Date",
                "Close",
                "SMA_50",
                "SMA_200",
                "52W_High",
                "ATR_14",
                "ATR_Pct",
                "RelativeVolume",
            ]
        ].tail(10).to_string(index=False)
    )

    print("\nPivotPulse Stage 1A complete.")


if __name__ == "__main__":
    main()