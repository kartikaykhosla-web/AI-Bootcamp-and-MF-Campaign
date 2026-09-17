# Jagran Next AI Future Bootcamp dashboard

A custom Streamlit operations dashboard for AI Future Bootcamp and Mutual Funds Mastery registrations, payments, revenue, offers and participant geography.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Connect the two APIs

Open the visible `api_config.toml` file and add both endpoint URLs:

```toml
ai_bootcamp_api_url = "https://your-ai-bootcamp-endpoint"
mutual_funds_api_url = "https://your-mutual-funds-endpoint"
page_param = "page"
```

No token or API key is required. The dashboard contains no demo records and loads only the selected project's live API.

For Streamlit Community Cloud, add the same three values under **App settings → Secrets**:

```toml
ai_bootcamp_api_url = "https://your-ai-bootcamp-endpoint"
mutual_funds_api_url = "https://your-mutual-funds-endpoint"
page_param = "page"
```

Cloud secrets take precedence over the local `api_config.toml` values. `.streamlit/secrets.toml` is excluded from Git.

Each project tab calls only its matching endpoint. Both endpoints may return the supplied `data.dataList` envelope. The loader also accepts `records`, `results`, `items`, a bare `data` list, or a top-level list. Pagination follows `nextPage` and `totalPages`; change `API_PAGE_PARAM` if the endpoint uses a different query parameter.

Each live API must return compatible registration rows. Records are deduplicated within that project using the first available key among `id`, `email`, `phone`, `txn_id`, and `order_id`.

The hidden `.streamlit` folder contains only visual theme settings; API configuration is kept in the visible `api_config.toml` file.
