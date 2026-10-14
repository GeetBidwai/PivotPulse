from datetime import date

from src.multi_stock_scanner import scan_stocks


def main():
    print("=" * 70)
    print("PivotPulse - JNPR VCP Scanner")
    print("=" * 70)

    results = scan_stocks(
        symbols=["JNPR"],
        start_date=date(2026, 8, 6),
        end_date=date.today(),
    )

    print("\n" + "=" * 70)
    print("JNPR RESULT")
    print("=" * 70)

    if results.empty:
        print("No result.")
        return

    print(results.to_string(index=False))


if __name__ == "__main__":
    main()