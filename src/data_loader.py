from pathlib import Path
import pandas as pd


REQUIRED_COLUMNS = [
    "Date",
    "Open",
    "High",
    "Low",
    "Close",
    "Volume",
]


def load_ohlcv_csv(file_path: str | Path) -> pd.DataFrame:
    """
    Load OHLCV data from a CSV file.

    Expected columns:
        Date, Open, High, Low, Close, Volume
    """

    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"Data file not found: {file_path}")

    df = pd.read_csv(file_path)

    missing_columns = [
        column for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    df["Date"] = pd.to_datetime(df["Date"])

    numeric_columns = [
        "Open",
        "High",
        "Low",
        "Close",
        "Volume",
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )

    df = df.sort_values("Date")
    df = df.drop_duplicates(subset="Date")
    df = df.reset_index(drop=True)

    validate_ohlcv(df)

    return df

def validate_ohlcv(df: pd.DataFrame) -> None:
    """Validate basic OHLCV data integrity."""

    if df.empty:
        raise ValueError("OHLCV dataset is empty.")

    numeric_columns = [
        "Open",
        "High",
        "Low",
        "Close",
        "Volume",
    ]

    if df[numeric_columns].isnull().any().any():
        raise ValueError(
            "OHLCV data contains missing numeric values."
        )

    invalid_prices = (
        (df["High"] < df["Low"])
        | (df["High"] < df["Open"])
        | (df["High"] < df["Close"])
        | (df["Low"] > df["Open"])
        | (df["Low"] > df["Close"])
    )

    if invalid_prices.any():
        raise ValueError(
            "OHLCV data contains invalid price relationships."
        )

    if (df["Volume"] < 0).any():
        raise ValueError(
            "Volume cannot be negative."
        )