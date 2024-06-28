import socket
import threading
import time


class Client:
    def __init__(self, server_ip, server_port, client_id):
        self.server_ip = server_ip
        self.server_port = server_port
        self.client_id = client_id
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.peer_addr = None

    def register_with_server(self):
        self.socket.sendto(self.client_id.encode('utf-8'),
                           (self.server_ip, self.server_port))
        data, _ = self.socket.recvfrom(1024)
        peer_ip, peer_port = data.decode('utf-8').split(':')
        self.peer_addr = (peer_ip, int(peer_port))
        print(f"Received peer info: {self.peer_addr}")

    def start_communication(self):
        # Send initial packet to peer to create a "hole" in NAT
        self.socket.sendto("Hello from client".encode('utf-8'), self.peer_addr)

        # Start listening for incoming messages from peer
        threading.Thread(target=self.listen_for_messages).start()

    def listen_for_messages(self):
        while True:
            data, addr = self.socket.recvfrom(1024)
            if data:
                print(f"Received from {addr}: {data.decode('utf-8')}")

    def send_message(self, message):
        self.socket.sendto(message.encode('utf-8'), self.peer_addr)


if __name__ == "__main__":
    import os
    ip = os.environ.get('SERVER_IP', 'localhost')

    client = Client('localhost', 8888, 'client2')
    client.register_with_server()
    client.start_communication()

    while 1:
        client.send_message("Hi client2!")
        time.sleep(1)
