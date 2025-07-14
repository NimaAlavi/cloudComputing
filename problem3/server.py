from flask import Flask, jsonify, request

app = Flask(__name__)

current_status = "OK"

@app.route('/api/v1/status', methods=['GET', 'POST'])
def status():
    global current_status
    if request.method == 'GET':
        return jsonify({"status": current_status}), 200
    elif request.method == 'POST':
        data = request.get_json()
        if data is None:
            return jsonify({"error": "Invalid JSON"}), 400
        if 'status' not in data:
            return jsonify({"error": "Missing 'status' key"}), 400
        current_status = data['status']
        return jsonify(data), 201

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)