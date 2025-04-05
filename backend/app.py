from flask import Flask, request, jsonify
from flask_cors import CORS
from auth import auth
from gps_tracker import start_gps_tracking, get_calories, is_connected
from threading import Thread

app = Flask(__name__)

# Enable CORS for all routes and methods globally to prevent CORS errors
CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}})
# CORS(app, origins=["http://localhost:3000"])

# Register authentication routes from auth.py
app.register_blueprint(auth, url_prefix="/auth")

# Dictionary to store user-specific iPhone IP addresses
user_ips = {}

@app.route("/register_ip", methods=["POST", "OPTIONS"])  
def register_ip():
    """
    Endpoint to register a user's iPhone IP address.
    Handles both POST and CORS preflight OPTIONS requests.
    """
    # Handle preflight OPTIONS request (necessary for CORS in the frontend)
    if request.method == "OPTIONS": 
        response = jsonify({"message": "CORS Preflight Passed"})
        response.headers.add("Access-Control-Allow-Origin", "http://localhost:3000")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type")
        response.headers.add("Access-Control-Allow-Methods", "POST, OPTIONS")
        return response

    # Handle actual POST request to register the iPhone IP
    data = request.json
    print("📩 Received Data:", data)  # Debugging log

    email = data.get("email")
    iphone_ip = data.get("iphone_ip")

    if not email:
        return jsonify({"error": "Missing email"}), 400
    if not iphone_ip:
        return jsonify({"error": "Missing iPhone IP"}), 400

    user_ips[email] = iphone_ip
    try:
        print(f"🚀 Starting GPS tracking for {iphone_ip}")
        # start_gps_tracking(iphone_ip)
        tracking_thread = Thread(target=start_gps_tracking, args=(iphone_ip,))
        tracking_thread.daemon = True  # This makes sure the thread stops when Flask stops
        tracking_thread.start()
        
        print("✅ GPS Tracking Started")
    except Exception as e:
        print(f"❌ Error Starting GPS Tracking: {e}")
        return jsonify({"error": "Failed to start GPS tracking"}), 500
    return jsonify({"message": "GPS tracking started"}), 200


@app.route("/get_calories", methods=["GET"])
def get_total_calories():
    calories = get_calories()
    """
    Endpoint to get the total calories burned.
    """
    return jsonify({"calories": calories}), 200

@app.route("/check-connection", methods=["GET"])
def check_connection():
    status = "Connected" if is_connected() else "Not Connected"
    return jsonify({"status": status})

if __name__ == "__main__":
    # Start the Flask app with debugging enabled
    app.run(debug=True)
