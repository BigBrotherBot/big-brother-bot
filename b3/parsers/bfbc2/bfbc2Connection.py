
import time
import socket
from b3.parsers.bfbc2.EventConsole import *

class Bfbc2Exception(Exception): pass
class Bfbc2BadPasswordException(Bfbc2Exception): pass
class Bfbc2BadCommandException(Bfbc2Exception): pass

class Bfbc2Connection(object):
    
    _serverSocket = None
    _host = None
    _port = None
    _password = None

    _maxShortRetryCount = 10
    _maxLongRetryCount = 10
    _delayBetweenLongRetry = 5 # seconds

    def __init__(self, host, port, password):
        
        self._host = host
        self._port = port
        self._password = password
        
        self._connect()
        self._auth()
   
    def _connect(self):
        self._serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._serverSocket.connect( ( self._host, self._port ) )
        self._serverSocket.setblocking(1)

    def sendRequest(self, command, *args):
        words = [command]
        words += args
        request = EncodeClientRequest(words)
        printPacket(DecodePacket(request))
        self._serverSocket.send(request)
        response = self._serverSocket.recv(4096)
        decodedResponse = DecodePacket(response)
        printPacket(decodedResponse)
        #[isFromServer, isResponse, sequence, words] = DecodePacket(response)
        return decodedResponse
        
    def _auth(self):
        # Retrieve this connection's 'salt' (magic value used when encoding password) from server
        response = self.sendRequest("login.hashed")
        [isFromServer, isResponse, sequence, words] = response

        # if the server doesn't understand "login.hashed" command, abort
        if words[0] != "OK":
            raise Bfbc2Exception("Could not retrieve salt")

        # Given the salt and the password, combine them and compute hash value
        salt = words[1].decode("hex")
        passwordHash = generatePasswordHash(salt, self._password)
        passwordHashHexString = string.upper(passwordHash.encode("hex"))

        # Send password hash to server
        loginResponse = self.sendRequest("login.hashed", passwordHashHexString)
        [isFromServer, isResponse, sequence, words] = loginResponse

        # if the server didn't like our password, abort
        if words[0] != "OK":
            raise Bfbc2BadPasswordException("The BFBC2 server refused our password")

            
    def subscribeToBfbc2Events(self):
        """
        tell the bfbc2 server to send us events
        """
        response = self.sendRequest("eventsEnabled", "true")
        [isFromServer, isResponse, sequence, words] = response

        # if the server didn't know about the command, abort
        if words[0] != "OK":
            raise Bfbc2BadCommandException()

        
    def waitForEvent(self):
        # Wait for packet from server
        packet = self._serverSocket.recv(4096)    
        [isFromServer, isResponse, sequence, words] = DecodePacket(packet)
        printPacket(DecodePacket(packet))
        
        # If this was a command from the server, we should respond to it
        # For now, we always respond with an "OK"
        if isResponse:
            print 'Received an unexpected response packet from server, ignoring'
            return self.waitForEvent()
        else:
            response = EncodeClientResponse(sequence, ["OK"])
            printPacket(DecodePacket(response))
            self._serverSocket.send(response)
            return words
            

        


###################################################################################
# Display contents of packet in user-friendly format, useful for debugging purposes
def printPacket(packet):

    if (packet[0]):
        print ">",
    else:
        print "<",
    
    if (packet[1]):
        print "R",
    else:
        print "Q",

    print "(%s)" %  packet[2],

    if packet[3]:
        print " :",
        for word in packet[3]:
            print "\"" + word + "\"",

    print ""
    
###################################################################################
# Example program

if __name__ == '__main__':
    import sys

    bc2server = Bfbc2Connection('xxx.xxx.xxx.xxx', 48888, 'xxxxxx')
    
    