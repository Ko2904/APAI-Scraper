"""Streamlit dashboard for the Supabase-backed Books to Scrape catalogue."""

from __future__ import annotations

import os

import streamlit as st
from dotenv import load_dotenv
from supabase import create_client

from scraper import BookScraper, save_to_supabase

load_dotenv()
st.set_page_config(page_title="Books to Scrape", page_icon="📚", layout="wide")
st.title("Books to Scrape")
st.caption("Catalogue snapshots and observed price changes")

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
if not url or not key:
    st.error("Configure SUPABASE_URL and SUPABASE_KEY in your local .env file.")
    st.stop()

client = create_client(url, key)
with st.sidebar:
    st.header("Run scraper")
    pages = st.number_input("Maximum pages", min_value=1, max_value=50, value=1)
    if st.button("Scrape and save", type="primary"):
        with st.spinner("Scraping catalogue and saving to Supabase..."):
            scraper = BookScraper()
            books = scraper.scrape(max_pages=int(pages))
            save_to_supabase(books, scraper.pages_scraped)
        st.success(f"Saved {len(books)} books from {scraper.pages_scraped} page(s).")
        st.rerun()

books_result = (
    client.table("books")
    .select("id, title, price, currency, availability, rating, source_url, last_seen_at")
    .order("title")
    .limit(1000)
    .execute()
)
books = books_result.data
st.metric("Books stored", len(books))
if not books:
    st.info("No books yet. Run a small scrape from the sidebar to get started.")
    st.stop()

st.subheader("Catalogue")
st.dataframe(books, use_container_width=True, hide_index=True)

st.subheader("Price history")
selected = st.selectbox("Book", books, format_func=lambda book: book["title"])
history = (
    client.table("price_history")
    .select("price, observed_at")
    .eq("book_id", selected["id"])
    .order("observed_at")
    .execute()
    .data
)
if history:
    st.line_chart(
        [{"Observed at": point["observed_at"], "Price": float(point["price"])} for point in history],
        x="Observed at",
        y="Price",
    )
else:
    st.info("No price changes have been recorded for this book yet.")
