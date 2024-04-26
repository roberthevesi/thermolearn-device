import bluetooth

esp32_address = 'CC:DB:A7:68:55:C2'
port = 1  # Bluetooth uses port 1 for RFCOMM
sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
sock.connect((esp32_address, port))

def send_message(message):
    sock.send(message)
    print("Sent: {}".format(message))
    response = sock.recv(1024)
    print("Received: {}".format(response.decode('utf-8')))

# send_message('ON')
send_message('OFF xxx')

sock.close()