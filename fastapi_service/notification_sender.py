from __future__ import annotations

import json
import os
import urllib.request
from typing import Any, Dict, Optional


def _post_http(url: str, payload: Dict[str, Any]) -> None:
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=float(os.getenv("WEBHOOK_TIMEOUT_SECONDS", "5"))):
            pass
    except Exception:
        # Swallow errors to avoid failing processing
        return


def _publish_kafka(topic: str, payload: Dict[str, Any]) -> None:
    try:
        from confluent_kafka import Producer  # type: ignore

        brokers = os.getenv("KAFKA_BROKERS") or os.getenv("KAFKA_BOOTSTRAP_SERVERS")
        if not brokers:
            return
        producer = Producer({"bootstrap.servers": brokers})
        producer.produce(topic, json.dumps(payload).encode("utf-8"))
        producer.flush(5.0)
    except Exception:
        # If kafka library not available or brokers not reachable, ignore
        return


def send_notifications(
    *,
    record: Dict[str, Any],
    callback_url: Optional[str],
    pubsub_provider: Optional[str],
    pubsub_topic: Optional[str],
) -> None:
    # Build a compact message with everything needed to fetch results
    processing_id = record.get("processing_id")
    message: Dict[str, Any] = {
        "type": record.get("type"),
        "filename": record.get("filename"),
        "processing_id": processing_id,
        "status": record.get("status", "completed"),
        "results_endpoints": {
            "full": f"/api/results/{processing_id}/full",
            "table": f"/api/results/{processing_id}/table",
            "meta": f"/api/results/{processing_id}/meta",
            "status": f"/api/status/{processing_id}/",
        },
    }

    # Attach direct download URLs if available
    download_urls = None
    storage = record.get("storage") or {}
    if isinstance(storage, dict) and storage.get("download_urls"):
        download_urls = storage["download_urls"]
    elif record.get("download_urls"):
        download_urls = record["download_urls"]
    if download_urls:
        message["download_urls"] = download_urls

    # Include storage references for consumers that fetch via keys
    if isinstance(storage, dict):
        refs = {}
        for k in ("processed_json", "table_data", "complexity_results", "original_file"):
            v = storage.get(k)
            if isinstance(v, dict) and v.get("key"):
                refs[k] = {"key": v.get("key"), "storage_type": v.get("storage_type")}
        if refs:
            message["storage_keys"] = refs

    # Optional cache handle
    if record.get("file_id"):
        message["cache_handle"] = {"file_id": record["file_id"]}

    # Emit
    if callback_url:
        _post_http(callback_url, message)
    if pubsub_provider and pubsub_topic:
        provider = pubsub_provider.strip().lower()
        if provider == "kafka":
            _publish_kafka(pubsub_topic, message)
        # Unknown provider => no-op


