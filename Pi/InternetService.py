import socket

def is_connected_to_internet():
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=5)
        return True
    except OSError:
        return False
    
is_connected_to_internet()