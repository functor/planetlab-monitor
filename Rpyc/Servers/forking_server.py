import sys
import os
from ServerUtils import serve_socket, create_listener_socket, DEFAULT_PORT


def serve_in_child(sock):
    """forks a child to run the server in. the parent doesnt wait() for the child, 
    so if you do a `ps`, you'll see zombies. but who cares. i used to do a doublefork()
    for that, but it's really meaningless. anyway, when the parent dies, the zombies
    die as well."""
    if os.fork() == 0:
        try:
            serve_socket(sock)
        finally:
            sys.exit()

def main(port = DEFAULT_PORT):
    sock = create_listener_socket(port)
    while True:
        newsock, name = sock.accept()
        serve_in_child(newsock)

if __name__ == "__main__":
    main()

    