# csv_to_mqtt_kairosdb_json.py
# Read CSV -> build KairosDB JSON -> publish to MQTT (two topics: node/task)

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



METRIC_TASK_NODE_STATUS = "task_status"      
METRIC_NODE_STATUS      = "node_status"      
METRIC_TASK_NODE_EDGE   = "task_node_edge"   

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


TASK_STATE_TEXT = {
    0: "TERMINATED",
    1: "QUEUED",
    2: "RUNNING",
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
        
        required = {"event", "task_id"}
        if not required.issubset(df.columns):
            return out
        work = df

    if "timestamp" not in work.columns:
        return out

    work = work.dropna(subset=["timestamp", "task_id", "event"]).copy()
    work["ts_ms"] = work["timestamp"].apply(to_ms)
    work = work.dropna(subset=["ts_ms"]).sort_values("ts_ms")

   
    emitted_nodes = set()

    for _, r in work.iterrows():
       #task point
        val = TASK_STATE_MAP.get(str(r["event"]).upper(), 2)
        task_id = str(r.get("task_id", ""))
        task_name = str(r.get("task_name", "")) if pd.notna(r.get("task_name", "")) else ""
        task_graph_id = str(r.get("task_graph_id", "")) if pd.notna(r.get("task_graph_id", "")) else ""
        node_id = str(r.get("node_id", "")) if pd.notna(r.get("node_id", None)) else ""

       
        task_tags = {
            "id": task_id,                         
            "type": "task",                        
            "task_name": task_name,
            "task_graph_id": task_graph_id,
            "state_text": TASK_STATE_TEXT.get(val, "RUNNING"), 
          
        }
        if node_id:
            task_tags["node_id"] = node_id  

        payload_task_status = [
            {
                "name": METRIC_TASK_NODE_STATUS,
                "datapoints": [[int(r["ts_ms"]), int(val)]],
                "tags": task_tags,
            }
        ]
        out.append((TOPIC, json.dumps(payload_task_status, separators=(",", ":"))))

       
        if node_id:
            if node_id not in emitted_nodes:
                node_tags = {
                    "id": node_id,     
                    "type": "node",     
                    "node_id": node_id, 
                  
                }
                payload_node_status = [
                    {
                        "name": METRIC_NODE_STATUS,
                        "datapoints": [[int(r["ts_ms"]), 1]],  # 存在即可
                        "tags": node_tags,
                    }
                ]
                out.append((TOPIC, json.dumps(payload_node_status, separators=(",", ":"))))
                emitted_nodes.add(node_id)

           
            edge_tags = {
                "source": task_id,            
                "target": node_id,            
                "edge_type": "assignment",     
                "task_name": task_name,        
                "task_graph_id": task_graph_id
                
            }
            payload_task_node_edge = [
                {
                    "name": METRIC_TASK_NODE_EDGE,
                    "datapoints": [[int(r["ts_ms"]), 1]], 
                    "tags": edge_tags,
                }
            ]
            out.append((TOPIC, json.dumps(payload_task_node_edge, separators=(",", ":"))))

    return out


#  MQTT to KairosDB bridge
def on_message(cli, _, msg):
    try:
        r = requests.post(KAIROS, data=msg.payload,
                          headers={"Content-Type":"application/json"})
        print("[Bridge] POST", KAIROS, "status=", r.status_code)
        if r.status_code >= 400:
            print("[Bridge] resp:", r.text[:400])
        r.raise_for_status()
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

    #from csv to mqtt
    pub_cli = Client(client_id="csv2mqtt_pub", protocol=MQTTv311)
    pub_cli.connect(BROKER, PORT, 30)
    pub_cli.loop_start()

    
    bridge_cli = Client(client_id="mqtt2kairos", protocol=MQTTv311)
    bridge_cli.connect(BROKER, PORT, 30)
    bridge_cli.on_message = on_message
    bridge_cli.subscribe(TOPIC, qos=1)
    bridge_cli.loop_start()

    try:
        for topic, payload in messages:
            pub_cli.publish(topic, payload, qos=1)
            print(f"[Publish] {topic} -> {payload}")
            time.sleep(0.05)  
    finally:
        pub_cli.loop_stop()
        pub_cli.disconnect()
        bridge_cli.loop_stop()
        bridge_cli.disconnect()

    print("metrics:")
    print(f"  - {METRIC_TASK_NODE_STATUS} (task nodes)")
    print(f"  - {METRIC_NODE_STATUS} (compute nodes)")
    print(f"  - {METRIC_TASK_NODE_EDGE} (edges: task -> node)")


if __name__ == "__main__":
    main()