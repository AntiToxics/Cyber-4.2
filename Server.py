"""
 Name: "Server_4+.py"
 Author: Barak Gonen and Nir Dweck and Gilad Elran
 Purpose: Provide a basis for Ex. 4+
 Date: 29/1/2025
"""

# Import modules
import socket
import os
import logging


# Server configuration constants
QUEUE_SIZE = 10
IP = '0.0.0.0'
PORT = 80
SOCKET_TIMEOUT = 2
HTTP_200 = 'HTTP/1.1 200 OK\r\n'
HTTP_400 = 'HTTP/1.1 400 BAD REQUEST\r\n'
HTTP_403 = 'HTTP/1.1 403 FORBIDDEN\r\n\r\n'
HTTP_404 = 'HTTP/1.1 404 NOT FOUND\r\n\r\n'
HTTP_500 = 'HTTP/1.1 500 INTERNAL SERVER ERROR\r\n\r\n'

# Directory that contains all website files
WEBROOT = 'web_root'

# Directory for uploaded files (inside WEBROOT)
UPLOAD_DIR = os.path.join(WEBROOT, 'upload')

# File returned when requesting "/"
DEFAULT_URL = 'index.html'

# Dictionary of URLs that should be redirected (302)
REDIRECTION_DICTIONARY = {
    '/moved': '/'
}

# Dictionary of file types for Content-Type header
CONTENT_TYPES = {
    'html': 'text/html;charset=utf-8',
    'jpg': 'image/jpeg',
    'css': 'text/css',
    'js': 'text/javascript; charset=UTF-8',
    'txt': 'text/plain',
    'ico': 'image/x-icon',
    'gif': 'image/jpeg',
    'png': 'image/png'
}


def get_file_data(file_name):
    """
    Reads data from a file

    :param file_name: File name
    :return: File data (as bytes)
    """
    # Build the full path to the file
    file_path = os.path.join(WEBROOT, file_name)

    with open(file_path, 'rb') as file:
        return file.read()


def parse_query_string(query_string):
    """
    Parses query string parameters

    :param query_string: Query string (e.g., "num=5&width=3")
    :return: Dictionary of parameters
    """
    params = {}
    if not query_string:
        return params

    pairs = query_string.split('&')
    for pair in pairs:
        if '=' in pair:
            key, value = pair.split('=', 1)
            params[key] = value

    return params


def handle_calculate_next(params, client_socket):
    """
    Handles /calculate-next endpoint
    Returns the next number after the given num parameter

    :param params: Dictionary of query parameters
    :param client_socket: Socket to send response
    :return: None
    """
    if 'num' not in params:
        http_header = HTTP_400
        logging.warning('HTTP/1.1 400 BAD REQUEST - missing num parameter')
        client_socket.send(http_header.encode())
        return

    try:
        num = int(params['num'])
        result = str(num + 1)

        http_header = HTTP_200
        http_header += 'Content-Type: text/plain\r\n'
        http_header += f'Content-Length: {len(result)}\r\n'
        http_header += '\r\n'

        http_response = http_header.encode() + result.encode()
        client_socket.send(http_response)
        logging.info(f'calculate-next: {num} -> {result}')
    except ValueError:
        http_header = HTTP_400
        logging.warning('HTTP/1.1 400 BAD REQUEST - num is not a number')
        client_socket.send(http_header.encode())


def handle_calculate_area(params, client_socket):
    """
    Handles /calculate-area endpoint
    Calculates area of triangle given height and width

    :param params: Dictionary of query parameters
    :param client_socket: Socket to send response
    :return: None
    """
    if 'height' not in params or 'width' not in params:
        http_header = HTTP_400
        logging.warning('HTTP/1.1 400 BAD REQUEST - missing height or width parameter')
        client_socket.send(http_header.encode())
        return

    try:
        height = float(params['height'])
        width = float(params['width'])
        area = (height * width) / 2.0
        result = str(area)

        http_header = HTTP_200
        http_header += 'Content-Type: text/plain\r\n'
        http_header += f'Content-Length: {len(result)}\r\n'
        http_header += '\r\n'

        http_response = http_header.encode() + result.encode()
        client_socket.send(http_response)
        logging.info(f'calculate-area: height={height}, width={width} -> {result}')
    except ValueError:
        http_header = HTTP_400
        logging.warning('HTTP/1.1 400 BAD REQUEST - height or width is not a number')
        client_socket.send(http_header.encode())


def handle_upload(params, body, client_socket):
    """
    Handles /upload endpoint (POST only)
    Saves uploaded file to upload directory

    :param params: Dictionary of query parameters
    :param body: Binary data of the uploaded file
    :param client_socket: Socket to send response
    :return: None
    """
    if 'file-name' not in params:
        http_header = HTTP_400
        logging.warning('HTTP/1.1 400 BAD REQUEST - missing file-name parameter')
        client_socket.send(http_header.encode())
        return

    file_name = params['file-name']

    file_path = os.path.join(UPLOAD_DIR, file_name)

    try:
        with open(file_path, 'wb') as f:
            f.write(body)

        http_header = HTTP_200
        http_header += '\r\n'
        client_socket.send(http_header.encode())
        logging.info(f'File uploaded: {file_name}')
    except Exception as e:
        http_header = HTTP_500
        logging.error(f'HTTP/1.1 500 INTERNAL SERVER ERROR - {e}')
        client_socket.send(http_header.encode())


def handle_image(params, client_socket):
    """
    Handles /image endpoint
    Returns an image from the upload directory

    :param params: Dictionary of query parameters
    :param client_socket: Socket to send response
    :return: None
    """
    if 'image-name' not in params:
        http_header = HTTP_404
        logging.warning('HTTP/1.1 404 NOT FOUND - missing image-name parameter')
        client_socket.send(http_header.encode())
        return

    image_name = params['image-name']
    file_path = os.path.join(UPLOAD_DIR, image_name)

    if not os.path.isfile(file_path):
        http_header = HTTP_404
        logging.warning(f'HTTP/1.1 404 NOT FOUND - image not found: {image_name}')
        client_socket.send(http_header.encode())
        return

    # Extract file extension
    file_extension = image_name.split('.')[-1]
    content_type = CONTENT_TYPES.get(file_extension)

    try:
        with open(file_path, 'rb') as f:
            data = f.read()

        http_header = HTTP_200
        http_header += f'Content-Type: {content_type}\r\n'
        http_header += f'Content-Length: {len(data)}\r\n'
        http_header += '\r\n'

        http_response = http_header.encode() + data
        client_socket.send(http_response)
        logging.info(f'Image served: {image_name}')
    except Exception as e:
        http_header = HTTP_500
        logging.error(f'HTTP/1.1 500 INTERNAL SERVER ERROR - {e}')
        client_socket.send(http_header.encode())


def handle_client_request(resource, client_socket, method, body):
    """
    Handles the client request – checks what was requested and sends a response
    :param resource: Requested resource (e.g. /index.html)
    :param client_socket: Socket used to communicate with the client
    :param method: HTTP method (GET or POST)
    :param body: Request body (for POST requests)
    :return: None
    """

    # Split resource into path and query string
    if '?' in resource:
        path, query_string = resource.split('?', 1) # splits only one time to avoid errors
    else:
        path = resource
        query_string = ''

    params = parse_query_string(query_string)

    # Handle new API endpoints
    if path == '/calculate-next':
        handle_calculate_next(params, client_socket)
        return

    if path == '/calculate-area':
        handle_calculate_area(params, client_socket)
        return

    if path == '/upload':
        if method != 'POST':
            http_header = HTTP_400
            logging.warning('HTTP/1.1 400 BAD REQUEST - upload requires POST')
            client_socket.send(http_header.encode())
            return
        handle_upload(params, body, client_socket)
        return

    if path == '/image':
        handle_image(params, client_socket)
        return

    # Original code for handling static files
    # If only "/" was requested, return index.html
    if resource == '/':
        uri = DEFAULT_URL
        logging.info(f'The uri is {uri}')
    else:
        # Remove the leading "/" from the resource
        uri = resource.lstrip('/')
        logging.info(f'The uri is {uri}')

    # Special check: if "/forbidden" was requested
    if resource == '/forbidden':
        http_header = HTTP_403
        logging.warning('HTTP/1.1 403 FORBIDDEN')
        client_socket.send(http_header.encode())
        return

    # Special check: if "/error" was requested
    if resource == '/error':
        http_header = HTTP_500
        logging.error('HTTP/1.1 500 INTERNAL SERVER ERROR')
        client_socket.send(http_header.encode())
        return

    # Check if the request should be redirected (302)
    if resource in REDIRECTION_DICTIONARY:
        new_location = REDIRECTION_DICTIONARY[resource]
        http_header = f'HTTP/1.1 302 MOVED TEMPORARILY\r\nLocation: {new_location}\r\n\r\n'
        logging.info('HTTP/1.1 302 MOVED TEMPORARILY')
        client_socket.send(http_header.encode())
        return

    # Build the full path to the requested file
    file_path = os.path.join(WEBROOT, uri)

    # Check if the file exists
    if not os.path.isfile(file_path):
        # File not found – send 404
        http_header = HTTP_404
        logging.warning('HTTP/1.1 404 NOT FOUND')
        client_socket.send(http_header.encode())
        return

    # Extract file extension
    # Example: index.html -> html
    file_extension = uri.split('.')[-1]

    # Get the matching Content-Type
    content_type = CONTENT_TYPES.get(file_extension)

    # Read file content
    try:
        data = get_file_data(uri)
    except Exception as e:
        # Error while reading the file
        http_header = HTTP_500
        logging.error(f'HTTP/1.1 500 INTERNAL SERVER ERROR{e}')
        client_socket.send(http_header.encode())
        return

    # Build the HTTP header
    http_header = HTTP_200
    http_header += f'Content-Type: {content_type}\r\n'
    http_header += f'Content-Length: {len(data)}\r\n'
    http_header += '\r\n'  # Empty line to end headers

    # Send response: header (text) + file data (binary)
    http_response = http_header.encode() + data
    client_socket.send(http_response)


def validate_http_request(request):
    """
    Checks whether the request is a valid HTTP request

    :param request: Request received from the client
    :return: Tuple (True/False if valid, requested resource, HTTP method)
    """

    # Split the request line into parts
    # Example: "GET /index.html HTTP/1.1"
    parts = request.split(' ')

    # Check: must contain at least 3 parts
    if len(parts) < 3:
        logging.error('Invalid HTTP request')
        return False, '', ''

    # Check: first word must be GET or POST
    method = parts[0]
    if method not in ['GET', 'POST']:
        logging.error('Invalid HTTP request: invalid verb')
        return False, '', ''

    # Check: HTTP version must start with HTTP/1.1
    if not parts[2].startswith('HTTP/1.1'):
        logging.error('Invalid HTTP request: Version is not 1.1')
        return False, '', ''

    # The requested resource is the second part
    resource = parts[1]
    logging.info("Valid HTTP request")
    return True, resource, method


def handle_client(client_socket):
    """
    Handles a client: receives a request, validates it, and responds
    :param client_socket: Socket used to communicate with the client
    :return: None
    """
    print('Client connected')

    try:
        # Receive data from the client character by character
        # until an empty line (\r\n\r\n) is received
        client_request = ''

        while not client_request.endswith('\r\n\r\n'):
            # Read exactly one byte at a time
            char = client_socket.recv(1).decode()
            client_request += char

        # Print the full request
        print(f'Client request:\n{client_request}')

        # Extract only the first line
        first_line = client_request.split('\r\n')[0]
        logging.info(f'First line: {first_line}')

        # Validate the HTTP request
        valid_http, resource, method = validate_http_request(first_line)

        if valid_http:
            print('Got a valid HTTP request')

            # For POST requests, read the body
            body = b''
            if method == 'POST':
                # Parse headers to get Content-Length
                headers = client_request.split('\r\n')
                content_length = 0
                for header in headers:
                    if header.lower().startswith('content-length:'):
                        content_length = int(header.split(':')[1].strip())
                        break

                # Read the body
                if content_length > 0:
                    body = client_socket.recv(content_length)

            handle_client_request(resource, client_socket, method, body)
        else:
            print('Error: Not a valid HTTP request')
            # Send 400 Bad Request
            http_header = HTTP_400
            client_socket.send(http_header.encode())

    except socket.timeout:
        print('Socket timeout - no data received')
    except Exception as e:
        print(f'Error handling client: {e}')
        logging.error(e)

    print('Closing connection')


def main():
    # Main function: opens a socket and waits for clients

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server_socket.bind((IP, PORT))
        server_socket.listen(QUEUE_SIZE)
        print("Listening for connections on port %d" % PORT)

        while True:
            client_socket, client_address = server_socket.accept()
            try:
                print('New connection received')
                client_socket.settimeout(SOCKET_TIMEOUT)
                handle_client(client_socket)
            except socket.error as err:
                print('Received socket exception - ' + str(err))
            finally:
                client_socket.close()
                logging.info('Closing connection')
    except socket.error as err:
        print('Received socket exception - ' + str(err))
    finally:
        server_socket.close()
        logging.info('Closing Server')


if __name__ == "__main__":

    # Logging setup
    logging.basicConfig(
        filename='Server.log',
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    # Assertions / tests
    valid, resource, method = validate_http_request('GET / HTTP/1.1')
    assert valid is True, "validate_http_request failed on valid request"
    assert resource == '/', "validate_http_request returned wrong resource"
    assert method == 'GET', "validate_http_request returned wrong method"

    # Test: validate_http_request rejects invalid requests
    valid, resource, method = validate_http_request('DELETE / HTTP/1.1')  # should log an error
    assert valid is False, "validate_http_request should reject DELETE"

    # Test: validate_http_request accepts POST
    valid, resource, method = validate_http_request('POST /upload HTTP/1.1')
    assert valid is True, "validate_http_request should accept POST"
    assert method == 'POST', "validate_http_request should return POST method"

    # Test: get_file_data reads a file
    if os.path.isfile(os.path.join(WEBROOT, DEFAULT_URL)):
        data = get_file_data(DEFAULT_URL)
        assert data is not None, "get_file_data returned None"
        assert isinstance(data, bytes), "get_file_data should return bytes"

    # Test: parse_query_string
    params = parse_query_string('num=5')
    assert params == {'num': '5'}, "parse_query_string failed on single param"

    params = parse_query_string('height=3&width=4')
    assert params == {'height': '3', 'width': '4'}, "parse_query_string failed on multiple params"

    logging.info('Server started: All assert tests passed successfully')

    main()
