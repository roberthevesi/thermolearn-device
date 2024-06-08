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

    if not ssid or not password:
        return jsonify({"status": "error", "message": "Missing ssid or password"}), 400

    credentials['ssid'] = ssid
    credentials['password'] = password

    print(f"Received SSID: {ssid}")
    print(f"Received Password: {password}")

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

