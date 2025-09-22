import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
import base64
import hmac
import hashlib
import time
from dotenv import load_dotenv

load_dotenv()
MOZ_ACCESS_ID = os.getenv("MOZ_ACCESS_ID")
MOZ_SECRET_KEY = os.getenv("MOZ_SECRET_KEY")

st.set_page_config(layout="wide")
st.title("Advanced APK Keyword Difficulty Checker")
st.write("Estimate KD for APK keywords (Apps/Games niche). Enter one keyword per line.")

keywords_input = st.text_area("Enter keywords:", height=200)
keywords = [k.strip() for k in keywords_input.split("\n") if k.strip()]
country = st.selectbox("Select Country:", ["Global", "Pakistan", "India"])

def get_moz_metrics(url):
    try:
        expires = int(time.time() + 300)
        string_to_sign = f"{MOZ_ACCESS_ID}\n{expires}"
        signature = base64.b64encode(hmac.new(MOZ_SECRET_KEY.encode(), string_to_sign.encode(), hashlib.sha1).digest())
        params = {"Cols": 103079215108, "AccessID": MOZ_ACCESS_ID, "Expires": expires, "Signature": signature}
        r = requests.get(f"https://lsapi.seomoz.com/v2/url_metrics?url={url}", params=params)
        data = r.json()
        return data.get("domain_authority", 0), data.get("page_authority", 0)
    except:
        return 0, 0

def estimate_kd(keyword):
    try:
        search_engine = "google.com"
        if country == "Pakistan": search_engine = "google.com.pk"
        elif country == "India": search_engine = "google.co.in"
        url = f"https://www.google.com/search?q={keyword.replace(' ', '+')}&gl={search_engine}"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        result_stats = soup.find("div", {"id": "result-stats"})
        num_results = int(''.join(filter(str.isdigit, result_stats.get_text().split()[1]))) if result_stats else 1000000
        top_url_div = soup.find("div", {"class": "tF2Cxc"})
        top_url = top_url_div.find("a")["href"] if top_url_div else ""
        da, pa = get_moz_metrics(top_url) if top_url else (20, 20)
        kd_score = min(100, int((num_results/100000)*0.5 + (da+pa)/2*0.5))
        return kd_score
    except:
        return "Error"

if st.button("Estimate KD"):
    if not keywords:
        st.warning("Enter at least one keyword.")
    else:
        results = [{"Keyword": kw, "Estimated KD": estimate_kd(kw)} for kw in keywords]
        df = pd.DataFrame(results)
        st.success("KD estimation complete!")
        st.dataframe(df)
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("Download CSV", data=csv, file_name="kd_results.csv", mime="text/csv")
