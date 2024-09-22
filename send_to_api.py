import requests
import json
from datetime import datetime, timezone

def send_data_to_api(device_id, parsed_data):
    # Helper function to calculate rtp value
    def get_rtp(timestamp):
        try:
            # Convert the timestamp from the payload to a timezone-aware datetime object
            payload_time = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
            payload_time = payload_time.replace(tzinfo=timezone.utc)  # Make it UTC aware
        except ValueError:
            # Handle incorrect timestamp format
            return 0

        # Get the current time as an aware datetime
        current_time = datetime.now(timezone.utc)

        # Calculate the time difference in seconds
        time_diff = (current_time - payload_time).total_seconds()
        # Determine the rtp value based on the time difference
        return 1 if time_diff <= 60 else 0

    # Check if parsed_data is a list and contains at least one record
    if parsed_data and isinstance(parsed_data, list) and len(parsed_data) > 0:
        # Iterate through each record
        for record in parsed_data:
            # Ensure that the required fields exist
            timestamp = record.get('T')
            rtp = get_rtp(timestamp) if timestamp else 0
            record['rtp'] = rtp  # Add rtp field to the record
            
            # Construct the payload including the DeviceID and the current record
            payload = {
                'DeviceID': device_id,
                **record  # Wrap the record in a "data" field
            }

            # Convert the payload into JSON format
            payload_json = json.dumps(payload)

            # Define your API endpoint
            url = "http://20.174.9.78:8000/receive-data"

            try:
                # Send a POST request to your API with the JSON payload
                response = requests.post(url, data=payload_json, headers={'Content-Type': 'application/json'})

                # Check the response
                if response.status_code == 200:
                    print(f"Data sent successfully to the API for Device {device_id}: {response.json()}")
                else:
                    print(f"Failed to send data, Status code: {response.status_code}, Response: {response.text}")

            except requests.exceptions.RequestException as e:
                print(f"An error occurred while sending data to the API: {e}")

    else:
        # Handle case where parsed_data is empty or not a list
        payload = {
            'DeviceID': device_id,
            'error': 'No valid data received'
        }

        # Convert the payload into JSON format
        payload_json = json.dumps(payload)

        # Define your API endpoint
        url = "http://20.174.9.78:8000/receive-data"

        try:
            # Send a POST request to your API with the JSON payload
            response = requests.post(url, data=payload_json, headers={'Content-Type': 'application/json'})

            # Check the response
            if response.status_code == 200:
                print(f"Error report sent successfully to the API for Device {device_id}: {response.json()}")
            else:
                print(f"Failed to send error report, Status code: {response.status_code}, Response: {response.text}")

        except requests.exceptions.RequestException as e:
            print(f"An error occurred while sending error message to the API: {e}")
