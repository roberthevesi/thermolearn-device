from EC2Service import is_thermostat_paired
from InternetService import is_connected_to_internet
import IoTCoreService  # Import IoTCoreService to utilize its functionality
import time

thermostatId = None

if __name__ == "__main__":
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

    # Check if thermostat is paired
    print("--- Checking if thermostat is paired...")
    while True:
        response = is_thermostat_paired()

        if response:
            print("Thermostat is paired")
            thermostatId = response.get('id')
            break
        else:
            print("Thermostat is not paired")

        time.sleep(10)

    IoTCoreService.thermostatId = thermostatId 
    IoTCoreService.start_mqtt_thread()
    
    # Main loop 
    while True:
        if IoTCoreService.latest_message:
            print(f"Latest message received: {IoTCoreService.latest_message}")
        time.sleep(5)

    print("Bye!")
