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
        response = self.control_socket.recv(4096).decode('ascii')
        print(response)

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

    def set_mode(self):
        mode_command = "MODE S\r\n"
        self.send_message(mode_command)

    # Your client should set STRU before attempting to upload or download any data.
    def set_stru(self):
        strf_command = "STRU F\r\n"
        self.send_message(strf_command)

    # Send PASV command to the server
    # if the server returns the right message, use the data socket to connect to the data channel
    def pasv(self):
        pasv_command = "PASV\r\n"
        self.control_socket.sendall(pasv_command.encode("ascii"))
        response = self.control_socket.recv(4096).decode('ascii')
        print(response)

        # 227 indicate success
        # Parse and calculate the ip address and port
        # Connect to the data channel
        if response.startswith("227"):
            try:
                address = parse_pasv_response(response)
                print(address)

                self.data_socket.connect(address)
                print("Data socket connected to server: ", self.data_socket.getpeername())

            except socket.error as e:
                print("Can't connect to the server with error %s", e)

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
        response = self.control_socket.recv(2048).decode('ascii')

    # set mode, stru, type and open pasv mode
    def open_data_channel(self):
        self.set_mode()
        self.set_stru()
        self.set_type()
        self.pasv()

    def list(self, pathToDirectory=None):
        self.open_data_channel()

        list_command = f"LIST {pathToDirectory}\r\n"
        # self.data_socket.sendall(list_command.encode('ascii'))
        # response = self.data_socket.recv(2048).decode('ascii')
        self.send_message(list_command)
        print("sending the list request")

        while True:
            data_response = self.data_socket.recv(2048).decode('ascii')
            if not data_response:
                break
            print(data_response)

    # Upload a new file with the given path and name to the FTP server.
    def stor(self, store_location_path, remote_path=None):
        # STOR command sent
        with open(store_location_path, 'rb') as file:
            self.open_data_channel()
            stor_command = f"STOR {remote_path}\r\n"
            print(stor_command)
            self.send_message(stor_command)


            print("start sending data")
            while True:
                file_data = file.read(2048)  # Read in chunks
                if not file_data:
                    break
                self.data_socket.sendall(file_data)

        self.data_socket.close()
        control_response = self.control_socket.recv(4096).decode('ascii')
        print(control_response)

    # Download a file with the given path and name from the FTP server.
    def retr(self, remote_file_path, local_file_path):
        self.open_data_channel()
        retr_command = f"STOR {remote_file_path}\r\n"
        self.send_message(retr_command)

        try:
            with open(local_file_path, 'wb') as file:
                while True:
                    file_data = self.data_socket.recv(2048)
                    if not file_data:
                        break
                    file.write(file_data)

            control_response = self.control_socket.recv(4096).decode('ascii')
            print(control_response)

        except Exception as e:
            print(f"Error during file download: {e}")


    # Delete the given file on the FTP server.
    def dele(self, pathTofile):
        self.open_data_channel()
        dele_command = f"DELE {pathTofile}\r\n"
        self.send_message(dele_command)


    # Move: RETR + STOR
    # Two Scenario: ftp to local ; local to ftp
    def move_server_to_local(self, ftp_path, local_path):
        # filename = ftp_path.split('/')[-1]
        # temp_local_file = f"/Users/ianwu/Desktop/NEU/CS5700_NETWORK/PJ2_FTP/temp_file/{filename}"

        # download the file to local
        self.retr(ftp_path, local_path)
        # delete the original file
        self.dele(ftp_path)


    def move_local_to_server(self, local_file_path, server_path):
        # upload to the server
        self.stor(local_file_path, server_path)
        # delete the original file

    # Copy: RETR + STOR + DELETE original file
    def copy_server_to_local(self, server_path, local_path):
        self.retr(server_path, local_path)

    def copy_local_to_server(self, local_path, server_path):
        # upload to server
        self.stor(local_path, server_path)

def parse_pasv_response(response):
    start = response.find('(')
    end = response.find(')')

    numbers = response[start + 1:end].split(',')
    ip_address = '.'.join(numbers[:4])
    port = (int(numbers[4]) << 8) + int(numbers[5])
    print(ip_address, port)

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

    # args = parse_arguments()
    # print(args)

    address = "ftp.4700.network"
    port = 21

    username, password = "ianwu0915", "899d51b6f01617357b012166090dd9fe0a3c9ae416020838d2d4469363449bc9"

    url = "ftp://ianwu0915:899d51b6f01617357b012166090dd9fe0a3c9ae416020838d2d4469363449bc9@ftp.4700.network/test"

    client = FtpClient()
    client.connect_to_server(address, port)
    client.login_to_ftp(username, password)
    # client.make_directory("test1")
    # client.make_directory("test1/ folder1")
    # client.remove_directory("/test")
    # client.list("test1/ folder1")
    local_path = "/Users/ianwu/Desktop/NEU/CS5700_NETWORK/PJ2_FTP/temp_file/empty.txt"
    # client.stor(local_path, "test1/test.txt")
    # client.move_local_to_server(local_path, "hello.txt")
    client.move_server_to_local("empty.txt", local_path)
    # client.dele("test1")

    # if args.operation == "mkdir":
    #     client.make_directory(args.param1)
    # elif args.operation == "rmdir":
    #     client.remove_directory(args.param1)
    # elif args.operatoin == "ls":
    #     client.list(args.param1)
    # # for upload or download data
    # client.set_type()
    # client.set_stru()
    client.quit()


if __name__ == '__main__':
    main()
