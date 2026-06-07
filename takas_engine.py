import requests
from bs4 import BeautifulSoup
import re
import os
from database import engine
from sqlalchemy import text
import pandas as pd
from datetime import datetime, timezone, timedelta
import pytz
from io import StringIO

TR_TZ = pytz.timezone("Europe/Istanbul")



class TakasScraper:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
    def fetch_all(self):
        return {}


def update_all_takas():
    # Yabancı takas kaynağı iptal edildiği için devredışı bırakıldı
    return True

def get_takas_data(ticker):
    # Yabancı takas veri kaynağı olmadığı için tüm hisselere 0.0 dönüyoruz
    return {'foreign_ratio': 0.0, 'daily_change': 0.0}
