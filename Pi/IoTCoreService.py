# IoTCoreService.py

from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import logging
import os
import threading
import time

thermostatId = None
latest_message = None 

def customCallback(client, userdata, message):
    global latest_message
    latest_message = message.payload
    print(f"Received a new message: {message.payload}")
    print(f"from topic: {message.topic}\n")

logger = logging.getLogger("AWSIoTPythonSDK.core")
logger.setLevel(logging.INFO)
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
    mqtt_client.connect()
    topic = "thermostat/" + thermostatId + "/mode"
    mqtt_client.subscribe(topic, 1, customCallback)
    
    while True:
        time.sleep(5)

def start_mqtt_thread():
    mqtt_thread = threading.Thread(target=start_mqtt_client)
    mqtt_thread.daemon = True
    mqtt_thread.start()
