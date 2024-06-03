import re
import uuid
import requests
import os

thermostatId = None
ec2_url = os.getenv("EC2_INSTANCE_URL")

def get_mac_address():
    mac = ':'.join(re.findall('..', '%012x' % uuid.getnode()))
    return mac.upper()

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
    print("hello")
    try:
        mac_address = get_mac_address()
        print("MAC Address: ", mac_address)
        response = get_thermostat_details(mac_address)


        print("Response: ", response)

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