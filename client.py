import socket
import threading
import time

from packet import Packet, PacketType, PayloadFormat
from shared import DISCONNECT_TIME

class Player:
    def __init__(self):
        self.position: tuple[float, float]
        self.old_position: tuple[float, float]
        self.direction: bool = False  # TODO typealias


class Client:
    def __init__(self, server_ip, server_port):
        self.server_ip = server_ip
        self.server_port = server_port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.peer_addr = None
        self.phrase = ""
        self.event_stack = []
        self.time_last_packet: float = 0
        self.running = True

        self.other_player: Player | None = None

    @property
    def peer_to_peer_established(self) -> bool:
        return self.peer_addr is not None

    def _send_packet(self, packet: Packet, to = None) -> None:
        self.socket.sendto(packet.serialize(), to if to else self.peer_addr) #pyright: ignore

    def _check_disconnected(self) -> bool:
        return self.time_last_packet <= time.time() + DISCONNECT_TIME

    def register_with_server(self, phrase: str):
        packet = Packet(PacketType.CONNECT, 0, PayloadFormat.CONNECT.pack(phrase.encode()))
        self._send_packet(packet, (self.server_ip, self.server_port))

        data, _ = self.socket.recvfrom(1024)
        peer_ip, peer_port = data.decode('utf-8').split(':')

        self.peer_addr = (peer_ip, int(peer_port))
        self.phrase = phrase

    def start_communication(self):
        packet = Packet(PacketType.CONNECT, 0, PayloadFormat.CONNECT.pack("UDP connect packet".encode()))
        self._send_packet(packet)

        while self.running:
            data, _ = self.socket.recvfrom(1024)
            if data:
                packet = Packet.deserialize(data)
                threading.Thread(target=self.handle_data, args=(packet,), daemon=True).start()

    def send_message(self, message: str) -> None:
        packet = Packet(PacketType.CONNECT, 0, PayloadFormat.CONNECT.pack(message.encode()))
        self._send_packet(packet)

    def send_update(self, position: tuple[float, float], direction: bool, anim_frame: int, state: int) -> None: # TODO typealias
        packet = Packet(PacketType.UPDATE, 0, PayloadFormat.UPDATE.pack(int(position[0]), int(position[1]), direction, anim_frame, state))
        self._send_packet(packet)

    def start(self) -> None:
        threading.Thread(target=self.start_communication, daemon=True).start()

    def handle_data(self, packet: Packet) -> None:
        self.time_last_packet = time.time()
        print("Recieved packet:", packet)
        if packet.packet_type == PacketType.UPDATE:
            x_pos, y_pos, direction, anim_frame, state = PayloadFormat.UPDATE.unpack(packet.payload)
            if not self.other_player:
                #  self.event_stack.append()  add Player joined event
                self.other_player = Player()

            else:
                self.other_player.old_position = self.other_player.position

            self.other_player.position = (x_pos, y_pos)
            self.other_player.direction = direction

    def stop(self) -> None:
        self.running = False


if __name__ == "__main__":
    import os
    ip = os.environ.get('SERVER_IP', 'localhost')

    client = Client(ip, 8888)
    client.register_with_server("pineapple")
    client.start()

    while 1:
        client.send_message("Hi client2!")
        time.sleep(1)
