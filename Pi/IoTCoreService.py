from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import paho.mqtt.client as paho
import logging
import os
import threading
import time
import json
from InternetService import is_connected_to_internet

thermostatId = None  

latest_messages = {
    "temperatureRequests": None,
    "updatedScheduleRequests": None
}

external_callbacks = {
    "temperatureRequests": None,
    "updatedScheduleRequests": None
}

def customCallback(client, userdata, message):
    global latest_messages

    print(f"--> Received a new message: {message.payload}")
    print(f"--> from topic: {message.topic}\n")

    message_dict = json.loads(message.payload.decode('utf-8'))
    
    for key, topic in TOPICS.items():
        if message.topic == topic:
            latest_messages[key] = message_dict
            if external_callbacks[key]:
                external_callbacks[key](message_dict)
            break

logger = logging.getLogger("AWSIoTPythonSDK.core")
logger.setLevel(logging.WARNING)

streamHandler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
streamHandler.setFormatter(formatter)
logger.addHandler(streamHandler)

mqtt_client = AWSIoTMQTTClient("MyClientID")
mqtt_client.configureEndpoint("amgaupjb9mzud-ats.iot.eu-central-1.amazonaws.com", 8883)

current_dir = os.getcwd()
root_ca = os.path.join(current_dir, 'certs/AmazonRootCA1.pem')
private_key = os.path.join(current_dir, 'certs/49acbbea06ff7300fb1183c2312953fc2c30edc6016e6be49d7d7dce00fe6f44-private.pem.key')
certificate = os.path.join(current_dir, 'certs/49acbbea06ff7300fb1183c2312953fc2c30edc6016e6be49d7d7dce00fe6f44-certificate.pem.crt')

mqtt_client.configureCredentials(root_ca, private_key, certificate)
mqtt_client.configureOfflinePublishQueueing(-1) # Infinite Publish Queue
mqtt_client.configureDrainingFrequency(2)
mqtt_client.configureConnectDisconnectTimeout(10)
mqtt_client.configureMQTTOperationTimeout(5)


def start_mqtt_client():
    global TOPICS

    if not thermostatId:
        raise ValueError("thermostatId is not set")

    TOPICS = {
        "temperatureRequests": f"thermostats/{thermostatId}/temperatureRequests",
        "updatedScheduleRequests": f"thermostats/{thermostatId}/updatedScheduleRequests"
    }
    
    mqtt_client.connect()
    print("Connected to MQTT broker")
    
    for topic_name, topic in TOPICS.items():
        mqtt_client.subscribe(topic, 1, customCallback)
        print(f"Subscribed to topic: {topic}")
    
    while True:
        time.sleep(5)


def start_mqtt_thread():
    mqtt_thread = threading.Thread(target=start_mqtt_client)
    mqtt_thread.daemon = True
    mqtt_thread.start()


def get_latest_message(topic_name):
    return latest_messages.get(topic_name)


def register_callback(topic_name, callback):
    if topic_name in external_callbacks:
        external_callbacks[topic_name] = callback
    else:
        raise ValueError(f"No such topic: {topic_name}")
    

paho_client = paho.Client()

def on_connect(client, userdata, flags, rc):
    print(f"Paho client connected with result code {rc}")

paho_client.on_connect = on_connect
paho_client.tls_set(root_ca, certfile=certificate, keyfile=private_key)


def publish_thermostat_status(ambientTemperature, heatingStatus, ambientHumidity):
    if not thermostatId:
        raise ValueError("thermostatId is not set")

    topic = f"thermostats/{thermostatId}/status"
    message = {
        "ambientTemperature": ambientTemperature,
        "heatingStatus": heatingStatus,
        "ambientHumidity": ambientHumidity
    }
    
    paho_client.publish(topic, json.dumps(message), qos=1, retain=True)
    print(f"Published message to {topic}: {message}")

def start_iot_core_service():
    paho_client.connect("amgaupjb9mzud-ats.iot.eu-central-1.amazonaws.com", 8883, 60)
    paho_client.loop_start()