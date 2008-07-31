from ServerUtils import DEFAULT_PORT, threaded_server


def main(port = DEFAULT_PORT):
    threaded_server(port)

if __name__ == "__main__":
    main()

