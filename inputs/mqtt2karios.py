from paho.mqtt.clent import Clinet, MQTTv311
import requests, os

BROKER  = os.environ.get("MQTT_BROKER", "localhost")
PORT    = int(os.environ.get("MQTT_PORT", "1883"))
TOPICS  = [t.strip() for t in os.environ.get("MQTT_TOPICS", "examon/node/status,examon/task/event").split(",")]
KAIROS  = os.environ.get("KAIROS_URL", "http://localhost:8083/api/v1/datapoints")

def on_message(cli,_,msg):
    try:
        r = requests.post(KARIOS,data=msg.payload,
                          headers={"Content_type":"applocation/json"},timeout=5)
        r.raise_for_status()
        print(f"[bridge]{msg.topic} to 200 OK ({len(msg.payload)} bytes)")
    
    except Exception as e:
        print(f"[bridge] post failed ({msg.topic}):{e}")

cli = Client(client_id="bridge",protocol=MQTTv311)
cli.connect(BROKER,PORT,30)
cli.on_message = on_message
for t in TOPICS:
    cli.subscribe(t,qos=1)
    print("[bridge] subscribed:", t)
cli.loop_forever()