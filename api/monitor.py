from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def monitor():
    return jsonify({"status": "test_endpoint_working"})
