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
                # Close the client socket since there’s no response to send
                clientSocket.close()
        except Exception as e:
            print('Error accessing cache:', e)
            clientSocket.close()

    except Exception as e:
        print('Error parsing request:', e)
        clientSocket.close()
        continue
