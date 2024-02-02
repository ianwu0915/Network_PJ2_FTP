import socket
import sys
import argparse


class FtpClient:
    def __init__(self):
        # Socket for control channel open to the FTP server port 21
        # for sending FTP requests and receiving FTP responses
        self.control_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect_to_server(self, address, port):
        try:
            self.control_socket.connect((address, port))
        except socket.error as e:
            print("Can't connect to the server with error %s", e)

        # do I need to decode and encode?
        response = self.control_socket.recv(2048).decode("ascii")
        print(response)

    def send_message(self, message):
        self.control_socket.sendall(message.encode('ascii'))

        # how to continuously recieve data from ftp server (ends with \r\n)
        while True:
            response = self.control_socket.recv(2048).decode('ascii')
            print(response)
            if not response.endswith('\r\n'):
                break

    def login_to_ftp(self, username=None, password=None):
        # Send USER and PASS commands
        if username:
            user_command = f"USER {username}\r\n"
        else:
            user_command = "USER\r\n"
        self.send_message(user_command)
        if password:
            pass_command = f"PASS {password}\r\n"
            self.send_message(pass_command)

    # Your client should set the TYPE before attempting to upload or download any data.
    def set_type(self):
        type_command = "TYPE I\r\n"
        self.send_message(type_command)

    # Your client should set STRU before attempting to upload or download any data.
    def set_stru(self):
        strf_command = "STRU F\r\n"
        self.send_message(strf_command)

    # Ask the FTP server to close the connection.
    def quit(self):
        quit_command = "QUIT\r\n"
        self.send_message(quit_command)

    def make_directory(self, pathToDirectory):
        mkd_command = f"MKD {pathToDirectory}\r\n"
        self.send_message(mkd_command)

    def remove_directory(self, pathToDirectory):
        mkd_command = f"RMD {pathToDirectory}\r\n"
        self.send_message(mkd_command)

    def list(self, pathToDirectory):
        list_command = f"LIST {pathToDirectory}\r\n"
        self.data_socket.sendall(list_command.encode('ascii'))

        # how to continuously receive data from ftp server (ends with \r\n)
        while True:
            response = self.data_socket.recv(2048).decode('ascii')
            print(response)
            if not response.endswith('\r\n'):
                break

    # Send PASV command to the server
    # if the server returns the right message, use the data socket to connect to the data channel
    def pasv(self):
        pasv_command = "PASV\r\n"
        self.control_socket.sendall(pasv_command.encode("ascii"))
        response = self.control_socket.recv(2048).decode('ascii')

        # 227 indicate success
        # Parse and calculate the ip address and port
        # Connect to the data channel
        if response.startswith("227"):
            self.data_socket.connect(parse_pasv_response(response))


def parse_pasv_response(response):
    start = response.find('(')
    end = response.find(')')

    numbers = response[start + 1:end].split(',')
    ip_address = '.'.join(numbers[:4])
    port = (int(numbers[4]) << 8) + int(numbers[5])

    return ip_address, port


def parse_arguments():
    command_parser = argparse.ArgumentParser()
    command_parser.add_argument("operation",
                                help="The operation to execute. Valid operations are 'ls', 'rm', 'rmdir','mkdir', 'cp', and 'mv'")
    command_parser.add_argument("param1", help="first string parameter, either a path or a utl to a file ")
    command_parser.add_argument("param2", help="second string parameter, either a path or a utl to a file ")

    return command_parser.parse_args()


def main():
    # command line parsing
    # $ ./4700ftp [operation] [param1] [param2]

    args = parse_arguments()
    print(args)

    address = "ftp.4700.network"
    port = 21

    username, password = "", ""

    client = FtpClient()
    client.connect_to_server(address, port)
    client.login_to_ftp()

    if args.operation == "mkdir":
        client.make_directory(args.param1)
    elif args.operation == "rmdir":
        client.remove_directory(args.param1)
    elif args.operatoin == "ls":
        client.list(args.param1)
    # for upload or download data
    client.set_type()
    client.set_stru()
    client.quit()


if __name__ == '__main__':
    main()
