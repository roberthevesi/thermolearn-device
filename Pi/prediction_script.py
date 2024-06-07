import pandas as pd
import requests
from sklearn.linear_model import SGDClassifier
from sklearn.preprocessing import StandardScaler, OneHotEncoder
import pickle
from datetime import datetime, timedelta
import os
from EC2Service import is_thermostat_paired

ec2_url = os.getenv("EC2_INSTANCE_URL")
model_path = '../../thermolearn-model/user_activity_model.pkl'
scaler_path = '../../thermolearn-model/scaler.pkl'
encoder_path = '../../thermolearn-model/encoder.pkl'

def fetch_logs(thermostatId):
    url = ec2_url + '/api/v1/log/get-user-logs-by-thermostat-id'
    params = {'thermostatId': thermostatId}
    response = requests.get(url, params=params)
    data = response.json()
    df = pd.DataFrame(data)
    return df

def load_model():
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    with open(scaler_path, 'rb') as f:
        scaler = pickle.load(f)
    with open(encoder_path, 'rb') as f:
        encoder = pickle.load(f)
    return model, scaler, encoder

def preprocess_data(current_time, encoder):
    hour = current_time.hour
    day_of_week = current_time.weekday()
    data = pd.DataFrame([[hour, day_of_week]], columns=['Hour', 'Day_of_Week'])
    
    encoded_days = encoder.transform(data[['Day_of_Week']])
    encoded_days_df = pd.DataFrame(encoded_days, columns=encoder.get_feature_names_out(['Day_of_Week']))
    data = pd.concat([data.drop('Day_of_Week', axis=1), encoded_days_df], axis=1)
    
    return data

def predict_next_home_time():
    response = is_thermostat_paired()
    if response:
        thermostatId = response.get('id')
        current_time = datetime.now()
        model, scaler, encoder = load_model()

        for i in range(1, 1440): # next 24h (1440 min)
            future_time = current_time + timedelta(minutes=i)
            features = preprocess_data(future_time, encoder)
            features_scaled = scaler.transform(features)
            prediction = model.predict(features_scaled)
            if prediction[0] == 1:
                print(f'The user is predicted to be home at {future_time.strftime("%Y-%m-%d %H:%M:%S")}')
                return future_time

        print("No home prediction within the next 24 hours.")
    else:
        print("Thermostat is not paired")

if __name__ == "__main__":
    predict_next_home_time()
