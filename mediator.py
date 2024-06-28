import socket

from packet import Packet, PacketType


class MediatorServer:
    def __init__(self, host='0.0.0.0', port=8888):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_socket.bind((host, port))
        self.clients = {}

    def start(self):
        print("Mediator server started.")
        while True:
            data, addr = self.server_socket.recvfrom(1024)
            if data:
                packet = Packet.deserialize(data)
                if packet.packet_type != PacketType.CONNECT:
                    continue

                phrase = packet.payload.decode()

                if phrase in self.clients.keys():
                    client = self.clients.pop(phrase)
                    self.exchange_info(client, addr)
                    continue

                self.clients[phrase] = addr
                print(f"Registered {phrase}: {addr}")

    def exchange_info(self, client1, client2):
        print(client1, client2)
        self.server_socket.sendto(
            f"{client1[0]}:{client1[1]}".encode('utf-8'), client2)
        self.server_socket.sendto(
            f"{client2[0]}:{client2[1]}".encode('utf-8'), client1)


if __name__ == "__main__":
    # Run the mediator server
    server = MediatorServer()
    server.start()
