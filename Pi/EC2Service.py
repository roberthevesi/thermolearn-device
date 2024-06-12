import re
import uuid
import requests
import os
from datetime import datetime
# from WiFiHotspotService import load_fingerprint
import WiFiHotspotService

thermostatId = None
ec2_url = os.getenv("EC2_INSTANCE_URL")


def get_mac_address():
    mac = ':'.join(re.findall('..', '%012x' % uuid.getnode()))
    return mac.upper()


def set_thermostat_fingerprint():
    try:
        fingerprint = WiFiHotspotService.load_fingerprint()
        print("FINGERPRINT: ", fingerprint)

        mac_address = get_mac_address()
        # print("MAC Address: ", mac_address)
        response = get_thermostat_details(mac_address)

        if response.get('isPaired') == False:
            thermostatId = response.get('id')

            print("THERMOSTAT ID: ", thermostatId)

            url = ec2_url + "/api/v1/thermostat/set-thermostat-fingerprint"
            params = {
                'thermostatId': thermostatId,
                'fingerprint': fingerprint
            }
            response = requests.post(url, params=params)
            
            if response.status_code == 200:
                print("Thermostat fingerprint set successfully")
            else:
                response.raise_for_status()
    
    except Exception as e:
        print(f"An error occurred: {e}")


def get_thermostat_details(mac_address):
    url = ec2_url + "/api/v1/thermostat/get-thermostat-by-mac-address"
    params = {'macAddress': mac_address}
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        return response.json()
    else:
        response.raise_for_status()


def is_thermostat_paired():
    global thermostatId
    try:
        mac_address = get_mac_address()
        print("MAC Address: ", mac_address)
        response = get_thermostat_details(mac_address)

        if response.get('isPaired') == True:
            thermostatId = response.get('id')
            return response
        
        if response.get('isPaired') == False:
            return False

        # return response.get('isPaired')
    
    except Exception as e:
        print(f"An error occurred: {e}")


def get_thermostat_id():
    try:
        mac_address = get_mac_address()
        response = get_thermostat_details(mac_address)
        return response.get('id')
    
    except Exception as e:
        print(f"An error occurred: {e}")


def get_thermostat_schedule():
    try:
        url = ec2_url + "/api/v1/thermostat/get-schedule-by-thermostat-id"
        params = {'thermostatId': thermostatId}
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            return response.json()
        else:
            response.raise_for_status()
    
    except Exception as e:
        print(f"An error occurred: {e}")


def save_thermostat_status_log(status, temperature, humidity):
    try:
        url = ec2_url + "/api/v1/thermostat-log/save-log"
        data = {
            'thermostatId': thermostatId,
            'status': status,
            'temperature': temperature,
            'humidity': humidity,
            'timestamp': datetime.now().isoformat()
        }
        response = requests.post(url, json=data)
        
        if response.status_code == 200:
            print("Thermostat status log saved successfully, with status:", status)
        else:
            response.raise_for_status()
    
    except Exception as e:
        print(f"An error occurred: {e}")


def get_lastest_user_log():
    try:
        url = ec2_url + "/api/v1/log/get-latest-user-log-by-thermostat-id"
        params = {
            'thermostatId': thermostatId
        }
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            return response.json()
        else:
            response.raise_for_status()
    
    except Exception as e:
        print(f"An error occurred: {e}")


def get_user_distance_from_home():
    try:
        url = ec2_url + "/api/v1/user/get-user-distance-from-home"
        params = {
            'thermostatId': thermostatId
        }
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            return response.json()
        else:
            response.raise_for_status()
    
    except Exception as e:
        print(f"An error occurred: {e}")