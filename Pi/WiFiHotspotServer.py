# server.py
from flask import Flask, request, jsonify
from threading import Thread, Event

app = Flask(__name__)
credentials = {}
shutdown_event = Event()

@app.route('/receive_credentials', methods=['GET'])
def receive_credentials():
    ssid = request.args.get('ssid')
    password = request.args.get('password')
    fingerprint = request.args.get('fingerprint')

    if not ssid or not password:
        return jsonify({"status": "error", "message": "Missing ssid or password or fingerprint"}), 400

    credentials['ssid'] = ssid
    credentials['password'] = password
    credentials['fingerprint'] = fingerprint

    print(f"Received SSID: {ssid}")
    print(f"Received Password: {password}")
    print(f"Received Fingerprint: {fingerprint}")


    return jsonify({"status": "success", "message": "Credentials received"})

@app.route('/shutdown', methods=['POST'])
def shutdown():
    shutdown_event.set()
    return 'Server shutting down...'

def run_server():
    app.run(host='0.0.0.0', port=5000) 

def start_server():
    server_thread = Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()
    return server_thread

def wait_for_shutdown():
    shutdown_event.wait()

