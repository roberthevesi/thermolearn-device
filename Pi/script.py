# script.py

from EC2Service import is_thermostat_paired, get_thermostat_schedule
from InternetService import is_connected_to_internet, get_current_day_and_time
import IoTCoreService
import time
from datetime import datetime, timedelta
import json
import threading
import adafruit_dht
import board

# DHT22 SETTINGS
dht22_pin = board.D17
dht_device = adafruit_dht.DHT22(dht22_pin)

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
days_of_week = ['MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY', 'SATURDAY', 'SUNDAY']


class ThermostatStateMachine:
    def __init__(self):
        self.state = 'Init'

        self.targetTemp = 0
        self.environmentTemp = 0

        self.current_day_of_week = None
        self.current_time = None
        
        self.current_day_index = None
        self.current_datetime = None
        self.current_date = None

        self.instant_request_desiredTemp = None
        self.instant_request_timestamp = None

        self.init_finished = False

    def transition(self, new_state):
        print(f"<<< Transitioning from {self.state} to {new_state} >>>")
        self.state = new_state
        self.run_state()

    def run_state(self):
        if self.state == 'Init':
            self.check_internet()
            self.check_thermostat()
            self.get_current_time_day()
            self.start_clock_thread()
            self.start_listening()
            # self.init_finished = True
        elif self.state == 'ComparingRequests':
            self.compare_requests()
        elif self.state == 'ReadingEnvironmentTemperature':
            self.read_environment_temperature()
        elif self.state == 'SettingTargetTemperature':
            self.set_target_temperature()
        elif self.state == 'ListeningForNewEvents':
            self.listen_for_events()
        else:
            print(f"Unknown state: {self.state}")

    ######################## 0 - INIT STATE ########################

    def check_internet(self):
        print("\n--- Checking if thermostat is connected to the internet ---")
        while True:
            connected = is_connected_to_internet()
            if connected:
                print("Thermostat is connected to the internet")
                # self.transition('FetchingSchedule')
                break
            else:
                print("Thermostat is not connected to the internet")
            time.sleep(10)

    def check_thermostat(self):
        global thermostatId
        print("\n--- Checking if thermostat is paired ---")
        while True:
            response = is_thermostat_paired()
            if response:
                print("Thermostat is paired")
                thermostatId = response.get('id')
                IoTCoreService.thermostatId = thermostatId
                # self.transition('FetchingTimeDay')
                break
            else:
                print("Thermostat is not paired")
            time.sleep(10)

    
    def get_current_time_day(self):
        print("\n--- Fetching current time and day ---")
        self.current_day_of_week, self.current_time, self.current_date = get_current_day_and_time()
        self.current_day_index = days_of_week.index(self.current_day_of_week)
        self.current_datetime = datetime.strptime(self.current_time, '%H:%M:%S')

    def start_clock(self):
        while True:
            self.current_time = self.current_datetime.time()
            time.sleep(1)
            self.current_datetime += timedelta(seconds=1)

            if self.current_datetime.hour == 0 and self.current_datetime.minute == 0 and self.current_datetime.second == 0:
                self.current_day_index = (self.current_day_index + 1) % 7

    def start_clock_thread(self):
        clock_thread = threading.Thread(target=self.start_clock)
        clock_thread.daemon = True
        clock_thread.start()

    def start_listening(self):
        print("\n--- Starting listening ---")
        IoTCoreService.start_mqtt_thread()
        IoTCoreService.register_callback("temperatureRequests", self.on_temperature_request)
        IoTCoreService.register_callback("updatedScheduleRequests", self.on_updated_schedule_request)

        time.sleep(2)
        self.init_finished = True
        self.transition('ComparingRequests')


    def on_temperature_request(self, message):
        print("Action: Processing temperature request", message)
        self.instant_request_desiredTemp = message.get('desiredTemp')
        self.instant_request_timestamp = message.get('timestamp')

        if self.init_finished is not False:
            self.transition('ComparingRequests')
        # self.transition('ListeningForNewEvents')
        

    def on_updated_schedule_request(self, message):
        print("Action: Processing updated schedule request", message)
        self.fetch_schedule()

        if self.init_finished is not False:
            self.transition('ComparingRequests')

    def fetch_schedule(self):
        print("--- Fetching thermostat schedule...")
        response = get_thermostat_schedule()
        self.reset_schedule()
        self.populate_schedule(response)
        for day, entries in weekly_schedule.items():
            print(f"{day}: {entries}")

    def reset_schedule(self):
        global weekly_schedule
        for day in weekly_schedule:
            weekly_schedule[day] = []

    def populate_schedule(self, response):
        global weekly_schedule
        for entry in response:
            day = entry['day']
            if day in weekly_schedule:
                weekly_schedule[day].append({
                    'startTime': entry['startTime'],
                    'desiredTemperature': entry['desiredTemperature']
                })

    ######################## 1 - ComparingRequests STATE ########################

    def compare_requests(self):
        # if self.init_finished is not False: 
        #     return
        
        print("\n--- Comparing manual request with scheduled events ---")

        # if self.instant_request_timestamp 

        last_scheduled_event = self.get_last_scheduled_event()
        print("last_scheduled_event: ", last_scheduled_event)
        is_within_one_week = self.is_request_within_one_week(self.instant_request_timestamp)

        if not is_within_one_week:
            print("Instant request is not within one week")

            if last_scheduled_event:
                self.targetTemp = last_scheduled_event['desiredTemperature']
                print(f"Setting target temperature to {self.targetTemp}")

            self.transition('ReadingEnvironmentTemperature')
        elif is_within_one_week:
            print("Instant request is within one week")
            print("comparing...")
            print("last_scheduled_event.startTime: ", last_scheduled_event['startTime'])
            print("last_scheduled_event.day_of_the_week: ", last_scheduled_event['day_of_the_week'])
            print("last_scheduled_event.desiredTemperature: ", last_scheduled_event['desiredTemperature'])
            print("with...")
            print("instant_request_timestamp: ", self.instant_request_timestamp)
            print("instant_request_desiredTemp: ", self.instant_request_desiredTemp)

            ret_val = self.more_recent_event(last_scheduled_event['startTime'], last_scheduled_event['day_of_the_week'])

            if ret_val == 0:
                print("Instant request is more recent")
                self.targetTemp = self.instant_request_desiredTemp
                print(f"Setting target temperature to {self.targetTemp}")

            elif ret_val == 1:
                print("Last scheduled event is more recent")
                self.targetTemp = last_scheduled_event['desiredTemperature']
                print(f"Setting target temperature to {self.targetTemp}")
                
            self.transition('ReadingEnvironmentTemperature')

    def sort_weekly_schedule_descending(self):
        for day, events in weekly_schedule.items():
            events.sort(key=lambda x: x['startTime'], reverse=True)
        return weekly_schedule

    def get_last_scheduled_event(self):
        self.sort_weekly_schedule_descending()
        most_recent_event = None
        
        for day_offset in range(7):
            day_index = (self.current_day_index - day_offset) % 7
            day_name = days_of_week[day_index]
            for event in weekly_schedule[day_name]:
                event_time = datetime.strptime(event.get('startTime'), '%H:%M:%S').time()
                if event_time <= self.current_time:
                    most_recent_event = event
                    most_recent_event['day_of_the_week'] = day_name

                    print("most recent event found, ", most_recent_event)

                    return most_recent_event

        return most_recent_event


    def is_request_within_one_week(self, instant_request_timestamp):
        instant_request_dt = datetime.strptime(instant_request_timestamp, '%Y-%m-%d %H:%M:%S')
        
        current_dt = datetime.strptime(f"{self.current_date} {self.current_time}", '%Y-%m-%d %H:%M:%S')
        time_difference = current_dt - instant_request_dt
    
        return time_difference <= timedelta(days=7)
    
    
    def more_recent_event(self, last_scheduled_event_start_time, last_scheduled_event_day_of_the_week):
        instant_request_dt = datetime.strptime(self.instant_request_timestamp, '%Y-%m-%d %H:%M:%S')
        
        current_dt = datetime.strptime(f"{self.current_date} {self.current_time}", '%Y-%m-%d %H:%M:%S')
    
        current_day_index = datetime.strptime(self.current_date, '%Y-%m-%d').weekday()
        event_day_index = days_of_week.index(last_scheduled_event_day_of_the_week)
        
        days_diff = (current_day_index - event_day_index) % 7
        if days_diff == 0 and instant_request_dt.date() == datetime.strptime(self.current_date, '%Y-%m-%d').date():
            last_scheduled_event_date = datetime.strptime(self.current_date, '%Y-%m-%d')
        else:
            last_scheduled_event_date = datetime.strptime(self.current_date, '%Y-%m-%d') - timedelta(days=days_diff)
        
        last_scheduled_event_dt = datetime.strptime(f"{last_scheduled_event_date.strftime('%Y-%m-%d')} {last_scheduled_event_start_time}", '%Y-%m-%d %H:%M:%S')
        
        if instant_request_dt > last_scheduled_event_dt:
            return 0
        elif instant_request_dt <= last_scheduled_event_dt:
            return 1
        else:
            return -1
    
    ######################## 2 - ReadingEnvironmentTemperature STATE ########################

    def read_environment_temperature(self):
        print(f"\n --- Reading environment temperature ---") 

        max_tries = 15
        while max_tries:
            try:
                temp = dht_device.temperature
                if temp is not None:
                    self.environmentTemp = temp
                    print(f"Current temperature: {self.environmentTemp:.1f}")
                    break
            except RuntimeError as e:
                print(f"An error occurred: {e}")
            finally:
                max_tries -= 1     
                time.sleep(1)    

        self.transition('SettingTargetTemperature')


    ######################## 3 - SettingTargetTemperature STATE ########################

    def set_target_temperature(self):
        print(f"\n --- Setting target temperature ---")
        # Implement the logic to set the thermostat's temperature

        print(f"Current temperature: {self.environmentTemp:.1f}")
        print(f"Target temperature: {self.targetTemp}")

        if self.environmentTemp < self.targetTemp:
            print(f"Setting thermostat to ON")
        elif self.environmentTemp >= self.targetTemp:
            print(f"Setting thermostat to OFF")

        self.transition('ListeningForNewEvents')


    ######################## 4 - ListeningForNewEvents STATE #######################

    def listen_for_events(self):    
        print("\n--- Listening for new events ---")
        # Implement the logic to listen for new events


if __name__ == "__main__":
    thermostat = ThermostatStateMachine()
    thermostat.run_state()

    while True:
        time.sleep(5)
    print("Bye!")
