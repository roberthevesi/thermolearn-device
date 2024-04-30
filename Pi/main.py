import adafruit_dht
import board
import bluetooth
import time
from iot_shadow_client import get_shadow, shadow_client

# DHT22 SETTINGS
dht22_pin = board.D17
dht_device = adafruit_dht.DHT22(dht22_pin)

# BLUETOOTH SETTINGS
esp32_address = 'CC:DB:A7:68:55:C2'
port = 1  # Bluetooth uses port 1 for RFCOMM
sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
sock.connect((esp32_address, port))

# FUNCTION TO SEND BLUETOOTH MESSAGE
def send_bluetooth_message(message):
    try:

        sock.send(message + '!')
        print(f"-> Sent: <{message + '!'}>")

        received_data = ""

        while True:
            data = sock.recv(1024)
            if not data:
                print("no data...")
                break
            received_data += data.decode('utf-8').strip()
            print(f"<- Received: <{received_data}>")

            if received_data.endswith('!'):
                if message == 'stat_req':
                    return received_data[:-1]
                
                if "ACK_" + message + '!' == received_data:
                    return message[:-1]
                else:
                    return None
            else:
                continue

    except bluetooth.BluetoothError as e:
        print(f"Bluetooth Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


# FUNCTION TO GET THING SHADOW
def get_iot_core_thing_shadow():
    shadow_result = get_shadow()
    if shadow_result:
        return shadow_result
    else:
        print("Failed to retrieve shadow or shadow is empty.")

    shadow_client.disconnect()


def ping_shadow():
    shadow_result = get_iot_core_thing_shadow()
    return shadow_result
    # mode = shadow_result.get('mode')
    # desiredTemp = shadow_result.get('desiredTemp')


def get_environment_temp():
    max_tries = 10
    while max_tries:
        try:
            temp = dht_device.temperature
            if temp is not None:
                return temp
        except RuntimeError as e:
            print(f"@@@@@ An error occurred: {e}")
        finally:
            max_tries -= 1     
            time.sleep(1)  
                                                                  

if __name__ == "__main__":
    message = 'stat_req'
    status = None

    while status == None:
        status = send_bluetooth_message(message)
        time.sleep(1)


    while True:
        try:
            shadow_result = get_iot_core_thing_shadow()
            mode = shadow_result.get('mode')
            desiredTemp = shadow_result.get('desiredTemp')

            print(f"- Desired: {desiredTemp}")

            temp_celsius = get_environment_temp()

            if temp_celsius is not None:
                print(f"- Current temp: {temp_celsius:.1f}")

                if temp_celsius < desiredTemp:
                    if status == 'OFF':
                        status = 'ON'
                        while send_bluetooth_message(status) == None:
                            time.sleep(1)
                            continue
                else:
                    if status == 'ON':
                        status = 'OFF'
                        while send_bluetooth_message(status) == None:
                            time.sleep(1)
                            continue
            else:
                print("failed to read temp.")

        except RuntimeError as e:
            print(f"An error occurred: {e}")

        print('\n')
        time.sleep(2)

    sock.close()