#
# BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2005 Michael "ThorN" Thornton
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301 USA
#
# CHANGELOG
#
# 2010/07/23 - xlr8or - 1.0.1 - fixed infinite loop in a python socket thread in receive_packet() on gameserver restart
# 2014/08/05 - Fenix  - 1.1   - syntax cleanup

__version__ = '1.1'

import socket

from struct import *

try:
    from hashlib import md5 as newmd5
except ImportError:
    # for Python versions < 2.5
    from md5 import new as newmd5


def EncodeHeader(isFromServer, isResponse, sequence):
    header = sequence & 0x3fffffff
    if isFromServer:
        header += 0x80000000
    if isResponse:
        header += 0x40000000
    return pack('<I', header)


def DecodeHeader(data):
    [header] = unpack('<I', data[0 : 4])
    return [header & 0x80000000, header & 0x40000000, header & 0x3fffffff]


def EncodeInt32(size):
    return pack('<I', size)


def DecodeInt32(data):
    return unpack('<I', data[0 : 4])[0]
    
    
def EncodeWords(words):
    size = 0
    encodedWords = ''
    for word in words:
        strWord = str(word)
        encodedWords += EncodeInt32(len(strWord))
        encodedWords += strWord
        encodedWords += '\x00'
        size += len(strWord) + 5
    
    return size, encodedWords


def DecodeWords(size, data):
    numWords = DecodeInt32(data[0:])
    words = []
    offset = 0
    while offset < size:
        wordLen = DecodeInt32(data[offset : offset + 4])        
        word = data[offset + 4 : offset + 4 + wordLen]
        words.append(word)
        offset += wordLen + 5

    return words


def EncodePacket(isFromServer, isResponse, sequence, words):
    encodedHeader = EncodeHeader(isFromServer, isResponse, sequence)
    encodedNumWords = EncodeInt32(len(words))
    [wordsSize, encodedWords] = EncodeWords(words)
    encodedSize = EncodeInt32(wordsSize + 12)
    return encodedHeader + encodedSize + encodedNumWords + encodedWords


def DecodePacket(data):
    """
    Decode a request or response packet.
    Return format is:
    [is_from_server, is_response, sequence, words]
    where
        is_from_server = the command in this command/response packet pair originated on the server
        is_response = True if this is a response, False otherwise
        sequence = sequence number
        words = list of words
    """
    [isFromServer, isResponse, sequence] = DecodeHeader(data)
    wordsSize = DecodeInt32(data[4:8]) - 12
    words = DecodeWords(wordsSize, data[12:])
    return [isFromServer, isResponse, sequence, words]

clientSequenceNr = 0

def EncodeClientRequest(words):
    """
    Encode a request packet.
    """
    global clientSequenceNr
    packet = EncodePacket(False, False, clientSequenceNr, words)
    clientSequenceNr = (clientSequenceNr + 1) & 0x3fffffff
    return packet

    
def EncodeClientResponse(sequence, words):
    """
    Encode a response packet.
    """
    return EncodePacket(True, True, sequence, words)


def printPacket(packet):
    """
    Display contents of packet in user-friendly format, useful for debugging purposes.
    """
    if packet[0]:
        print "IsFromServer, ",
    else:
        print "IsFromClient, ",
    
    if packet[1]:
        print "Response, ",
    else:
        print "Request, ",

    print "Sequence: " + str(packet[2]),

    if packet[3]:
        print " Words:",
        for word in packet[3]:
            print "\"" + word + "\"",

    print ""


def generatePasswordHash(salt, password):
    m = newmd5()
    m.update(salt)
    m.update(password)
    return m.digest()
    

def containsCompletePacket(data):
    if len(data) < 8:
        return False
    if len(data) < DecodeInt32(data[4:8]):
        return False
    return True


def receivePacket(_socket, receiveBuffer):
    """
    Wait until the local receive buffer contains a full packet (appending data from the network socket),
    then split receive buffer into first packet and remaining buffer data
    """
    while not containsCompletePacket(receiveBuffer):
        data = _socket.recv(4096)  # was 16384
        # make sure we raise a socket error when the socket is hanging
        # on a loose end (receiving no data after server restart)
        if not data:
            raise socket.error('no data received: remote end unexpectedly closed socket')
        receiveBuffer += data

    packetSize = DecodeInt32(receiveBuffer[4:8])
    packet = receiveBuffer[0:packetSize]
    receiveBuffer = receiveBuffer[packetSize:len(receiveBuffer)]

    return [packet, receiveBuffer]

########################################################################################################################
# EXAMPLE PROGRAM
########################################################################################################################
# if __name__ == '__main__':
#
#     import sys
#     import string
#
#     from getopt import getopt
#
#     print "Remote administration event listener for BFBC2"
# # history_file = os.path.join( os.environ["HOME"], ".bfbc2_rcon_history" )
#
#     host = None
#     port = None
#     pw = None
#     serverSocket = None
#
#     opts, args = getopt(sys.argv[1:], 'h:p:e:a:')
#     for k, v in opts:
#         if k == '-h':
#             host = v
#         elif k == '-p':
#             port = int(v)
#         elif k == '-a':
#             pw = v
#
#     if not host:
#         host = raw_input('Enter game server host IP/name: ')
#     if not port:
#         port = int(raw_input('Enter host port: '))
#     if not pw:
#         pw = raw_input('Enter password: ')
#
#     try:
#         serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#
#         print 'Connecting to port: %s:%d...' % ( host, port )
#         serverSocket.connect( ( host, port ) )
#         serverSocket.setblocking(1)
#         receiveBuffer = ''
#
#         print 'Logging in - 1: retrieving salt...'
#
#         # Retrieve this connection's 'salt' (magic value used when encoding password) from server
#         getPasswordSaltRequest = EncodeClientRequest( [ "login.hashed" ] )
#         serverSocket.send(getPasswordSaltRequest)
#
#         [getPasswordSaltResponse, receiveBuffer] = receivePacket(serverSocket, receiveBuffer)
#         printPacket(DecodePacket(getPasswordSaltResponse))
#
#         [isFromServer, isResponse, sequence, words] = DecodePacket(getPasswordSaltResponse)
#
#         # if the server doesn't understand "login.hashed" command, abort
#         if words[0] != "OK":
#             sys.exit(0);
#
#         print 'Received salt: ' + words[1]
#
#         # Given the salt and the password, combine them and compute hash value
#         salt = words[1].decode("hex")
#         passwordHash = generatePasswordHash(salt, pw)
#         passwordHashHexString = string.upper(passwordHash.encode("hex"))
#
#         print 'Computed password hash: ' + passwordHashHexString
#
#         # Send password hash to server
#         print 'Logging in - 2: sending hash...'
#
#         loginRequest = EncodeClientRequest( [ "login.hashed", passwordHashHexString ] )
#         serverSocket.send(loginRequest)
#
#         [loginResponse, receiveBuffer] = receivePacket(serverSocket, receiveBuffer)
#
#         printPacket(DecodePacket(loginResponse))
#
#         [isFromServer, isResponse, sequence, words] = DecodePacket(loginResponse)
#
#         # if the server didn't like our password, abort
#         if words[0] != "OK":
#             sys.exit(0);
#
#         print 'Logged in.'
#
#         print 'Enabling events...'
#
#         enableEventsRequest = EncodeClientRequest( [ "eventsEnabled", "true" ] )
#         serverSocket.send(enableEventsRequest)
#
#         [enableEventsResponse, receiveBuffer] = receivePacket(serverSocket, receiveBuffer)
#         printPacket(DecodePacket(enableEventsResponse))
#
#         [isFromServer, isResponse, sequence, words] = DecodePacket(enableEventsResponse)
#
#         # if the server didn't know about the command, abort
#         if words[0] != "OK":
#             sys.exit(0);
#
#         print 'Now waiting for events.'
#
#         while True:
#             # Wait for packet from server
#             [packet, receiveBuffer] = receivePacket(serverSocket, receiveBuffer)
#
#             [isFromServer, isResponse, sequence, words] = DecodePacket(packet)
#
#             # If this was a command from the server, we should respond to it
#             # For now, we always respond with an "OK"
#             if not isResponse:
#                 response = EncodeClientResponse(sequence, ["OK"])
#                 serverSocket.send(response)
#             else:
#                 print 'Received an unexpected response packet from server, ignoring:'
#
#             printPacket(DecodePacket(packet))
#
#
#     except socket.error, detail:
#         print 'Network error:', detail[1]
#
#     except EOFError, KeyboardInterrupt:
#         pass
#
#     except:
#         raise