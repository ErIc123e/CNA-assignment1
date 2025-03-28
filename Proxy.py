# Include the libraries for socket and system calls
import socket
import sys
import os
import argparse
import re

# 1MB buffer size
BUFFER_SIZE = 1000000

# Get the IP address and Port number to use for this web proxy server
parser = argparse.ArgumentParser()
parser.add_argument('hostname', help='the IP Address Of Proxy Server')
parser.add_argument('port', help='the port number of the proxy server')
args = parser.parse_args()
proxyHost = args.hostname
proxyPort = int(args.port)

# Create a server socket, bind it to a port and start listening
try:
    # Create a server socket
    # AF_INET: IPv4 address family, SOCK_STREAM: TCP socket
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # ~~~~ END CODE INSERT ~~~~
    print('Created socket')
except:
    print('Failed to create socket')
    sys.exit()

try:
    # Bind the the server socket to a host and port
    # Bind the socket to the specified host and port
    serverSocket.bind((proxyHost, proxyPort))
     # ~~~~ END CODE INSERT ~~~~
    print('Port is bound')
except:
    print('Port is already in use')
    sys.exit()

try:
    # Listen on the server socket
    # Allow up to 5 pending connections in the queue
    serverSocket.listen(5)
    # ~~~~ END CODE INSERT ~~~~
    print('Listening to socket')
except:
    print('Failed to listen')
    sys.exit()

# Continuously accept connections
while True:
    print('Waiting for connection...')
    clientSocket = None

    # Accept connection from client and store in the clientSocket
    try:
        # Accept a connection from a client
        # clientSocket: new socket object to communicate with the client
        # clientAddress: address bound to the socket on the other end
        clientSocket, clientAddress = serverSocket.accept()
        # Send a simple acknowledgment message to the client
        # ~~~~ END CODE INSERT ~~~~
        print('Received a connection from:', clientAddress)
    except:
        print('Failed to accept connection')
        sys.exit()

    # Get HTTP request from client and store it in the variable: message_bytes
    try:
        # Initialize an empty buffer to accumulate data
        message_bytes = b""
        while True:
            # Receive data from the client socket
            data = clientSocket.recv(BUFFER_SIZE)
            if not data:
                print("Client closed the connection")
                clientSocket.close()
                break
            # Append the received data to the buffer    
            message_bytes += data
            # Check if the request is complete (ends with \r\n\r\n)
            if b"\r\n\r\n" in message_bytes:
                break

        # Decode the complete request
        message = message_bytes.decode('utf-8')
        print('Received request:')
        print('< ' + message)

        # Extract the method, URI and version of the HTTP client request
        requestParts = message.split()
        if len(requestParts) < 3:
            print("Invalid HTTP request")
            clientSocket.close()
            continue

        method = requestParts[0]
        URI = requestParts[1]
        version = requestParts[2]

        print('Method:\t\t' + method)
        print('URI:\t\t' + URI)
        print('Version:\t' + version)
        print('')

        # Get the requested resource from URI
        # Remove http protocol from the URI

        URI = re.sub('^(/?)http(s?)://', '', URI, count=1)
        # Remove parent directory changes - security
        URI = URI.replace('/..', '')

        # Split hostname from resource name
        resourceParts = URI.split('/', 1)
        if not resourceParts or not resourceParts[0]:
            print("Invalid URI: No hostname found")
            clientSocket.close()
            continue

        hostname = resourceParts[0]
        resource = '/'
        if len(resourceParts) == 2:
            # Resource is absolute URI with hostname and resource
            resource = resource + resourceParts[1]

        print('Requested Resource:\t' + resource)

        try:
            # Defined the base cache directory
            cacheDir = './cache'
            # Construct the initial cache path by joining the cache directory with the hostname
            # Replace any backslashes with forward slashes for consistent path formatting
            cacheLocation = os.path.join(cacheDir, hostname.replace('\\', '/'))

            # Check if the requested resource is a root path ('/') or ends with a slash
            # If so, append 'index.html' as the default file name for directory requests
            if resource == '/' or resource.endswith('/'):
                cacheLocation = os.path.join(cacheLocation, 'index.html').replace('\\', '/')
            else:
                # For non-root resources, strip the leading slash from the resource path
                # to avoid duplicate slashes in the file path, then append it to cacheLocation
                resourcePath = resource.lstrip('/')
                cacheLocation = os.path.join(cacheLocation, resourcePath).replace('\\', '/')
            # Print the computed cache file location for debugging purposes
            print('Cache location:\t\t' + cacheLocation)
            # Check if the file exists at the computed cache location
            if os.path.isfile(cacheLocation):
                # If the file exists, log a cache hit and proceed to serve it
                print('Cache hit! Loading from cache file: ' + cacheLocation)
                # Open the cached file in binary read mode ('rb') to read its contents
                with open(cacheLocation, 'rb') as cacheFile:
                    # Read the entire file into cacheData as bytes
                    cacheData = cacheFile.read()
                    # Construct HTTP response headers with proper formatting
                    # Includes status line, content length, content type, and connection close directive
                response_headers = (
                    "HTTP/1.1 200 OK\r\n"
                    f"Content-Length: {len(cacheData)}\r\n"
                    "Content-Type: text/html; charset=utf-8\r\n"
                    "Connection: close\r\n"
                    "\r\n"
                ).encode('utf-8')
                # Combine headers and cached data into a single response
                response = response_headers + cacheData
                
                # Attempt to send the response to the client
                try:
                    # Send the entire response over the socket to the client
                    clientSocket.sendall(response)
                    # Log success after sending the response
                    print('Cached response sent to the client')
                except Exception as e:
                    # Handle any errors that occur during sending (e.g., broken connection)
                    print('Error sending response:', e)
                finally:
                    # Ensure the client socket is closed after attempting to send the response
                    # This runs regardless of success or failure
                    clientSocket.close()
            else:
                # If the file doesn’t exist in the cache, log a cache miss
                print('Cache miss: File not found in cache')
                
                # ~~~~ INSERT CODE ~~~~
                # Create a socket to connect to the origin server
                originSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                try:
                    # Set a timeout of 10 seconds to prevent hanging on slow origin servers
                    originSocket.settimeout(10.0)
                    # Connect to the origin server on port 80 (default HTTP port)
                    originSocket.connect((hostname, 80))
                    print(f'Connected to origin server: {hostname}')

                    # Format the HTTP GET request for the origin server as per RFC 2616 Section 5.1.2
                    # Include mandatory Host header and Connection: close for clean termination
                    request = f"{method} {resource} HTTP/1.1\r\n"
                    request += f"Host: {hostname}\r\n"
                    request += "Connection: close\r\n\r\n"
                    
                    # Send the request to the origin server
                    originSocket.sendall(request.encode('utf-8'))
                    print('Request sent to origin server')

                    # Receive the full response from the origin server
                    response_bytes = b""
                    while True:
                        data = originSocket.recv(BUFFER_SIZE)
                        if not data:
                            break
                        response_bytes += data
                    
                    # Split response into headers and body using the double CRLF separator
                    header_end = response_bytes.find(b"\r\n\r\n")
                    if header_end == -1:
                        raise Exception("Invalid server response: No header-body separator")
                    
                    headers = response_bytes[:header_end].decode('utf-8', errors='ignore')
                    body = response_bytes[header_end + 4:]
                    
                    # Parse the status line to extract status code (e.g., 200, 301, 302, 404)
                    status_line = headers.split('\r\n')[0]
                    status_code = status_line.split()[1]
                    
                    # Extract key headers for cache-control and redirect handling
                    content_type = "text/html; charset=utf-8"  
                    location = None  
                    max_age = None   
                    
                    # Parse headers line by line (case-insensitive per RFC 2616)
                    for line in headers.split('\r\n'):
                        if line.lower().startswith('content-type:'):
                            content_type = line.split(':', 1)[1].strip()
                        elif line.lower().startswith('location:'):
                            location = line.split(':', 1)[1].strip()
                        elif line.lower().startswith('cache-control:'):
                            # Extract max-age value if present (RFC 2616 Section 13)
                            cache_control = line.split(':', 1)[1].strip().lower()
                            if 'max-age=' in cache_control:
                                try:
                                    max_age = int(cache_control.split('max-age=')[1].split(',')[0])
                                except ValueError:
                                    max_age = None  

                    # Handle caching logic only for 200 OK responses with valid max-age
                    if status_code == "200" and max_age != 0:
                        # Sanitize cacheLocation to remove invalid filename characters (?, &, =, etc.)
                        safe_cache_location = cacheLocation.replace('?', '_').replace('&', '_').replace('=', '_').replace(':', '_')
                        try:
                            # Create cache directory if it doesn't exist, using sanitized path
                            os.makedirs(os.path.dirname(safe_cache_location), exist_ok=True)
                            with open(safe_cache_location, 'wb') as cacheFile:
                                cacheFile.write(body)
                            print(f'Cached response at: {safe_cache_location} with max-age={max_age}')
                        except Exception as cache_error:
                            print(f'Failed to cache response: {cache_error}')
                    elif status_code in ("301", "302"):
                        # Log redirects but do not attempt to cache
                        print(f'Redirect detected: {status_code} to {location}')
                    elif max_age == 0:
                        print('Not caching due to Cache-Control: max-age=0')
                    else:
                        print(f'Not caching response with status: {status_code}')

                    # Prepare response headers for the client
                    response_headers = (
                        f"HTTP/1.1 {status_line.split(' ', 1)[1]}\r\n"  
                        f"Content-Length: {len(body)}\r\n"
                        f"Content-Type: {content_type}\r\n"
                    )
                    
                    # Include Location header for 301/302 redirects (RFC 2616 Section 10.3)
                    if status_code in ("301", "302") and location:
                        response_headers += f"Location: {location}\r\n"
                    
                    # Add Cache-Control header if max-age is specified
                    if max_age is not None:
                        response_headers += f"Cache-Control: max-age={max_age}\r\n"
                    
                    # Finalize headers with Connection: close
                    response_headers += "Connection: close\r\n\r\n"
                    response_headers = response_headers.encode('utf-8')
                    
                    # Combine headers and body into the final response
                    response = response_headers + body
                    
                    # Send the response to the client
                    clientSocket.sendall(response)
                    print(f'Response sent to client with status: {status_code}')

                except Exception as e:
                    # Enhanced error handling for origin server communication
                    print(f'Error communicating with origin server: {e}')
                    # Send appropriate error response based on failure type
                    if isinstance(e, socket.timeout):
                        error_response = (
                            "HTTP/1.1 504 Gateway Timeout\r\n"
                            "Content-Length: 0\r\n"
                            "Connection: close\r\n\r\n"
                        ).encode('utf-8')
                    else:
                        error_response = (
                            "HTTP/1.1 502 Bad Gateway\r\n"
                            "Content-Length: 0\r\n"
                            "Connection: close\r\n\r\n"
                        ).encode('utf-8')
                    clientSocket.sendall(error_response)
                    print('Sent error response to client')

                finally:
                    # Ensure sockets are closed in all cases
                    originSocket.close()
                    clientSocket.close()
                # ~~~~ END CODE INSERT ~~~~

        except Exception as e:
            print('Error accessing cache:', e)
            clientSocket.close()

    except Exception as e:
        print('Error parsing request:', e)
        clientSocket.close()
        continue