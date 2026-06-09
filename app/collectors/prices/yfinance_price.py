from datetime import date
from decimal import Decimal
from typing import Any

import pandas as pd
import yfinance as yf


class YFinancePriceCollector:
    def __init__(
            self,
            ticker: str,
            source_name: str = "yfinance_daily_prices",
            period: str = "6mo",
            interval: str = "1d",
            start_date: str | None = None,
            end_date: str | None = None,
    ) -> None:
        self.ticker = ticker.upper()
        self.source_name = source_name
        self.period = period
        self.interval = interval
        self.start_date = start_date
        self.end_date = end_date

    def collect(self) -> list[dict[str, Any]]:
        ticker_obj = yf.Ticker(self.ticker)

        if self.start_date or self.end_date:
            frame = ticker_obj.history(
                start=self.start_date,
                end=self.end_date,
                interval=self.interval,
                auto_adjust=False,
            )
        else:
            frame = ticker_obj.history(
                period=self.period,
                interval=self.interval,
                auto_adjust=False,
            )

        return _frame_to_records(
            ticker=self.ticker,
            frame=frame,
            source_name=self.source_name,
        )


class YFinanceBatchPriceCollector:
    def __init__(
            self,
            tickers: list[str],
            source_name: str = "yfinance_daily_prices",
            period: str = "6mo",
            interval: str = "1d",
            start_date: str | None = None,
            end_date: str | None = None,
    ) -> None:
        self.tickers = [
            ticker.upper()
            for ticker in tickers
            if ticker
        ]
        self.source_name = source_name
        self.period = period
        self.interval = interval
        self.start_date = start_date
        self.end_date = end_date

    def collect(self) -> dict[str, list[dict[str, Any]]]:
        if not self.tickers:
            return {}

        if self.start_date or self.end_date:
            frame = yf.download(
                tickers=self.tickers,
                start=self.start_date,
                end=self.end_date,
                interval=self.interval,
                auto_adjust=False,
                group_by="ticker",
                threads=True,
                progress=False,
            )
        else:
            frame = yf.download(
                tickers=self.tickers,
                period=self.period,
                interval=self.interval,
                auto_adjust=False,
                group_by="ticker",
                threads=True,
                progress=False,
            )

        if frame is None or frame.empty:
            return {
                ticker: []
                for ticker in self.tickers
            }

        records_by_ticker: dict[str, list[dict[str, Any]]] = {}

        # Multiple tickers with group_by="ticker" normally returns MultiIndex columns:
        # level 0 = ticker, level 1 = OHLCV fields.
        if isinstance(frame.columns, pd.MultiIndex):
            available_tickers = set(frame.columns.get_level_values(0))

            for ticker in self.tickers:
                if ticker not in available_tickers:
                    records_by_ticker[ticker] = []
                    continue

                ticker_frame = frame[ticker]
                records_by_ticker[ticker] = _frame_to_records(
                    ticker=ticker,
                    frame=ticker_frame,
                    source_name=self.source_name,
                )

            return records_by_ticker

        # Fallback for a single ticker or unexpected yfinance shape.
        if len(self.tickers) == 1:
            ticker = self.tickers[0]
            return {
                ticker: _frame_to_records(
                    ticker=ticker,
                    frame=frame,
                    source_name=self.source_name,
                )
            }

        return {
            ticker: []
            for ticker in self.tickers
        }


def _frame_to_records(
        ticker: str,
        frame: pd.DataFrame | None,
        source_name: str,
) -> list[dict[str, Any]]:
    if frame is None or frame.empty:
        return []

    frame = frame.reset_index()
    records: list[dict[str, Any]] = []

    for _, row in frame.iterrows():
        price_date = _parse_price_date(row.get("Date"))

        if price_date is None:
            # yfinance sometimes names the date index as Datetime.
            price_date = _parse_price_date(row.get("Datetime"))

        if price_date is None:
            continue

        close = _decimal_or_none(row.get("Close"))

        # Skip fully empty rows that yfinance can produce for failed symbols.
        if close is None:
            continue

        records.append(
            {
                "ticker": ticker.upper(),
                "price_date": price_date,
                "open": _decimal_or_none(row.get("Open")),
                "high": _decimal_or_none(row.get("High")),
                "low": _decimal_or_none(row.get("Low")),
                "close": close,
                "adj_close": _decimal_or_none(row.get("Adj Close")),
                "volume": _int_or_none(row.get("Volume")),
                "source": source_name,
            }
        )

    return records


def _parse_price_date(value) -> date | None:
    if value is None or pd.isna(value):
        return None

    if hasattr(value, "date"):
        return value.date()

    try:
        return pd.to_datetime(value).date()
    except Exception:
        return None


def _decimal_or_none(value) -> Decimal | None:
    if value is None or pd.isna(value):
        return None

    try:
        return Decimal(str(round(float(value), 6)))
    except Exception:
        return None


def _int_or_none(value) -> int | None:
    if value is None or pd.isna(value):
        return None

    try:
        return int(value)
    except Exception:
        return None
