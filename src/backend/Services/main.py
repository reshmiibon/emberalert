import sys
import os
fpath = os.path.abspath(os.path.join(
    os.path.dirname(__file__),
    os.pardir
))
sys.path.append(fpath)
from flask import Flask, redirect, url_for, jsonify, request
from Services import Notification 
from flask_cors import CORS, cross_origin
from DataManager import open_connection, execute_read_stored_procedure

app = Flask(__name__)
CORS(app)

users = []

@app.route("/map/get-fires")
def get_fires():
    try:
        fires = execute_read_stored_procedure("find_fires", [])

        # Format the result as a list of dictionaries
        fire_data = []
        for sublist in fires:
            for fire in sublist:
                fire_dict = {'id': fire[0], 'lat': fire[1], 'lng': fire[2]}
                fire_data.append(fire_dict)

        # Return the fire data as JSON
        return jsonify(fire_data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route("/map/get-fire-mask/<fire_id>")
def get_fire_mask(fire_id):

    print("Received request for fire mask with fire_id:", fire_id)
    
    try:
        # Convert fire_id to integer
        fire_id = int(fire_id)

        mask_details = execute_read_stored_procedure("get_fire_mask_data", [fire_id])
        
        # Initialize a dictionary to store data based on fire_mask number
        response_data = {}

        # Grouping data based on fire_mask number
        for sublist in mask_details:
            for mask_id, point_id, latitude, longitude, fire_status in sublist:
                # Check if mask_id exists in response_data, if not, add it
                if mask_id not in response_data:
                    response_data[mask_id] = {'mask_id': mask_id, 'points': []}
                
                # Append the point data to the corresponding mask_id
                response_data[mask_id]['points'].append({
                    'point_id': point_id,
                    'latitude': latitude,
                    'longitude': longitude,
                    'fire_status': fire_status
                })

        # Convert the dictionary values to a list
        response_data_list = list(response_data.values())

        # Return the JSON response
        return jsonify(response_data_list), 200
    except ValueError:
        return jsonify({'error': 'Invalid fire ID'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route("/map/get-region-data/<fire_id>")
def get_region_data(fire_id):
    try:
        print("fnsknflsdn this is the fire_id: ",fire_id )
        table_details = execute_read_stored_procedure("get_table_data", [fire_id])

        # Format the result as a list of dictionaries
        region_data = []
        for sublist in table_details:
            for data in sublist:
                region_dict = {
                    'wind_direction': data[4],
                    'wind_speed': data[5],
                    'min_temp': data[6],
                    'max_temp': data[7],
                    'humidity': data[8],
                    'precipitation': data[9],
                    'generation_date': data[10]
                }
                region_data.append(region_dict)

        # Log the region data
        print("Region data:", region_data)

        # Return the region data as JSON
        return jsonify(region_data), 200
    except Exception as e:
        # Log the error
        print("Error fetching region data:", e)
        return jsonify({'error': str(e)}), 500

@app.route("/map/get-min-max/<fire_id>")
def get_fire_bounds(fire_id):
    try:
        # Convert fire_id to integer
        fire_id = int(fire_id)

        # Call the stored procedure to get the min and max coordinates
        fire_data = execute_read_stored_procedure("get_max_and_min", [fire_id])
        
        # Initialize a list to store the response data
        response_data_list = []
        print(fire_data)
        # Extract the min and max coordinates from the response
        if fire_data:
            for sublist in fire_data:
                for point in sublist:
                    min_lat = point[0]
                    min_lng = point[1]
                    max_lat = point[2]
                    max_lng = point[3]

                    # Construct dictionaries for min and max coordinates
                    min_coord = {'lat': min_lat, 'lng': min_lng}
                    max_coord = {'lat': max_lat, 'lng': max_lng}

                    # Append dictionaries to the response list
                    response_data_list.append(min_coord)
                    response_data_list.append(max_coord)

        # Return the JSON response
        print(response_data_list)
        return jsonify(response_data_list), 200

    except ValueError:
        return jsonify({'error': 'Invalid fire ID'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route("/notification/process-opt-in", methods=['POST'])
def process_opt_in():
    success = False
    if request.method == "POST":
        try:
            phone_number = request.json['phone']
            longitude = request.json['lng']
            latitude = request.json['lat']

            success = Notification.handle_opt_in(latitude, longitude, phone_number)
        except Exception as e:
            print(e)
            success = False
        
    response = jsonify({"success": success})
    return response, 200

@app.route("/notification/process-opt-out", methods=['POST'])
def process_opt_out():
    success = False
    try:
        phone_number = request.json['phone_number']
        Notification.handle_opt_out(phone_number)
        success = True
    except Exception as e:
        print(e)
        success = False
    
    response = jsonify({'succcess': success})
    return response, 200


@app.route("/")
def home():
    print(users)
    response = "<h1> This will be the NEXT PAGE. No redirect will be necessary for API <h1>"
    response+= "<ul>"
    print(users)
    for user in users:
        response+= "<li>" + user["phoneNumber"] + "</li>"
    response+= "</ul>"

    return response