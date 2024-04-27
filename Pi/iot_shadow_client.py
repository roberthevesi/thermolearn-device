# iot_shadow_client.py
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTShadowClient
import os
import json
import threading

# Constants and configuration
endpoint = "amgaupjb9mzud-ats.iot.eu-central-1.amazonaws.com"
thing_name = "RaspberryPiThing"
current_dir = os.getcwd()
root_ca = os.path.join(current_dir, 'certs/AmazonRootCA1.pem')
private_key = os.path.join(current_dir, 'certs/49acbbea06ff7300fb1183c2312953fc2c30edc6016e6be49d7d7dce00fe6f44-private.pem.key')
certificate = os.path.join(current_dir, 'certs/49acbbea06ff7300fb1183c2312953fc2c30edc6016e6be49d7d7dce00fe6f44-certificate.pem.crt')

# Initialize MQTT Shadow Client
shadow_client = AWSIoTMQTTShadowClient(thing_name)
shadow_client.configureEndpoint(endpoint, 8883)
shadow_client.configureCredentials(root_ca, private_key, certificate)
shadow_client.connect()

# Create a device shadow handler
device_shadow_handler = shadow_client.createShadowHandlerWithName(thing_name, True)

# Event for synchronization
desired_state_event = threading.Event()
desired_state_info = {}

def shadow_callback(payload, responseStatus, token):
    global desired_state_info
    try:
        if responseStatus == 'accepted':
            payload_dict = json.loads(payload)
            desired_state_info = payload_dict.get('state', {}).get('desired', {})
        else:
            print("Failed to get the desired state:", responseStatus)
    except json.JSONDecodeError:
        print("Error decoding JSON payload")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    finally:
        desired_state_event.set()

def get_shadow():
    device_shadow_handler.shadowGet(shadow_callback, 0.5)  # Adjust timeout to a reasonable value
    desired_state_event.wait()  # Wait for the callback to signal that the desired state is ready
    return desired_state_info if desired_state_info else None
