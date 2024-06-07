import pandas as pd
import requests
from sklearn.linear_model import SGDClassifier
from sklearn.preprocessing import StandardScaler, OneHotEncoder
import pickle
from datetime import datetime, timedelta
import os
from threading import Timer
from EC2Service import is_thermostat_paired

ec2_url = os.getenv("EC2_INSTANCE_URL")
thermostatId = None
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

def preprocess_data(df, encoder, original_columns):
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['Hour'] = df['timestamp'].dt.hour
    df['Day_of_Week'] = df['timestamp'].dt.dayofweek
    features = df[['Hour', 'Day_of_Week']]
    
    # One-hot encode the Day_of_Week column
    encoded_days = encoder.transform(features[['Day_of_Week']])
    encoded_days_df = pd.DataFrame(encoded_days, columns=encoder.get_feature_names_out(['Day_of_Week']))
    features = pd.concat([features.drop('Day_of_Week', axis=1), encoded_days_df], axis=1)
    
    # Ensure the new data has the same columns as the original training data
    for col in original_columns:
        if col not in features.columns:
            features[col] = 0

    features = features[original_columns]  # Ensure the columns are in the correct order

    target = df['eventType'].map({'IN': 1, 'OUT': 0})
    return features, target

def update_model(df, model, scaler, encoder, original_columns):
    features, target = preprocess_data(df, encoder, original_columns)
    features_scaled = scaler.transform(features)
    model.partial_fit(features_scaled, target, classes=[0, 1])

    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    with open(scaler_path, 'wb') as f:
        pickle.dump(scaler, f)
    with open(encoder_path, 'wb') as f:
        pickle.dump(encoder, f)

    print("Model, scaler, and encoder updated and saved.")

def update_model_periodically(original_columns):
    print("Updating model with new logs...")
    response = is_thermostat_paired()
    if response:
        thermostatId = response.get('id')
        df = fetch_logs(thermostatId)
        model, scaler, encoder = load_model()
        update_model(df, model, scaler, encoder, original_columns)
    else:
        print("Thermostat is not paired")

    # Schedule the next update
    Timer(3600, update_model_periodically, [original_columns]).start()  # Update model every hour

if __name__ == "__main__":
    # Assuming the initial columns used during training are known
    original_columns = [
        'Hour',
        'Day_of_Week_0', 'Day_of_Week_1', 'Day_of_Week_2',
        'Day_of_Week_3', 'Day_of_Week_4', 'Day_of_Week_5', 'Day_of_Week_6'
    ]

    update_model_periodically(original_columns)
