"""This code is designed to parse AVL packets, which contain data like timestamps, GPS coordinates,
 and various IO (input/output) data from a device.

It starts by reading and skipping some header information, like the preamble and data length.
The codec ID is checked to ensure it's compatible (in this case, 0x08).
The code then loops through each data record in the packet, parsing details such as:
  1-Timestamp (converted into a human-readable format),
  2-GPS data (longitude, latitude, altitude, speed, etc.),
  3-IO data (various values like one-byte, two-byte, etc.).
For each record, the parsed information (timestamp, GPS, and IO data) is stored in a dictionary and added to a list.
The function finally returns the list of parsed AVL records, the number of records, and the current position 
in the packet (in case there's more to parse)."""

import struct
import time
from io_id_mapping import *

def parse_avl_packet(packet):
    index = 0
    avl_records = []
    no_of_records = 0


    try:
        # Parse the preamble (first 4 bytes)
        if len(packet) < index + 4:
            raise ValueError("Not enough data for preamble")
        # Parse the preamble (first 4 bytes)
        preamble = packet[index:index + 4]
        #preamble_hex = preamble.hex()  # Convert it to a readable hex format (optional)
        index += 4  # Move the index forward
        
        # Parse the data length (next 4 bytes)
        data_length = struct.unpack('>I', packet[index:index + 4])[0]
        index += 4
       
        # Parse the codec ID (next 1 byte)
        codec_id = packet[index]
        index += 1

        # Check codec ID once (assuming it should always be the same for the whole packet)
        if codec_id != 0x08:
            raise ValueError("Unsupported codec ID")

        # Parse the number of data records (next 1 byte)
        num_of_data_1 = packet[index]
        index += 1

        for record_num in range(num_of_data_1):
            # Process each AVL record
            # Parse the timestamp (next 8 bytes)
            timestamp = struct.unpack('>Q', packet[index:index + 8])[0]
            timestamp_seconds = timestamp / 1000
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(timestamp_seconds))
            index += 8

            # Parse the priority (next 1 byte)
            priority = packet[index]
            index += 1

            # Parse GPS data (longitude, latitude, altitude, angle, satellites, speed)
            longitude = struct.unpack('>I', packet[index:index + 4])[0] / 10**7
            latitude = struct.unpack('>I', packet[index + 4:index + 8])[0] / 10**7
            altitude = struct.unpack('>H', packet[index + 8:index + 10])[0]
            angle = struct.unpack('>H', packet[index + 10:index + 12])[0]
            satellites = packet[index + 12]
            speed = struct.unpack('>H', packet[index + 13:index + 15])[0]
            index += 15

            # Parse the IO data
            io_records = {
                'N1 (One Byte IO)': {},
                'N2 (Two Bytes IO)': {},
                'N4 (Four Bytes IO)': {},
                'N8 (Eight Bytes IO)': {}
            }

            # Event IO ID (next 1 byte)
            event_io_id = packet[index]
            index += 1

            # Total IO count (next 1 byte)
            n_total_id = packet[index]
            index += 1

            # One Byte IO data
            n1_one_byte_io = packet[index]
            index += 1
            for _ in range(n1_one_byte_io):
                io_id = struct.unpack('>B', packet[index:index + 1])[0]
                io_value = struct.unpack('>B', packet[index + 1:index + 2])[0]
                property_name = IO_ID_MAPPING.get(io_id, 'IO ID')
                io_records['N1 (One Byte IO)'][property_name] = io_value
                index += 2

            # Two Bytes IO data
            n2_two_bytes_io = packet[index]
            index += 1
            for _ in range(n2_two_bytes_io):
                io_id = packet[index]
                io_value = struct.unpack('>H', packet[index + 1:index + 3])[0]
                property_name = IO_ID_MAPPING.get(io_id, 'IO ID')
                io_records['N2 (Two Bytes IO)'][property_name] = io_value
                index += 3

            # Four Bytes IO data
            n4_four_bytes_io = packet[index]
            index += 1
            for _ in range(n4_four_bytes_io):
                io_id = packet[index]
                io_value = struct.unpack('>I', packet[index + 1:index + 5])[0]
                property_name = IO_ID_MAPPING.get(io_id, 'IO ID')
                io_records['N4 (Four Bytes IO)'][property_name] = io_value
                index += 5

            # Eight Bytes IO data
            n8_eight_bytes_io = packet[index]
            index += 1
            for _ in range(n8_eight_bytes_io):
                io_id = packet[index]
                io_value = struct.unpack('>Q', packet[index + 1:index + 9])[0]
                property_name = IO_ID_MAPPING.get(io_id, 'IO ID')
                io_records['N8 (Eight Bytes IO)'][property_name] = io_value
                index += 9

            # After parsing IO, proceed to the next AVL record (timestamp -> priority -> GPS -> IO)
            # Flatten IO records and append to the AVL records list
            flattened_io_records = {}
            for io_type, records in io_records.items():
                for key, value in records.items():
                    flattened_io_records[key] = value

            avl_records.append({
                'T': timestamp,
                'long': longitude,
                'lat': latitude,
                'altitude': altitude,
                'angle': angle,
                'satellites': satellites,
                'speed': speed,
                **flattened_io_records,
                'priority': priority,
                'end_position': index
            })
            no_of_records +=1

        # Final step, return the parsed AVL records and the number of records
        return avl_records, no_of_records, index # len(avl_records)

    except Exception as e:
        print("Error while parsing packet:", e)
        return None  # Ensure that None is returned if there is an error
