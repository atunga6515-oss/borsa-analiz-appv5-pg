from sqlalchemy import Column, Integer, BigInteger, String, Float, Text, Boolean, DateTime, UniqueConstraint, Index
from database import Base
import datetime

class User(Base):
    __tablename__ = 'users'
    username = Column(String(255), primary_key=True, index=True)
    password_hash = Column(String(255), nullable=False)

class Portfolio(Base):
    __tablename__ = 'portfolio'
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(255), index=True)
    ticker = Column(String(50), nullable=False)
    adet = Column(Float, nullable=False)
    alis_fiyati = Column(Float, nullable=False)
    alis_tarihi = Column(String(50), nullable=False)
    durum = Column(String(20), default='ACIK')
    satis_fiyati = Column(Float, nullable=True)
    satis_tarihi = Column(String(50), nullable=True)
    not_text = Column(Text, nullable=True)
    sl = Column(Float, nullable=True)
    tp = Column(Float, nullable=True)
    var = Column(Float, nullable=True)

class TakasData(Base):
    __tablename__ = 'takas_data'
    ticker = Column(String(50), primary_key=True)
    date = Column(String(50), primary_key=True)
    foreign_ratio = Column(Float)
    daily_change = Column(Float)

class Alert(Base):
    __tablename__ = 'alerts'
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(255), index=True)
    ticker = Column(String(50), nullable=False)
    alert_type = Column(String(100), nullable=False)
    threshold = Column(Float, nullable=False)
    status = Column(String(50), default='AKTIF')
    note = Column(Text, nullable=True)
    created_at = Column(String(50), nullable=False)
    triggered_at = Column(String(50), nullable=True)
    triggered_value = Column(Float, nullable=True)

class ScanHistory(Base):
    __tablename__ = 'scan_history'
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(255), index=True)
    scan_date = Column(String(50), nullable=False)
    ticker = Column(String(50), nullable=False)
    score = Column(Float)
    decision = Column(String(100))
    price = Column(Float)
    pct_change = Column(Float)
    is_bad_signal = Column(Integer, default=0)

class Watchlist(Base):
    __tablename__ = 'watchlist'
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(255), index=True)
    ticker = Column(String(50), nullable=False)
    added_date = Column(String(50), nullable=False)
    note = Column(Text, default='')

class TopPicksHistory(Base):
    __tablename__ = 'top_picks_history'
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(255), index=True)
    run_date = Column(String(50), nullable=False)
    results_json = Column(Text, nullable=False)

class Ohlcv(Base):
    __tablename__ = 'ohlcv'
    ticker = Column(String(50), primary_key=True, index=True)
    interval = Column(String(10), primary_key=True)
    date = Column(String(50), primary_key=True)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    adj_close = Column(Float)
    volume = Column(BigInteger)
    
    __table_args__ = (
        Index('idx_ticker_interval_date', 'ticker', 'interval', 'date'),
    )

class FinancialData(Base):
    __tablename__ = 'financial_data'
    ticker = Column(String(50), primary_key=True)
    date = Column(String(50), primary_key=True)
    financials_json = Column(Text)

class InfoData(Base):
    __tablename__ = 'info_data'
    ticker = Column(String(50), primary_key=True)
    info_json = Column(Text)
    last_updated = Column(String(50))
