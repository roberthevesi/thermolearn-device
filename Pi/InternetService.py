import socket
import requests
from datetime import datetime
from dateutil.parser import isoparse

def is_connected_to_internet():
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=5)
        return True
    except OSError:
        return False


def get_ip_and_location():
    response = requests.get('https://ipinfo.io/json')
    data = response.json()
    return data['timezone']


def get_current_day_and_time():
    timezone = get_ip_and_location()

    response = requests.get(f'https://worldtimeapi.org/api/timezone/{timezone}')
    data = response.json()
    datetime_str = data['datetime']

    current_datetime = isoparse(datetime_str)
    
    day_of_week = current_datetime.strftime('%A').upper()
    current_time = current_datetime.strftime('%H:%M:%S')
    current_date = current_datetime.strftime('%Y-%m-%d')

    return day_of_week, current_time, current_date, timezone