import socket
import threading
import time

from packet import Packet, PacketType, PayloadFormat


class Client:
    def __init__(self, server_ip, server_port):
        self.server_ip = server_ip
        self.server_port = server_port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.peer_addr = None

    @property
    def peer_to_peer_established(self) -> bool:
        return self.peer_addr is not None

    def _send_packet(self, packet: Packet, to = None) -> None:
        self.socket.sendto(packet.serialize(), to if to else self.peer_addr) #pyright: ignore

    def register_with_server(self, phrase: str):
        packet = Packet(PacketType.CONNECT, 0, PayloadFormat.CONNECT.pack(phrase.encode()))
        self._send_packet(packet, (self.server_ip, self.server_port))

        data, _ = self.socket.recvfrom(1024)
        peer_ip, peer_port = data.decode('utf-8').split(':')

        self.peer_addr = (peer_ip, int(peer_port))
        print(f"Received peer info: {self.peer_addr}")

    def start_communication(self):
        packet = Packet(PacketType.CONNECT, 0, PayloadFormat.CONNECT.pack("UDP connect packet".encode()))
        self._send_packet(packet)

        while True:
            data, _ = self.socket.recvfrom(1024)
            if data:
                packet = Packet.deserialize(data)
                threading.Thread(target=self.handle_data, args=(packet,), daemon=True).start()

    def send_message(self, message: str):
        packet = Packet(PacketType.CONNECT, 0, PayloadFormat.CONNECT.pack(message.encode()))
        self._send_packet(packet)

    def send_update(self, position: tuple[float, float]):
        packet = Packet(PacketType.UPDATE, 0, PayloadFormat.UPDATE.pack(*position))
        self._send_packet(packet)

    def start(self) -> None:
        threading.Thread(target=self.start_communication, daemon=True).start()

    def handle_data(self, packet: Packet) -> None:
        print("Recieved packet:", packet)


if __name__ == "__main__":
    import os
    ip = os.environ.get('SERVER_IP', 'localhost')

    client = Client('localhost', 8888)
    client.register_with_server("pineapple")
    client.start()

    while 1:
        client.send_message("Hi client2!")
        time.sleep(1)
