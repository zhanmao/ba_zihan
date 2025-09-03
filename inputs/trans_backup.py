import ast
import json
import time
from datetime import datetime
from typing import List, Dict, Any

import pandas as pd
import requests
from paho.mqtt.client import Client, MQTTv311


BROKER = "localhost"
PORT = 1883
TOPIC = "metric/test"
KAIROS = "http://localhost:8083/api/v1/datapoints"
CSV_PATH = "merged_events.csv" 
# -------------------------


def to_ms(ts) -> int:
    """pandas/numpy datetime -> epoch ms (UTC)."""
    if pd.isna(ts):
        return None
    if isinstance(ts, (pd.Timestamp, datetime)):
        dt = ts.tz_convert("UTC") if getattr(ts, "tzinfo", None) else pd.Timestamp(ts).tz_localize("UTC")
        return int(dt.timestamp() * 1000)

    # fallback: try parse
    dt = pd.to_datetime(ts, utc=True, errors="coerce")
    if pd.isna(dt):
        return None
    return int(dt.timestamp() * 1000)


def safe_literal_list(s) -> List[Dict[str, Any]]:
    """Parse a string like '[{...}, {...}]' safely into list[dict]."""
    if not isinstance(s, str) or not s.strip():
        return []
    try:
        v = ast.literal_eval(s)
        return v if isinstance(v, list) else []
    except Exception:
        return []


# task event -> numeric state (KairosDB value)
TASK_STATE_MAP = {
    "TASK_QUEUED": 1,
    "TASK_RUNNING": 2,
    "TASK_TERMINATED": 0,
    "QUEUED": 1,
    "RUNNING": 2,
    "TERMINATED": 0,
}


def build_task_points(df: pd.DataFrame):

    out = []

    if "job_event" in df.columns:
        df = df.copy()
        df["job_event"] = df["job_event"].fillna("[]")
        df["job_event_list"] = df["job_event"].apply(safe_literal_list)

        exploded = df.explode("job_event_list").dropna(subset=["job_event_list"])
        for col in ["event", "task_id", "task_name", "task_graph_id", "node_id"]:
            exploded[col] = exploded["job_event_list"].apply(
                lambda x: x.get(col) if isinstance(x, dict) else None
            )
        work = exploded
    else:
        # 直接列模式
        required = {"event", "task_id"}
        if not required.issubset(df.columns):
            return out
        work = df

    if "timestamp" not in work.columns:
        return out

    work = work.dropna(subset=["timestamp", "task_id", "event"]).copy()
    work["ts_ms"] = work["timestamp"].apply(to_ms)
    work = work.dropna(subset=["ts_ms"]).sort_values("ts_ms")

    for _, r in work.iterrows():
        val = TASK_STATE_MAP.get(str(r["event"]).upper(), 2)
        tags = {
            "task_id": str(r.get("task_id", "")),
            "task_name": str(r.get("task_name", "")) if pd.notna(r.get("task_name", "")) else "",
            "task_graph_id": str(r.get("task_graph_id", "")) if pd.notna(r.get("task_graph_id", "")) else "",
        }
        if pd.notna(r.get("node_id", None)):
            tags["node_id"] = str(r["node_id"])

        payload = [
            {
                "name": "task_status",
                "datapoints": [[int(r["ts_ms"]), int(val)]],
                "tags": tags,
            }
        ]
        out.append((TOPIC, json.dumps(payload, separators=(",", ":"))))

    return out


def on_message(cli, _, msg):
    try:
        r = requests.post(KAIROS, data=msg.payload, headers={"Content-Type": "application/json"})
        r.raise_for_status()
        print(f"[Bridge] Forwarded to KairosDB: {len(msg.payload)} bytes")
    except Exception as e:
        print("[Bridge] Post to KairosDB failed:", e)


def main():
   
    try:
        df = pd.read_csv(CSV_PATH, parse_dates=["timestamp"])
    except Exception as e:
        print(f"[Error] Failed to read CSV '{CSV_PATH}':", e)
        return

    messages = build_task_points(df)
    if not messages:
        print("[Warn] No datapoints built from CSV. Check columns: timestamp/event/task_id or job_event.")
        return

   
    pub_cli = Client(client_id="csv2mqtt_pub", protocol=MQTTv311)
    pub_cli.connect(BROKER, PORT, 30)
    pub_cli.loop_start()

    # 桥接端：订阅 MQTT，并转发到 KairosDB
    bridge_cli = Client(client_id="mqtt2kairos", protocol=MQTTv311)
    bridge_cli.connect(BROKER, PORT, 30)
    bridge_cli.on_message = on_message
    bridge_cli.subscribe(TOPIC, qos=1)
    bridge_cli.loop_start()

    try:
        for topic, payload in messages:
            pub_cli.publish(topic, payload, qos=1)
            print(f"[Publish] {topic} -> {payload}")
            time.sleep(0.2)
    finally:
        pub_cli.loop_stop()
        pub_cli.disconnect()
        bridge_cli.loop_stop()
        bridge_cli.disconnect()

    print("metric name is: task_status")


if __name__ == "__main__":

    main()
