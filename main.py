# -*- coding: utf-8 -*-
import requests
import pandas as pd
from bs4 import BeautifulSoup

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from config import SENDGRID_API_KEY


def scrape_ercot(url: str) -> pd.DataFrame:
    r = requests.get(url)
    soup = BeautifulSoup(r.text, "html.parser")
    table = soup.find("table")
    return pd.read_html(str(table), header=0)[0]


def send_text(msg: str) -> None:
    message = Mail(
        from_email="test@example.com",
        to_emails="test@example.com",
        subject=msg,
        plain_text_content=" ",
    )
    SendGridAPIClient(SENDGRID_API_KEY).send(message)


def ercot(price: int = 6, *args) -> None:
    url = "http://www.ercot.com/content/cdr/html/rtd_ind_lmp_lz_hb_LZ_HOUSTON.html"
    df = scrape_ercot(url)

    time_col = "RTD Date and Time"
    df[time_col] = pd.to_datetime(df[time_col]).dt.round("min")

    df2 = df.melt(id_vars=time_col)

    time_add = df2["variable"].str.extract(r"\+([0-9]+)", expand=False).fillna(0).astype(int)
    df2["dt"] = df2[time_col] + pd.to_timedelta(time_add, unit="m")
    df2 = df2[df2["dt"] > pd.Timestamp.now()]

    df2 = (df2.groupby("dt")["value"].max() / 10).round(1)
    df2 = df2[df2 >= price]

    if not df2.empty:
        msg = f"{df2.iloc[0]}c projected at {df2.head(1).index.strftime('%H:%M')[0]}"
        try:
            send_text(msg)
        except Exception as e:
            print(e)
            print(e.body)
