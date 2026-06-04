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

        if frame is None or frame.empty:
            return []

        frame = frame.reset_index()
        records: list[dict[str, Any]] = []

        for _, row in frame.iterrows():
            price_date = self._parse_price_date(row.get("Date"))
            if price_date is None:
                continue

            records.append(
                {
                    "ticker": self.ticker,
                    "price_date": price_date,
                    "open": self._decimal_or_none(row.get("Open")),
                    "high": self._decimal_or_none(row.get("High")),
                    "low": self._decimal_or_none(row.get("Low")),
                    "close": self._decimal_or_none(row.get("Close")),
                    "adj_close": self._decimal_or_none(row.get("Adj Close")),
                    "volume": self._int_or_none(row.get("Volume")),
                    "source": self.source_name,
                }
            )

        return records

    @staticmethod
    def _parse_price_date(value) -> date | None:
        if value is None or pd.isna(value):
            return None

        if hasattr(value, "date"):
            return value.date()

        try:
            return pd.to_datetime(value).date()
        except Exception:
            return None

    @staticmethod
    def _decimal_or_none(value) -> Decimal | None:
        if value is None or pd.isna(value):
            return None

        try:
            return Decimal(str(round(float(value), 6)))
        except Exception:
            return None

    @staticmethod
    def _int_or_none(value) -> int | None:
        if value is None or pd.isna(value):
            return None

        try:
            return int(value)
        except Exception:
            return None