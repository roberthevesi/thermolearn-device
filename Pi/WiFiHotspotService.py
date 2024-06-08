import subprocess
import os
import time
import requests
import json
from WiFiHotspotServer import start_server, credentials, wait_for_shutdown, shutdown_event

CONFIG_FILE = 'wifi_credentials.json'

def start_hotspot():
    try:
        subprocess.run(['sudo', 'systemctl', 'start', 'start_wifi_hotspot.service'], check=True)
        print("Hotspot service started successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to start hotspot service: {e}")


def stop_hotspot():
    try:
        subprocess.run(['sudo', 'systemctl', 'start', 'stop_wifi_hotspot.service'], check=True)
        print("Hotspot service stopped successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to stop hotspot service: {e}")


def save_credentials(ssid, password):
    with open(CONFIG_FILE, 'w') as f:
        json.dump({'ssid': ssid, 'password': password}, f)


def load_credentials():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            creds = json.load(f)
            return creds.get('ssid'), creds.get('password')
    return None, None


def connect_to_wifi(ssid, password):
    try:
        result = subprocess.run(['nmcli', 'dev', 'wifi', 'connect', ssid, 'password', password], capture_output=True, text=True)
        if 'successfully activated' in result.stdout:
            print(f"Connected to WiFi network: {ssid}")
            return True
        else:
            print(f"Failed to connect to WiFi network: {ssid}")
            print(result.stdout)
            return False
    except Exception as e:
        print(f"Error occurred while connecting to WiFi: {e}")
        return False


def start_wifi_process():
    ssid, password = load_credentials()

    if ssid and password:
        print(f"Found credentials in configuration file. Attempting to connect to WiFi: SSID={ssid}")
        if connect_to_wifi(ssid, password):
            print("Successfully connected to WiFi.")
            return
        else:
            print("Failed to connect with provided credentials. Starting server to get new credentials.")

    start_hotspot()

    start_server()
    print("Server started")

    while True:
        if credentials:
            ssid = credentials.get('ssid')
            password = credentials.get('password')
            if ssid and password:
                print(f"Attempting to connect to WiFi: SSID={ssid}")
                stop_hotspot()
                if connect_to_wifi(ssid, password):
                    print("Successfully connected to WiFi.")
                    save_credentials(ssid, password)
                    break
                else:
                    print("Failed to connect. Restarting hotspot to wait for new credentials...")
                    start_hotspot()
                    credentials.clear()

        time.sleep(5)

    print("Stopping the server.")
    requests.post('http://127.0.0.1:5000/shutdown')
    wait_for_shutdown()