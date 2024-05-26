# script.py

from EC2Service import is_thermostat_paired, get_thermostat_schedule
from InternetService import is_connected_to_internet
import IoTCoreService  # Import IoTCoreService to utilize its functionality
import time
import json


thermostatId = None
weekly_schedule = {
    'MONDAY': [],
    'TUESDAY': [],
    'WEDNESDAY': [],
    'THURSDAY': [],
    'FRIDAY': [],
    'SATURDAY': [],
    'SUNDAY': []
}


def check_internet():
    # Check if thermostat is connected to the internet
    print("--- Checking if thermostat is connected to the internet...")
    while True:
        connected = is_connected_to_internet()

        if connected:
            print("Thermostat is connected to the internet")
            break
        else:
            print("Thermostat is not connected to the internet")

        time.sleep(10)


def check_thermostat():
    # Check if thermostat is paired
    print("--- Checking if thermostat is paired...")
    while True:
        response = is_thermostat_paired()

        if response:
            print("Thermostat is paired")
            thermostatId = response.get('id')
            IoTCoreService.thermostatId = thermostatId 
            break
        else:
            print("Thermostat is not paired")

        time.sleep(10)


def populate_schedule(response):
    global weekly_schedule

    for entry in response:
        day = entry['day']
        if day in weekly_schedule:
            weekly_schedule[day].append({
                'startTime': entry['startTime'],
                'desiredTemperature': entry['desiredTemperature']
            })


def reset_schedule():
    global weekly_schedule
    for day in weekly_schedule:
        weekly_schedule[day] = []


def on_temperature_request(message):
    print("Action: Processing temperature request", message)


def fetch_schedule():
    response = get_thermostat_schedule()

    reset_schedule()
    populate_schedule(response)
    for day, entries in weekly_schedule.items():
        print(f"{day}: {entries}")


def on_updated_schedule_request(message):
    print("Action: Processing updated schedule request", message)
    fetch_schedule()
    # print(type(message))    


if __name__ == "__main__":
    check_internet()
    
    check_thermostat()

    IoTCoreService.start_mqtt_thread()

    IoTCoreService.register_callback("temperatureRequests", on_temperature_request)
    IoTCoreService.register_callback("updatedScheduleRequests", on_updated_schedule_request)
    
    # Main loop 
    while True:
        # if IoTCoreService.latest_messages:
        #     print("Latest temperature requests message:", IoTCoreService.get_latest_message("temperatureRequests"))
        #     print("Latest updated schedule requests message:", IoTCoreService.get_latest_message("updatedScheduleRequests"))
 
        time.sleep(5)

    print("Bye!")
