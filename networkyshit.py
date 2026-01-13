import json
import queue
import socket
import threading
import time

# ---------- EVENT KEY ---------- (most important yes?)
# 0 = join --> have someone who was already in the game give the joining player all the game states
# 1 = join response --> explained above lol
# 2 = move character --> sent by a player when they move to update the position of them for eveyone else
# 3 = chat event
# 4 = damageevent --> damage player or object
# 5 = add object --> tells all clients to add a new object to the game
# 6 = delete object --> deletes object form the game

# ---------- helpers ----------



def _recv_exact(sock, n):
    data = b""
    while len(data) < n:
        chunk = sock.recv(n - len(data))
        if not chunk:
            return None
        data += chunk
    return data


# ---------- client ----------

class Client:
    def __init__(self, host, port):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect((host, port))

        self.incoming = queue.Queue()
        self.running = True

        threading.Thread(target=self._listen, daemon=True).start()

    def _listen(self):
        buffer = b""
        while self.running:
            try:
                data = self.s.recv(4096)
                if not data:
                    break

                buffer += data

                while b"\n" in buffer:
                    packet, buffer = buffer.split(b"\n", 1)
                    msg = json.loads(packet.decode())
                    self.incoming.put(msg)

            except:
                break

    def send(self, payload):
        self.s.sendall((json.dumps(payload) + "\n").encode())

    def poll(self):
        """Non-blocking receive"""
        messages = []
        while not self.incoming.empty():
            messages.append(self.incoming.get())
        return messages

    def close(self):
        self.running = False
        self.s.close()


# ---------- server ----------

class Server:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.clients = []  # list of (socket, address)
        self.lock = threading.Lock()

        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.s.bind((self.host, self.port))
        self.s.listen()
        print(f"Server listening on {self.host}:{self.port}")

        threading.Thread(target=self.accept_loop, daemon=True).start()

    def wait_for_client(self):
        while True:
            with self.lock:
                if len(self.clients) > 0:
                    return
            time.sleep(0.01)

    def accept_loop(self):
        while True:
            conn, addr = self.s.accept()
            print(f"New connection: {addr}")
            with self.lock:
                self.clients.append((conn, addr))
            threading.Thread(target=self.client_thread, args=(conn, addr), daemon=True).start()

    def client_thread(self, conn, addr):
        # handle this client
        try:
            while True:
                data = self.recv_message(conn)
                if data is None:
                    break
                print(f"[{addr}] {data}")
                # Example: broadcast to all other clients
                self.send_all(f"{addr} says: {data}", exclude=conn)
        finally:
            with self.lock:
                self.clients = [(c,a) for (c,a) in self.clients if c != conn]
            conn.close()
            print(f"Connection closed: {addr}")

    # ----- helper functions -----
    def send_all(self, data, exclude=None):
        # send to all clients, optionally excluding one
        with self.lock:
            for c, _ in self.clients:
                if c != exclude:
                    self.send_message(c, data)

    def send_message(self, conn, data):
        payload = data.encode()
        length = len(payload).to_bytes(4, "big")
        conn.sendall(length + payload)

    def recv_message(self, conn):
        # length-prefixed receive
        length_bytes = self._recv_exact(conn, 4)
        if length_bytes is None:
            return None
        length = int.from_bytes(length_bytes, "big")
        payload = self._recv_exact(conn, length)
        if payload is None:
            return None
        return payload.decode()

    @staticmethod
    def _recv_exact(conn, n):
        data = b""
        while len(data) < n:
            chunk = conn.recv(n - len(data))
            if not chunk:
                return None
            data += chunk
        return data
