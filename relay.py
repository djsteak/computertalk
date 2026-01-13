# ⚠ ⚠ ⚠ THIS FILE SHOULD NOT BE RUN UNLESS YOU KNOW WHAT YOU ARE DOING ⚠ ⚠ ⚠


import socket
import threading
import json
import uuid

HOST = "0.0.0.0"
PORT = 34197

clients = {}  # id -> socket
lock = threading.Lock()

def handle_client(conn, addr):
    client_id = str(uuid.uuid4())
    with lock:
        clients[client_id] = conn

    print(f"{client_id} connected from {addr}")

    try:
        while True:
            data = conn.recv(4096)
            if not data:
                break

            message = json.loads(data.decode())
            message["from"] = client_id

            broadcast(message, exclude=client_id)

    except Exception as e:
        print("error:", e)

    finally:
        with lock:
            del clients[client_id]
        conn.close()
        print(f"{client_id} disconnected")

def broadcast(message, exclude=None):
    packet = json.dumps(message).encode()
    with lock:
        for cid, sock in clients.items():
            if cid != exclude:
                try:
                    sock.sendall(packet)
                except:
                    pass

def main():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((HOST, PORT))
    s.listen()
    print("Relay server listening...")

    while True:
        conn, addr = s.accept()
        threading.Thread(
            target=handle_client,
            args=(conn, addr),
            daemon=True
        ).start()

if __name__ == "__main__":
    main()
