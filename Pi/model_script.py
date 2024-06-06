import pandas as pd
import requests
from sklearn.ensemble import RandomForestClassifier
import pickle
from datetime import datetime
import os
from EC2Service import is_thermostat_paired

ec2_url = os.getenv("EC2_INSTANCE_URL")
thermostatId = None

def fetch_logs(thermostatId):
    url = ec2_url + '/api/v1/log/get-user-logs-by-thermostat-id'
    params = {'thermostatId': thermostatId}
    response = requests.get(url, params=params)
    print("Response: ", response.json())
    data = response.json()
    df = pd.DataFrame(data)
    return df

def train_model(df):
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['hour'] = df['timestamp'].dt.hour
    df['day_of_week'] = df['timestamp'].dt.dayofweek
    features = df[['hour', 'day_of_week']]
    target = df['eventType'].map({'IN': 1, 'OUT': 0}) 
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(features, target)
    with open('../../thermolearn-model/user_activity_model.pkl', 'wb') as f:
        pickle.dump(model, f)
    return model

def predict_activity(model, current_time):
    current_hour = current_time.hour
    current_day = current_time.weekday()
    features = pd.DataFrame([[current_hour, current_day]], columns=['hour', 'day_of_week'])
    prediction = model.predict(features)
    return 'IN' if prediction[0] == 1 else 'OUT' 

if __name__ == "__main__":
    response = is_thermostat_paired()
    if response:
        thermostatId = response.get('id')
        df = fetch_logs(thermostatId)
        model = train_model(df)
        current_time = datetime.now()
        activity = predict_activity(model, current_time)
        print(f'Predicted user activity: {activity}')

    else:
        print("Thermostat is not paired")
        exit()
