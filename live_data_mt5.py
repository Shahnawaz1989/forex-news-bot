# live_data_mt5.py
import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timedelta


def fetch_live_1h(symbol: str, lookback_days: int = 90) -> pd.DataFrame:
    """
    Last N days ka 1H OHLC MT5 se lao.
    Columns: datetime, open, high, low, close
    """
    if not mt5.initialize():
        raise RuntimeError("MT5 initialize failed")

    tf = mt5.TIMEFRAME_H1
    end = datetime.now()
    start = end - timedelta(days=lookback_days)

    rates = mt5.copy_rates_range(symbol, tf, start, end)
    if rates is None or len(rates) == 0:
        mt5.shutdown()
        raise RuntimeError(f"No 1H data for {symbol}")

    df = pd.DataFrame(rates)
    df["datetime"] = pd.to_datetime(df["time"], unit="s")
    df = df[["datetime", "open", "high", "low", "close"]]

    mt5.shutdown()
    return df
