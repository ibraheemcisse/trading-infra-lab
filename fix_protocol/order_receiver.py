import socket
import simplefix

HOST = "0.0.0.0"
PORT = 9876


def get_field(msg, tag):
    value = msg.get(tag)
    if value is None:
        return None
    if isinstance(value, bytes):
        return value.decode("ascii", errors="replace")
    return str(value)


def print_order(msg):
    clordid = get_field(msg, 11)
    symbol  = get_field(msg, 55)
    side    = get_field(msg, 54)
    qty     = get_field(msg, 38)
    price   = get_field(msg, 44)

    side_name = {"1": "BUY", "2": "SELL"}.get(side, side)

    print("\nReceived NewOrderSingle")
    print(f"  ClOrdID : {clordid}")
    print(f"  Symbol  : {symbol}")
    print(f"  Side    : {side_name}")
    print(f"  Qty     : {qty}")
    print(f"  Price   : {price}")


def main():
    parser = simplefix.FixParser()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((HOST, PORT))
        server.listen(1)

        print(f"FIX receiver listening on port {PORT}...")

        conn, addr = server.accept()

        with conn:
            print(f"Connection from {addr[0]}:{addr[1]}")
            print("-" * 40)

            while True:
                data = conn.recv(4096)
                if not data:
                    print("\nClient disconnected")
                    break

                parser.append_buffer(data)

                while True:
                    msg = parser.get_message()
                    if msg is None:
                        break

                    msg_type = get_field(msg, 35)

                    if msg_type == "D":
                        print_order(msg)
                    else:
                        print(f"Received message type={msg_type}")


if __name__ == "__main__":
    main()
