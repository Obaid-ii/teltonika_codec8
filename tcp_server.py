import socket
import logging
from parsing_data import *
from data_to_provisioner import *

logging.basicConfig(level=logging.INFO)

# For now I'm hardcoding device_ID
device_id = "codec_8"

def parse_imei(imei_data):
    imei_length = int.from_bytes(imei_data[:2], byteorder='big')
    imei = imei_data[2:2 + imei_length].decode('ascii')
    return imei

def start_tcp_server(host='0.0.0.0', port=5000):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(1)
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
                                parsed_data, num_of_data_1, num_of_bytes_processed = parse_avl_packet(avl_data)
                                logging.info(f'Parsed AVL Data: {parsed_data}')
                                
                                # Send parsed data to the API
                                if isinstance(parsed_data, list):
                                    for record in parsed_data:
                                        # Send each record to the API
                                        send_data_to_api(device_id, [record])

                                # Construct and send response based on Number of Data (Records)
                                response = struct.pack('>I', num_of_data_1)
                                logging.info(f"Sending response: {response}")
                                connection.sendall(response)
                                 # Remove processed data from avl_data (adjust as necessary)
                                avl_data = avl_data[num_of_bytes_processed:]  # Use the correct number of bytes processed

                                # If there are remaining bytes, continue parsing
                                avl_data = avl_data[parsed_data[-1]['end_position']:]  # Adjust as needed
                            
                            except Exception as e:
                                logging.error('Error parsing AVL data:', e)
                                break

                    except (ConnectionResetError, ConnectionAbortedError) as e:
                        logging.error(f"Connection error: {e}")
                        break

            except Exception as e:
                logging.error(f"Error in IMEI handling: {e}")

        except Exception as e:
            logging.error(f"Server accept error: {e}")

        finally:
            connection.close()

if __name__ == "__main__":
    start_tcp_server()