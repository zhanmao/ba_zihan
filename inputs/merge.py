import pandas as pd
import json, requests, time

#read csv
def to_dt(df):
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s")
    return df

df_job  = to_dt(pd.read_csv("job.csv"))
df_node = to_dt(pd.read_csv("node.csv"))

def group(df, payload_col):
    others = [c for c in df.columns if c != "timestamp"]
    return (df.groupby("timestamp")
              .apply(lambda g: g[others].to_dict("records"))
              .reset_index(name=payload_col)
              .set_index("timestamp")
              .sort_index())

df_job_g  = group(df_job,  "job_event")
df_node_g = group(df_node, "node_status")


full_idx      = pd.date_range(df_node_g.index.min(),
                              df_node_g.index.max(),
                              freq="s")
df_node_full  = df_node_g.reindex(full_idx, method="ffill")


points_idx = sorted(set(df_job_g.index) | set(df_node_full.index))
merged     = (pd.DataFrame(index=points_idx)
                .join(df_node_full, how="left")
                .join(df_job_g,  how="left"))


KAIROS_URL = "http://localhost:8083/api/v1/datapoints"
HEADERS    = {"Content-Type": "application/json"}

def ts_ms(ts) -> int:
    return int(pd.Timestamp(ts).timestamp() * 1000)


session = requests.Session()

for row in merged.itertuples():
    t_ms     = ts_ms(row.Index)
    job_list = row.job_event  if isinstance(row.job_event,  list) else []
    node_list= row.node_status if isinstance(row.node_status, list) else []

    datapoints = []

    # metric
    datapoints.append({
        "name"      : "merged",
        "datapoints": [[t_ms, 2 if job_list else 1]],
        "tags"      : {"kind": "status"}
    })

    # nodestatus
    for node in node_list:
        datapoints.append({
            "name": "merged",
            "datapoints": [[t_ms, 1]],
            "tags": {"kind": "node", **{k:str(v) for k,v in node.items()}}
        })

    # jobevents
    for job in job_list:
        datapoints.append({
            "name": "merged",
            "datapoints": [[t_ms, 1]],
            "tags": {"kind": "job", **{k:str(v) for k,v in job.items()}}
        })

    # to kariosdb by json
    resp = session.post(KAIROS_URL, headers=HEADERS, data=json.dumps(datapoints))
    resp.raise_for_status()          
    print(f"✓ {row.Index} sent {len(datapoints)} datapoints")

print("\n all data was loaded")