import requests
import json
from datetime import datetime, timezone

def send_data_to_api(device_id, parsed_data):
    # Get the current time
    current_time = datetime.now(timezone.utc)

    # Helper function to calculate rtp value
    def get_rtp(timestamp):
    # Convert the timestamp from the payload to a timezone-aware datetime object
        try:
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
        # Process all records
        #data_to_send = []
        for record in parsed_data:
            # Add rtp field to each record
            timestamp = record.get('T')
            rtp = get_rtp(timestamp) if timestamp else 0
            record['rtp'] = rtp
            #data_to_send.append(record)

        # Construct the payload including the DeviceID
        payload = {
            'DeviceID': device_id,
            **record  # Unpack the first record into the payload
        }

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
            print('Data sent successfully to the API:', response.json())
        else:
            print(f"Failed to send data, Status code: {response.status_code}, Response: {response.text}")

    except requests.exceptions.RequestException as e:
        print(f"An error occurred while sending data to the API: {e}")
