import bluetooth
import time

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

# def send_message(message):
#     while send_bluetooth_message(message) == None:
#         time.sleep(1)
#         continue

def turn_on_thermostat():
    while send_bluetooth_message('ON') == None:
        time.sleep(1)
        continue

def turn_off_thermostat():
    while send_bluetooth_message('OFF') == None:
        time.sleep(1)
        continue

def get_thermostat_status():
    status = None

    while status == None:
        status = send_bluetooth_message('stat_req')
        time.sleep(1)
    
    return status