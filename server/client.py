# import socket
# from time import sleep # for socket


# def main():
#     try:
#         s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#         print ("Socket successfully created")
#     except socket.error as err:
#         print ("socket creation failed with error %s" %(err))

#     print("start")
#     # for num in range(3):
#     #     sleep(1)
#     #     print(num)
#     # connecting to the server
#     s.sendto("200:c".encode(), ("34.125.245.207", 3000))

#     print (s.recv(1024).decode())
# # close the connection
#     # s.close()   
# if __name__ == "__main__":
#     main()

import socket

HOST = "34.125.245.207"  # The server's hostname or IP address
PORT = 3000 # The port used by the server

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    s.sendall(b"Hello, world")
    data = s.recv(1024)

print(f"Received {data!r}")