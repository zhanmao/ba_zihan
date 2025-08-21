#from paho.mqtt.client import Client, MQTTv311
#import time, random, json
#from datetime import datetime, timezone
#
#BROKER = "localhost"
#PORT   = 1883
#TOPIC  = "metric/test"
#KAIROS = "http://localhost:8083/api/v1/datapoints"
#
#def now_ms():  
#    return int(datetime.now(tz=timezone.utc).timestamp() * 1000)
#
#def make_payload():
#    pkt = [{
#        "name": "test",
#        "datapoints": [[now_ms(), random.randint(0, 100)]],
#        "tags": {"test1": "demo"}      
#    }]
#    return json.dumps(pkt, separators=(",", ":"))
#
#cli = Client(client_id="json_pub", protocol=MQTTv311)
#cli.connect(BROKER, PORT, 30)
#cli.loop_start()
#
#try:
#    while True:
#        payload = make_payload()
#        info = cli.publish(TOPIC, payload, qos=1)
#        info.wait_for_publish()        
#        print("sent:", payload)
#        time.sleep(2)
#except KeyboardInterrupt:
#    pass
#finally:
#    cli.loop_stop()
#    cli.disconnect()

from paho.mqtt.client import Client, MQTTv311
import time, random, json, requests
from datetime import datetime, timezone
import threading

BROKER = "localhost"; PORT = 1883
TOPIC  = "metric/test"
KAIROS = "http://localhost:8083/api/v1/datapoints" #need to have mqtt to karios in the programm

def now_ms():  
    return int(datetime.now(tz=timezone.utc).timestamp() * 1000)

def make_payload():#karios JSON fromat
    return json.dumps([{
        "name": "test",
        "datapoints": [[now_ms(), random.randint(0, 100)]],
        "tags": {"test1": "demo"}
    }], separators=(",", ":"))

def on_message(cli, _, msg):#mqtt to karios
    try:
        r = requests.post(KAIROS, data=msg.payload,
                          headers={"Content-Type": "application/json"})
        r.raise_for_status()
        print("forwarded", len(msg.payload), "bytes")
    except Exception as e:
        print("post failed:", e)

def publisher():#publish mqttt to topic
    pub = Client(client_id="json_pub", protocol=MQTTv311)
    pub.connect(BROKER, PORT, 30)
    pub.loop_start()
    try:
        while True:
            p = make_payload()
            pub.publish(TOPIC, p, qos=1).wait_for_publish()
            print("sent:", p)
            time.sleep(2)
    finally:
        pub.loop_stop()
        pub.disconnect()

def bridge():
    sub = Client(client_id="bridge", protocol=MQTTv311)
    sub.connect(BROKER, PORT, 30)
    sub.on_message = on_message
    sub.subscribe(TOPIC, qos=1)
    sub.loop_forever()

if __name__ == "__main__":
    threading.Thread(target=bridge, daemon=True).start()
    publisher()