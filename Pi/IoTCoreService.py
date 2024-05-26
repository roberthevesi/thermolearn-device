# IoTCoreService.py

from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import logging
import os
import threading
import time
import json

# Initialize thermostatId
thermostatId = None  # This will be set by an external function

# Dictionary to store the latest messages from each topic
latest_messages = {
    "temperatureRequests": None,
    "updatedScheduleRequests": None
}

# Dictionary to store the external callbacks for each topic
external_callbacks = {
    "temperatureRequests": None,
    "updatedScheduleRequests": None
}

def customCallback(client, userdata, message):
    global latest_messages

    print(f"--> Received a new message: {message.payload}")
    print(f"--> from topic: {message.topic}\n")

    message_dict = json.loads(message.payload.decode('utf-8'))
    
    # Determine which topic this message came from and update the respective entry in latest_messages
    for key, topic in TOPICS.items():
        if message.topic == topic:
            latest_messages[key] = message_dict
            # Trigger the external callback if registered
            if external_callbacks[key]:
                external_callbacks[key](message_dict)
            break

# Configure the logger for AWSIoTPythonSDK
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

    # Ensure thermostatId is set
    if not thermostatId:
        raise ValueError("thermostatId is not set")

    # Define the topics to subscribe to using the thermostatId
    TOPICS = {
        "temperatureRequests": f"thermostats/{thermostatId}/temperatureRequests",
        "updatedScheduleRequests": f"thermostats/{thermostatId}/updatedScheduleRequests"
    }
    
    mqtt_client.connect()
    print("Connected to MQTT broker")
    
    # Subscribe to all topics in the TOPICS dictionary
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
