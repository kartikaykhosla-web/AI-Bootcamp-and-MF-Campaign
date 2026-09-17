"""API and normalization helpers for the Jagran AI Bootcamp dashboard."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Iterable

import pandas as pd
import requests


MONEY_COLUMNS = [
    "amount",
    "discount",
    "base_amount",
    "gst",
    "igst",
    "cgst",
    "sgst",
    "payable_amount",
]


@dataclass(frozen=True)
class DataBundle:
    records: pd.DataFrame
    fetched_at: datetime
    sources: tuple[str, ...]
    warnings: tuple[str, ...] = ()


def _headers(token: str = "", api_key: str = "") -> dict[str, str]:
    result = {"Accept": "application/json"}
    if token:
        result["Authorization"] = f"Bearer {token}"
    if api_key:
        result["x-api-key"] = api_key
    return result


def extract_records(payload: Any) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Accept common API envelopes and return records plus pagination metadata."""
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)], {}
    if not isinstance(payload, dict):
        raise ValueError("API response must be a JSON object or list.")

    data = payload.get("data", payload)
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)], {}
    if not isinstance(data, dict):
        raise ValueError("The response does not contain a usable data object.")

    for key in ("dataList", "records", "results", "items"):
        value = data.get(key)
        if isinstance(value, list):
            metadata = {k: v for k, v in data.items() if k != key}
            return [item for item in value if isinstance(item, dict)], metadata
    return [], data


def fetch_all_pages(
    url: str,
    *,
    source: str,
    token: str = "",
    api_key: str = "",
    page_param: str = "page",
    timeout: int = 20,
    max_pages: int = 100,
) -> list[dict[str, Any]]:
    """Fetch a paginated endpoint, following totalPages/nextPage when present."""
    if not url:
        return []
    rows: list[dict[str, Any]] = []
    page = 1
    seen_pages: set[int] = set()

    while page not in seen_pages and len(seen_pages) < max_pages:
        seen_pages.add(page)
        response = requests.get(
            url,
            params={page_param: page},
            headers=_headers(token, api_key),
            timeout=timeout,
        )
        response.raise_for_status()
        page_rows, meta = extract_records(response.json())
        rows.extend({**row, "_source": source} for row in page_rows)

        next_page = meta.get("nextPage")
        total_pages = int(meta.get("totalPages") or page)
        if next_page is None and page >= total_pages:
            break
        page = int(next_page or page + 1)
    return rows


def normalize_records(records: Iterable[dict[str, Any]]) -> pd.DataFrame:
    frame = pd.DataFrame(list(records))
    if frame.empty:
        return frame

    for column in MONEY_COLUMNS:
        if column in frame:
            frame[column] = pd.to_numeric(frame[column], errors="coerce").fillna(0.0)
    for column in ("created_at", "updated_at"):
        if column in frame:
            frame[column] = pd.to_datetime(frame[column], errors="coerce", utc=True)

    for column in ("payment_status", "state_name", "city_name", "coupon_code", "batch_date"):
        if column in frame:
            frame[column] = frame[column].fillna("Unknown").astype(str).str.strip()
    if "payment_status" in frame:
        frame["payment_status"] = frame["payment_status"].str.lower()

    identity = next((c for c in ("id", "email", "phone", "txn_id", "order_id") if c in frame), None)
    if identity:
        frame = frame.drop_duplicates(subset=[identity], keep="last")
    return frame.reset_index(drop=True)


def load_live_data(
    api_urls: Iterable[str],
    *,
    token: str = "",
    api_key: str = "",
    page_param: str = "page",
) -> DataBundle:
    rows: list[dict[str, Any]] = []
    warnings: list[str] = []
    sources: list[str] = []
    for index, url in enumerate(api_urls, start=1):
        if not url:
            continue
        source = f"API {index}"
        try:
            rows.extend(
                fetch_all_pages(
                    url,
                    source=source,
                    token=token,
                    api_key=api_key,
                    page_param=page_param,
                )
            )
            sources.append(source)
        except (requests.RequestException, ValueError, TypeError) as exc:
            warnings.append(f"{source}: {exc}")
    return DataBundle(
        records=normalize_records(rows),
        fetched_at=datetime.now(timezone.utc),
        sources=tuple(sources),
        warnings=tuple(warnings),
    )


def mask_contact(value: Any, kind: str) -> str:
    text = str(value or "")
    if kind == "email" and "@" in text:
        name, domain = text.split("@", 1)
        return f"{name[:2]}***@{domain}"
    digits = "".join(char for char in text if char.isdigit())
    return f"******{digits[-4:]}" if digits else "—"
