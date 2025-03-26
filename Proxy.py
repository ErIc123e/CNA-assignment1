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
  print ('Created socket')
except:
  print ('Failed to create socket')
  sys.exit()

try:
  # Bind the the server socket to a host and port
  # Bind the socket to the specified host and port
  serverSocket.bind((proxyHost, proxyPort))
  # ~~~~ END CODE INSERT ~~~~
  print ('Port is bound')
except:
  print('Port is already in use')
  sys.exit()

try:
  # Listen on the server socket
  # Allow up to 5 pending connections in the queue
  serverSocket.listen(5)
  # ~~~~ END CODE INSERT ~~~~
  print ('Listening to socket')
except:
  print ('Failed to listen')
  sys.exit()

# continuously accept connections
while True:
  print ('Waiting for connection...')
  clientSocket = None

  # Accept connection from client and store in the clientSocket
  try:
    # Accept a connection from a client
    # clientSocket: new socket object to communicate with the client
    # clientAddress: address bound to the socket on the other end
    clientSocket, clientAddress = serverSocket.accept()
    # Send a simple acknowledgment message to the client
    clientSocket.sendall(b"Connected to proxy server\r\n")
    # ~~~~ END CODE INSERT ~~~~
    print ('Received a connection from:', clientAddress)
  except:
    print ('Failed to accept connection')
    sys.exit()

  # Get HTTP request from client
  # and store it in the variable: message_bytes
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
      hostname = resourceParts[0]
      resource = '/'

      if len(resourceParts) == 2:
          # Resource is absolute URI with hostname and resource
          resource = resource + resourceParts[1]

      print('Requested Resource:\t' + resource)

  except Exception as e:
      print('Error parsing request:', e)
      clientSocket.close()
      continue