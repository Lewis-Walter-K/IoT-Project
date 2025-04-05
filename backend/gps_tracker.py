import socket
import math
import time

# Constants
CALORIES_PER_METER_WALK = 0.04
CALORIES_PER_METER_RUN = 0.08
SPEED_THRESHOLD = 2  # m/s
PORT = 11123
MOVEMENT_THRESHOLD = 3

# Global variables
total_calories = 0
total_distance = 0
connection_status = False

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c * 1000  # meters

def parse_nmea_gprmc(nmea_sentence):
    parts = nmea_sentence.split(",")
    if parts[0] != "$GPRMC":
        return None, None, None

    lat_raw = parts[3]
    lat_dir = parts[4]
    lon_raw = parts[5]
    lon_dir = parts[6]
    speed_knots = parts[7]

    if not lat_raw or not lon_raw:
        return None, None, None

    lat_deg = int(float(lat_raw) / 100)
    lat_min = float(lat_raw) % 100 / 60
    latitude = lat_deg + lat_min
    if lat_dir == 'S':
        latitude = -latitude

    lon_deg = int(float(lon_raw) / 100)
    lon_min = float(lon_raw) % 100 / 60
    longitude = lon_deg + lon_min
    if lon_dir == 'W':
        longitude = -longitude

    speed_mps = float(speed_knots) * 0.51444 if speed_knots else 0

    return latitude, longitude, speed_mps

def start_gps_tracking(iphone_ip):
    global total_calories, total_distance, connection_status
    # total_calories = 0
    total_distance = 0
    connection_status = False
    previous_lat, previous_lon = None, None

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect((iphone_ip, PORT))
        connection_status = True
        print("Connected to GPS2IP at {iphone_ip}:{PORT}")
    except Exception as e:
        print(f"Connection error: {e}")
        connection_status = False
        return
    
    while True:
        try:
            data = client_socket.recv(1024)
            if not data:
                print("Connection lost. Reconnecting...")
                connection_status = False
                client_socket.connect((iphone_ip, PORT))
                connection_status = True
                continue

            connection_status = True
            gps_data = data.decode("utf-8").strip()
            print("Received GPS Data:", gps_data)

            latitude, longitude, speed_mps = parse_nmea_gprmc(gps_data)

            if latitude is not None and longitude is not None:
                if previous_lat is not None and previous_lon is not None:
                    distance = haversine(previous_lat, previous_lon, latitude, longitude)

                    print(f"Previous: ({previous_lat}, {previous_lon})")  # Debugging print
                    print(f"Current: ({latitude}, {longitude})")  # Debugging print
                    print(f"Calculated Distance: {distance:.2f} meters")  # Debugging print

                    if distance > MOVEMENT_THRESHOLD:
                        total_distance += distance # Update total distance

                        #Determine calories based on walking or running
                        if speed_mps < SPEED_THRESHOLD:
                            calories_burned = distance * CALORIES_PER_METER_WALK
                        else:
                            calories_burned = distance * CALORIES_PER_METER_RUN
                        total_calories += calories_burned

                previous_lat, previous_lon = latitude, longitude

                print(f"Total Distance: {total_distance:.2f} meters")
                print(f"Total Calories Burned: {total_calories:.2f} kcal\n")
                get_calories()
                is_connected()
            else:
                print("Invalid GPS data received.")

            time.sleep(5)

        except Exception as e:
            print(f"Error: {e}")
            connection_status = False
            break
    client_socket.close()

def get_calories():
    global total_calories
    return total_calories

def is_connected():
    return connection_status
