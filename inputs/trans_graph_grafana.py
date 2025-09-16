# csv_to_mqtt_kairosdb_json.py
# Read CSV -> build KairosDB JSON -> publish to MQTT (two topics: node/task)

import ast
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
import os,time
import pandas as pd
import requests
from requests.adapters import HTTPAdapter

# ----------------------- Configuration -----------------------
KAIROS   = "http://localhost:8083/api/v1/datapoints"
CSV_PATH = "merged_events.csv"
DUMP_ENABLE     = True                 
DUMP_DIR        = "payload_dump"       
DUMP_COMBINED   = "all_points.ndjson"

HTTP_BATCH_SIZE = 200
HTTP_TIMEOUT    = 30
BATCH_PAUSE_S = 0.02
# -------------------------------------------------------------

# Metric names
METRIC_TASK_NODE_STATUS = "task_status"
METRIC_NODE_STATUS      = "node_status"
METRIC_TASK_NODE_EDGE   = "task_node_edge"
# For Grafana Node Graph
METRIC_GRAPH_NODES = "graph_nodes"
METRIC_GRAPH_EDGES = "graph_edges"

# ----------------------- Helpers -----------------------------
def to_ms(ts) -> Optional[int]:
    """pandas/numpy datetime -> epoch ms (UTC)."""
    if pd.isna(ts):
        return None
    if isinstance(ts, (pd.Timestamp, datetime)):
        dt = ts.tz_convert("UTC") if getattr(ts, "tzinfo", None) else pd.Timestamp(ts).tz_localize("UTC")
        return int(dt.timestamp() * 1000)
    dt = pd.to_datetime(ts, utc=True, errors="coerce")
    if pd.isna(dt):
        return None
    return int(dt.timestamp() * 1000)

def parse_cell_to_list(s) -> List[Dict[str, Any]]:
    """Robustly parse a cell into list[dict]."""
    if s is None or (isinstance(s, float) and pd.isna(s)) or (isinstance(s, str) and not s.strip()):
        return []
    if isinstance(s, list): return s
    if isinstance(s, dict): return [s]
    if isinstance(s, str):
        txt = s.strip()
        try:
            v = json.loads(txt)
            if isinstance(v, dict): return [v]
            if isinstance(v, list): return v
        except Exception:
            pass
        try:
            v = ast.literal_eval(txt)
            if isinstance(v, dict): return [v]
            if isinstance(v, list): return v
        except Exception:
            pass
        return [{"_raw_string": txt}]
    return []

def deep_get_any(d, keys):
    """Depth-first search for the first non-empty value for any of `keys`."""
    if isinstance(d, dict):
        for k in keys:
            if k in d and d[k] not in (None, ""):
                return d[k]
        for v in d.values():
            got = deep_get_any(v, keys)
            if got not in (None, ""):
                return got
    elif isinstance(d, list):
        for v in d:
            got = deep_get_any(v, keys)
            if got not in (None, ""):
                return got
    return None

def s(v) -> str:
    """Force tag values to string (KairosDB requires)."""
    if v is None: return ""
    return str(v)

def sanitize_tag(v: str) -> str:
    return s(v).replace("MCAGraphObject://", "")

# Task state mapping
TASK_STATE_MAP  = {
    "TASK_QUEUED": 1, "TASK_RUNNING": 2, "TASK_TERMINATED": 0,
    "QUEUED": 1, "RUNNING": 2, "TERMINATED": 0,
}
TASK_STATE_TEXT = {0: "TERMINATED", 1: "QUEUED", 2: "RUNNING"}

# --------------------- Build datapoints ----------------------
def build_all_datapoints(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Return a flat list of KairosDB datapoint objects (NOT wrapped in outer array).
    Each element looks like:
      {
        "name": "...",
        "datapoints": [[ts_ms, value]],
        "tags": {"k": "v", ...}
      }
    """
    out: List[Dict[str, Any]] = []
    df = df.copy()

    if "timestamp" not in df.columns:
        return out

    # ---- Expand job_event ----
    if "job_event" in df.columns:
        df["job_event_list"] = df["job_event"].apply(parse_cell_to_list)
        df = df.explode("job_event_list").dropna(subset=["job_event_list"])
        df["event"]          = df["job_event_list"].apply(lambda x: deep_get_any(x, ["event","status","state"]))
        df["task_id"]        = df["job_event_list"].apply(lambda x: deep_get_any(x, ["task_id","taskId","task","id"]))
        df["task_name"]      = df["job_event_list"].apply(lambda x: deep_get_any(x, ["task_name","taskName","name"]))
        df["task_graph_id"]  = df["job_event_list"].apply(lambda x: deep_get_any(x, ["task_graph_id","graphId","graph","workflow_id"]))
        df["node_id_evt"]    = df["job_event_list"].apply(lambda x: deep_get_any(x, ["node_id","nodeId","node","hostname","host"]))
    else:
        for c in ["event","task_id","task_name","task_graph_id","node_id_evt"]:
            if c not in df.columns: df[c] = None

    # ---- Fallback node_id from node_status ----
    if "node_status" in df.columns:
        df["node_status_list"] = df["node_status"].apply(parse_cell_to_list)
        node_id_fallback = df["node_status_list"].apply(
            lambda x: deep_get_any(x, ["node_id","nodeId","id","hostname","host","name","node","_raw_string"])
                      if isinstance(x, list) else None
        )
    else:
        df["node_status_list"] = [[] for _ in range(len(df))]
        node_id_fallback = None


    df["node_id"] = df["node_id_evt"]
    if node_id_fallback is not None:
        df["node_id"] = df["node_id"].where(df["node_id"].notna() & (df["node_id"] != ""), node_id_fallback)

#    for _, r in work.iterrows():
#       #task points
#        val = TASK_STATE_MAP.get(str(r["event"]).upper(), 2)
#        task_id = str(r.get("task_id", ""))
#        task_name = str(r.get("task_name", "")) if pd.notna(r.get("task_name", "")) else ""
#        task_graph_id = str(r.get("task_graph_id", "")) if pd.notna(r.get("task_graph_id", "")) else ""
#        node_id = str(r.get("node_id", "")) if pd.notna(r.get("node_id", None)) else ""


    # ---- Time ----
    df = df.dropna(subset=["timestamp"]).copy()
    df["ts_ms"] = df["timestamp"].apply(to_ms)
    df = df.dropna(subset=["ts_ms"]).sort_values("ts_ms")

    # ---- Rows that contain a task (task_id comes only from job_event) ----
    with_task = df.dropna(subset=["task_id"]).copy()

    print(f"[BUILD] rows total={len(df)}, with task_id={len(with_task)}, with node_id={with_task['node_id'].notna().sum()}")

    emitted_node_ids = set()

    # ---------- emit from task rows ----------
    for _, r in with_task.iterrows():
        ts = int(r["ts_ms"])
        event_raw = s(r.get("event","")).upper()
        val = TASK_STATE_MAP.get(event_raw, 2)

        task_id       = sanitize_tag(r.get("task_id",""))
        task_name     = s(r.get("task_name","")) or task_id
        task_graph_id = sanitize_tag(r.get("task_graph_id",""))
        node_id       = sanitize_tag(r.get("node_id",""))

        # task_status
        task_tags = {
            "id": task_id,
            "type": "task",
            "task_id": task_id,
            "task_name": task_name,
            "task_graph_id": task_graph_id,
            "state_text": TASK_STATE_TEXT.get(val, "RUNNING"),
        }
        if node_id:
            task_tags["node_id"] = node_id

        out.append({
            "name": METRIC_TASK_NODE_STATUS,
            "datapoints": [[ts, int(val)]],
            "tags": {k: s(v) for k, v in task_tags.items()},
        })

        # node_status + edge if we have node_id
        if node_id:
            if node_id not in emitted_node_ids:
                out.append({
                    "name": METRIC_NODE_STATUS,
                    "datapoints": [[ts, 1]],
                    "tags": {"id": s(node_id), "type": "node", "node_id": s(node_id)},
                })
                emitted_node_ids.add(node_id)

            edge_id = f"{task_id}_{node_id}"
            out.append({
                "name": METRIC_TASK_NODE_EDGE,
                "datapoints": [[ts, 1]],
                "tags": {
                    "id": s(edge_id),
                    "source": s(task_id),
                    "target": s(node_id),
                    "title": s(f"{task_name}->{node_id}"),
                },
            })

        # graph_nodes: task
        out.append({
            "name": METRIC_GRAPH_NODES,
            "datapoints": [[ts, 1]],
            "tags": {"id": s(task_id), "title": s(task_name), "type": "task"},
        })

        # graph_nodes: node + graph_edges
        if node_id:
            out.append({
                "name": METRIC_GRAPH_NODES,
                "datapoints": [[ts, 1]],
                "tags": {"id": s(node_id), "title": s(node_id), "type": "node"},
            })
            out.append({
                "name": METRIC_GRAPH_EDGES,
                "datapoints": [[ts, 1]],
                "tags": {
                    "id": s(f"{task_id}_{node_id}"),
                    "source": s(task_id),
                    "target": s(node_id),
                    "title": s(f"{task_name}->{node_id}"),
                },
            })

    # ---------- emit pure nodes from node_status (even when no task rows) ----------
    ns_rows = df.loc[df["node_status_list"].astype(bool), ["ts_ms","node_status_list"]]
    for _, r in ns_rows.iterrows():
        ts = int(r["ts_ms"])
        for ent in r["node_status_list"]:
            nid = sanitize_tag(deep_get_any(ent, ["node_id","nodeId","id","hostname","host","name","node","_raw_string"]))
            if not nid:
                continue
            out.append({
                "name": METRIC_NODE_STATUS,
                "datapoints": [[ts, 1]],
                "tags": {"id": s(nid), "type": "node", "node_id": s(nid)},
            })
            out.append({
                "name": METRIC_GRAPH_NODES,
                "datapoints": [[ts, 1]],
                "tags": {"id": s(nid), "title": s(nid), "type": "node"},
            })

    return out

# ------------------ Direct HTTP poster -----------------------
def post_in_batches(session: requests.Session, all_points: List[Dict[str, Any]]):
    total = len(all_points)
    sent = 0
    idx = 0

    while idx < total:
        batch = all_points[idx: idx + HTTP_BATCH_SIZE]
        payload = json.dumps(batch, separators=(",", ":"))


        if DUMP_ENABLE:
            fname = f"batch_{idx:06d}_{idx+len(batch)-1:06d}.json"
            fpath = os.path.join(DUMP_DIR, fname)
            with open(fpath, "w", encoding="utf-8") as f:
                f.write(payload)
            with open(os.path.join(DUMP_DIR, DUMP_COMBINED), "a", encoding="utf-8") as g:
                for obj in batch:
                    g.write(json.dumps(obj, ensure_ascii=False) + "\n")
            print(f"[DUMP] wrote {fname} ({len(payload)} bytes)")


        headers = {"Content-Type": "application/json", "Connection": "close"}

        r = session.post(KAIROS, data=payload, headers=headers, timeout=HTTP_TIMEOUT)
        print(f"[POST] {idx}-{idx+len(batch)-1}/{total-1} status={r.status_code}")
        r.raise_for_status()


        time.sleep(0.02)

        sent += len(batch)
        idx  += len(batch)

    print(f"[DONE] posted datapoints: {sent}")

#  MQTT to KairosDB bridge

# ---------------------------- main ---------------------------
def main():
    # Load CSV
    try:
        df = pd.read_csv(CSV_PATH, parse_dates=["timestamp"])
    except Exception as e:
        print(f"[Error] Failed to read CSV '{CSV_PATH}': {e}")
        return

    print(f"[CSV] rows={len(df)} cols={list(df.columns)}")

    # Build all datapoints (flat list of dicts)
    points = build_all_datapoints(df)
    print(f"[BUILD] datapoints={len(points)}")
    if not points:
        print("[Warn] No datapoints built from CSV.")
        return
    if DUMP_ENABLE:
        os.makedirs(DUMP_DIR, exist_ok=True)
        open(os.path.join(DUMP_DIR, DUMP_COMBINED), "w").close()

    session = requests.Session()
    try:
        from urllib3.util.retry import Retry
        retry = Retry(total=5, backoff_factor=0.3, status_forcelist=(429, 500, 502, 503, 504))
        adapter = HTTPAdapter(max_retries=retry, pool_connections=20, pool_maxsize=50)
        session.mount("http://", adapter)
    except Exception:
        pass

    # Quick sanity print: one graph_edges example to prove tags are present
    for obj in points:
        if obj.get("name") == METRIC_GRAPH_EDGES:
            print("[DEBUG sample graph_edges]", json.dumps(obj, ensure_ascii=False)[:300], "...")
            break

    # Direct HTTP posting (no sleeps)
    post_in_batches(session, points)

    print("metrics ready:")
    print(f"  - {METRIC_TASK_NODE_STATUS}")
    print(f"  - {METRIC_NODE_STATUS}")
    print(f"  - {METRIC_TASK_NODE_EDGE}")
    print(f"  - {METRIC_GRAPH_NODES}")
    print(f"  - {METRIC_GRAPH_EDGES}")


if __name__ == "__main__":
    main()


