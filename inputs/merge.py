import pandas as pd
<<<<<<< HEAD
import json, paho.mqtt.client as mqtt
import sys


#read charts
df_job   = pd.read_csv("job.csv", parse_dates=["timestamp"])
df_node  = pd.read_csv("node.csv",parse_dates=["timestamp"])
#print(df_node.columns.tolist())
#df_set   = pd.read_csv("set.csv",parse_dates=["timestamp"])
#df_setop = pd.read_csv("setop.csv",parse_dates=["timestamp"])

#time transfer
def time_tr(df):
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit='s')
    return df

df_job = time_tr(df_job)
df_node = time_tr(df_node)


#merge all the tag into 1 tag
def group(df):
    tag_besides = [c for c in df.columns if c != "timestamp"]
    s = df.groupby("timestamp").apply(lambda g: g[tag_besides].to_dict(orient="records"))
    grouped = s.reset_index(name="node_status")
    return grouped

df_job_g = group(df_job)
df_node_g = group(df_node)

#use timestamp as index
for df in (df_job_g,df_node_g):
    df.set_index("timestamp", inplace=True)
    df.sort_index(inplace=True)

#df_node = df_node.set_index("timestamp").sort_index()

#fill the sates for the node 
def ffill_df(df):
    full_idx = pd.date_range(df.index.min(),
                             df.index.max(),
                             freq="s")
    df_full = df.reindex(full_idx, method="ffill")
    df_full.index.name= "timestamp"
    return df_full

df_node_full = ffill_df(df_node_g)

#merged chart by timestamp
points_idx = sorted(
    set(df_job_g.index)
    .union(set(df_node_full.index))
)


merged = pd.DataFrame(index=points_idx)
merged = merged.join(df_node_full, how="left")

#create a instant job event
tag_cols = [c for c in df_job_g.columns if c!="timestamp"]
job_info = df_job_g[tag_cols]   
job_info.index.name = "timestamp"
job_entries = df_job_g
merged["job_event"] = job_entries.reindex(points_idx) #use all the event as job event

merged.index.name = "timestamp"
merged.reset_index().to_csv("merged_events.csv",index=False)

#send to examon via mqtt
client = mqtt.Client()
client.connect("127.0.0.1",1883)
client.subscribe("#") 

for row in pd.read_csv("merged_events.csv", parse_dates=["timestamp"]).itertuples():
    time_s = row.timestamp.isoformat()
    node_status = row.node_status
    job_datas = row.job_event
    has_job = bool(row.job_event)



    payload = {
      "name":"status",
      "timestamp": time_s,
      "value": 2 if has_job else 1,
      "tags": {
        "source": "merged",
        "node_data": node_status,
        **({"job_data": job_datas} if has_job else {})
      }
    }

    result = client.publish("examon_mertic", json.dumps(payload))
    print(result)
    
#payload_node ={
#    "name": "node_status",
#    "timestamp": time_s.isoformat(),
#    "value": 1,
#    "tags": {"source":"merged", "node_statu":node_status}
#}
#client.publish("examon_mertic", json.dumps(payload_node))
#
#
#
#payload_job = {
#    "name": "job_event",
#    "timestamp": time_s.isoformat(),
#    "value": 1 if pd.notna(job_name) else 0,
#    "tags": {"source":"merged", "job_data": job_name}
#}
#client.publish("examon_mertic", json.dumps(payload_job))


#merged.reset_index().rename(columns={'index':'timestamp'}).to_csv("merged_n_j.csv",index = False )

client.disconnect()
=======
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
>>>>>>> master
