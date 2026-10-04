from datetime import date

from src.multi_stock_scanner import scan_stocks


def main():
    print("=" * 70)
    print("PivotPulse - VCP Scanner")
    print("=" * 70)

    symbols = [
        "RELIANCE",
        "INFY",
        "TCS",
        "HDFCBANK",
        "ICICIBANK",
    ]

    print("\nScanning:")
    print(", ".join(symbols))

    results = scan_stocks(
        symbols=symbols,
        start_date=date(2025, 1, 1),
        end_date=date.today(),
    )

    print("\n" + "=" * 70)
    print("VCP SIGNALS")
    print("=" * 70)

    if results.empty:
        print("No VCP signals found.")
        return

    display_columns = [
        "symbol",
        "date",
        "score",
        "classification",
        "signal",
    ]

    print(
        results[display_columns]
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()