import ast
import pandas as pd
from dash import Dash, html, dcc, Input, Output
import datetime as dt
import plotly.graph_objects as go


##read the csv
df = pd.read_csv("merged_events.csv", parse_dates=["timestamp"])
df["job_event"] = df["job_event"].fillna("[]")            

#solve the problem between "" and ''
def parse_events(s):
    if not isinstance(s, str):
        return []
    try:
        return ast.literal_eval(s)
    except Exception:
        return []

df["job_event_list"] = df["job_event"].apply(parse_events)
exploded = df.explode("job_event_list").dropna(subset=["job_event_list"])




for col in ["event", "task_id", "task_name", "task_graph_id"]:
    exploded[col] = exploded["job_event_list"].apply(lambda x: x.get(col))
time_marks = sorted(exploded["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S").unique())


#count the max tasks
def active_count(t):
    sub = exploded[exploded["timestamp"] <= t]
    last = sub.sort_values("timestamp").groupby("task_id").last()
    return (last["event"] != "TASK_TERMINATED").sum()

max_tasks = max(active_count(pd.to_datetime(t)) for t in time_marks)
MAX_SLOTS  = min(max_tasks, 9) or 1        

#compare the task status
change_points = []


exploded_sorted = exploded.sort_values(["task_id", "timestamp"])
for task_id, grp in exploded_sorted.groupby("task_id"):
    prev_event = None
    for _, row in grp.iterrows():
        if row["event"] != prev_event:
            change_points.append({
                "timestamp": row["timestamp"],
                "task_id": task_id,
                "event": row["event"]
            })
            prev_event = row["event"]

from collections import defaultdict
change_dict = defaultdict(list)
for pt in change_points:
    change_dict[pt["timestamp"]].append(pt["task_id"])

#red point
def build_timeline_figure():
    
    x_vals = list(change_dict.keys())
    y_vals = [0] * len(x_vals)
    hover = [
        "<br>".join(change_dict[t]) for t in x_vals
    ]  

    fig = go.Figure(
        data=go.Scatter(
            x=x_vals,
            y=y_vals,
            mode="markers",
            marker=dict(color="red", size=8),
            hoverinfo="text",
            text=hover
        )
    )
    fig.update_layout(
        height=120,
        margin=dict(l=20, r=20, t=10, b=10),
        xaxis=dict(showticklabels=False),  
        yaxis=dict(visible=False)
    )
    return fig

#2 dashapp
app = Dash(__name__)
app.layout = html.Div([
    html.H2("Visualize task data"),

    dcc.Graph(
    id="timeline_graph",
    figure=build_timeline_figure(),
    config={"displayModeBar": False}
),
    #time line
    dcc.Slider(
        id="time_slider",
        min=0,
        max=len(time_marks) - 1,
        step=1,
        value=0,
        marks={i: time_marks[i] for i in range(0, len(time_marks), max(1, len(time_marks)//10))}
    ),

    # cards
    html.Div(
        id="grid_container",
        style={
            "display": "grid",
            "gridTemplateColumns": "repeat(3, 1fr)",
            "gridTemplateRows": "repeat(3, auto)",
            "gridGap": "10px",
            "width": "95vw",
            "marginTop": "20px"
        },
        children=[]  
    )
])


@app.callback(
    Output("grid_container", "children"),
    Input("time_slider", "value")
)
def update_cards(idx):
    
    current_time = pd.to_datetime(time_marks[idx])

   
    sub  = exploded[exploded["timestamp"] <= current_time]
    last = sub.sort_values("timestamp").groupby("task_id").last().reset_index()

    
    active = last[last["event"] != "TASK_TERMINATED"]

    cards = []
    for _, row in active.iterrows():
        cards.append(
            html.Div(
                style={
                    "border": "1px solid #888",
                    "borderRadius": "8px",
                    "padding": "8px",
                    "backgroundColor": "#F5F5F5"
                },
                children=[
                    html.H4(row["task_name"], style={"margin": "4px 0 8px 0"}),

                    html.Details([
                        html.Summary("Status"),
                        html.P(row["event"], style={"margin": "4px 0"})
                    ]),
                    html.Details([
                        html.Summary("Task ID"),
                        html.P(row["task_id"], style={"margin": "4px 0"})
                    ]),
                    html.Details([
                        html.Summary("Graph ID"),
                        html.P(row["task_graph_id"], style={"margin": "4px 0"})
                    ])
                ]
            )
        )

    
    for _ in range(MAX_SLOTS - len(cards)):
        cards.append(html.Div())

    return cards
@app.callback(
    Output("time_slider", "value"),
    Input("timeline_graph", "clickData"),
    prevent_initial_call=True
)
def jump_from_dot(clickData):
    
    ts = clickData["points"][0]["x"]
    
    idx = time_marks.index(pd.to_datetime(ts).strftime("%Y-%m-%d %H:%M:%S"))
    return idx


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8050)