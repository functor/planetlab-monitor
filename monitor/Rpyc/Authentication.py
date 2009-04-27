"""
Challenge-Response authentication algorithm over channels: the client sends the
username, recvs a challenge, generates a response based on the challenge and 
password, sends it back to the server, which also calculates the expected response.
the server returns "WRONG" or "OKAY". this way the password is never sent over
the wire.

* servers should call the accept function over a channel, with a dict of 
(username, password) pairs.
* clients should call login over a channel, with the username and password
"""
import md5
import random

def get_bytes(num_bytes):
	ret = []
	for n in xrange(num_bytes):
		ret.append( chr(random.randint(0,255)) )
	return ''.join(ret)

def accept(chan, users):
    username = chan.recv()
    challenge = get_bytes(16)
    chan.send(challenge)
    response = chan.recv()
    if username not in users:
        chan.send("WRONG")
        return False
    expected_response = md5.new(users[username] + challenge).digest()
    if response != expected_response:
        chan.send("WRONG")
        return False
    chan.send("OKAY")
    return True

def login(chan, username, password):
    chan.send(username)
    challenge = chan.recv()
    response = md5.new(password + challenge).digest()
    chan.send(response)
    return chan.recv() == "OKAY"

