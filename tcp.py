
"""This Python code is for a TCP server that listens for connections from devices,
 receives data from them, and processes it. The data is associated with a unique IMEI 
 (International Mobile Equipment Identity) number for each device. 
 The server parses the IMEI, processes data (called AVL data), and sends it to an API."""

import socket
import struct
import logging
from parser import *
from send_to_api import *

logging.basicConfig(level=logging.INFO)

"""This class holds information for each connected device. Each device has an IMEI and
 a list of AVL records (data records from the device)."""

class Device:
    def __init__(self, imei):
        self.imei = imei
        self.avl_records = []

    def add_avl_record(self, avl_record):
        self.avl_records.append(avl_record)

# Global dictionary to manage connected devices
connected_devices = {}

def parse_imei(imei_data):
    imei_length = int.from_bytes(imei_data[:2], byteorder='big')
    imei = imei_data[2:2 + imei_length].decode('ascii')
    return imei

def start_tcp_server(host='0.0.0.0', port=9025):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(5)  # Allow multiple connections
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)

    logging.info(f'Started TCP server on {host}:{port}')

    while True:
        try:
            connection, client_address = server_socket.accept()
            logging.info(f'Connection from {client_address}')

            try:
                imei_data = connection.recv(1024)
                if not imei_data:
                    logging.info("No IMEI data received. Closing connection.")
                    connection.close()
                    continue

                logging.info(f"Received IMEI data: {imei_data}")

                try:
                    imei = parse_imei(imei_data)
                    logging.info(f"Parsed IMEI: {imei}")
                    connection.sendall(b'\x01')  # IMEI accepted
                    
                    # Check if this device is already connected
                    if imei not in connected_devices:
                        connected_devices[imei] = Device(imei)
                        logging.info(f"New device added: {imei}")
                    else:
                        logging.info(f"Device {imei} reconnected.")

                    device = connected_devices[imei]  # Get the device object

                except Exception as e:
                    logging.error(f"Failed to parse IMEI: {e}")
                    connection.sendall(b'\x00')  # IMEI rejected
                    connection.close()
                    continue

                while True:
                    try:
                        avl_data = connection.recv(4096)  # Adjust buffer size as needed
                        if not avl_data:
                            logging.info("No AVL data received. Closing connection.")
                            break

                        logging.info(f'Received raw AVL data: {avl_data}')

                        while avl_data:
                            try:
                                # Parse the AVL packet
                                parsed_data, num_of_data_1, num_of_bytes_processed = parse_avl_packet(avl_data)
                                logging.info(f'Parsed AVL Data: {parsed_data}')

                                # Store each parsed record into the device object
                                if isinstance(parsed_data, list):
                                    for record in parsed_data:
                                        device.add_avl_record(record)
                                        # Remove 'end_position' from the record before sending to the API
                                        record_for_api = {k: v for k, v in record.items() if k != 'end_position'}
                                        # Send the record to the API
                                        send_data_to_api(imei, [record_for_api])

                                # Construct and send response based on Number of Data (Records)
                                response = struct.pack('>I', num_of_data_1)
                                logging.info(f"Sending response: {response}")
                                connection.sendall(response)  # Send the original packed response

                                # Remove processed data from avl_data (adjust as necessary)
                                avl_data = avl_data[num_of_bytes_processed:]

                            except Exception as e:
                                #logging.error(f'Error parsing AVL data: {e}')
                                break

                    except (ConnectionResetError, ConnectionAbortedError) as e:
                        logging.error(f"Connection error: {e}")
                        break

            except Exception as e:
                logging.error(f"Error in IMEI handling: {e}")

        except Exception as e:
            logging.error(f"Server accept error: {e}")

        finally:
            # Clean up the connection
            connection.close()

if __name__ == "__main__":
    start_tcp_server()
