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
    sock.send(message)
    print(f"Sent: {message}")
    response = sock.recv(1024)
    received = response.decode('utf-8')
    print(f"Received: {received}")

    if "ACK_"+message == received:
        return True
    return False

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

# FUNCTION TO GET LAST HEATING STATUS
def get_status():
    message = 'stat_req'

    sock.send(message)
    print(f"Sent: {message}")

    response = sock.recv(1024)
    received = response.decode('utf-8')
    print(f"Received: {received}")

    return received

if __name__ == "__main__":
    last_status = get_status()

    while True:
        try:
            shadow_result = get_iot_core_thing_shadow()
            mode = shadow_result.get('mode')
            desiredTemp = shadow_result.get('desiredTemp')
            print(f"Desired: {desiredTemp}")

            temp_celsius = dht_device.temperature
            if temp_celsius is not None:
                print(f"Current temp: {temp_celsius:.1f}")

                if temp_celsius < desiredTemp:
                    if last_status == 'OFF':
                        last_status = 'ON'
                        while send_bluetooth_message(last_status) == False:
                            time.sleep(1)
                            continue
                else:
                    if last_status == 'ON':
                        last_status = 'OFF'
                        while send_bluetooth_message(last_status) == False:
                            time.sleep(1)
                            continue
            else:
                print("failed to read temp.")

        

        except RuntimeError as e:
            print(f"An error occurred: {e}")

        time.sleep(2)

    sock.close()