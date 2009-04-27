from ServerUtils import DEFAULT_PORT, threaded_server

#
# define user:password pairs of your own
#
users = {
    "johnnash" : "t3hgam3r",
    "tolkien" : "1ring",
    "yossarian" : "catch22",
}

def main(port = DEFAULT_PORT):
    threaded_server(port, authenticate = True, users = users)

if __name__ == "__main__":
    main()



