#!/usr/local/bin/python
from struct import *
import md5
import socket
import sys
import shlex
import string
import threading
import os


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

# Decode a request or response packet
# Return format is:
# [isFromServer, isResponse, sequence, words]
# where
#	isFromServer = the command in this command/response packet pair originated on the server
#   isResponse = True if this is a response, False otherwise
#   sequence = sequence number
#   words = list of words
	
def DecodePacket(data):
	[isFromServer, isResponse, sequence] = DecodeHeader(data)
	wordsSize = DecodeInt32(data[4:8]) - 12
	words = DecodeWords(wordsSize, data[12:])
	return [isFromServer, isResponse, sequence, words]

###############################################################################

clientSequenceNr = 0

# Encode a request packet

def EncodeClientRequest(words):
	global clientSequenceNr
	packet = EncodePacket(False, False, clientSequenceNr, words)
	clientSequenceNr = (clientSequenceNr + 1) & 0x3fffffff
	return packet

# Encode a response packet
	
def EncodeClientResponse(sequence, words):
	return EncodePacket(False, True, sequence, words)


###################################################################################
# Display contents of packet in user-friendly format, useful for debugging purposes
	
def printPacket(packet):

	if (packet[0]):
		print "IsFromServer, ",
	else:
		print "IsFromClient, ",
	
	if (packet[1]):
		print "Response, ",
	else:
		print "Request, ",

	print "Sequence: " + str(packet[2]),

	if packet[3]:
		print " Words:",
		for word in packet[3]:
			print "\"" + word + "\"",

	print ""

###################################################################################

def generatePasswordHash(salt, password):
	m = md5.new()
	m.update(salt)
	m.update(password)
	return m.digest()
	
###################################################################################
# Example program

if __name__ == '__main__':
	from getopt import getopt
	import sys

	print "Remote administration event listener for BFBC2"
#	history_file = os.path.join( os.environ["HOME"], ".bfbc2_rcon_history" )

	host = raw_input('Enter game server host IP/name: ')
	port = int(raw_input('Enter host port: '))
	pw = raw_input('Enter password: ')

	serverSocket = None

	opts, args = getopt(sys.argv[1:], 'h:p:e:a:')
	for k, v in opts:
		if k == '-h':
			host = v
		elif k == '-p':
			port = int(v)
		elif k == '-a':
			pw = v

	if not pw:
		pw = raw_input('Enter password: ')

	try:
		serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

		print 'Connecting to port: %s:%d...' % ( host, port )
		serverSocket.connect( ( host, port ) )
		serverSocket.setblocking(1)

		print 'Logging in - 1: retrieving salt...'

		# Retrieve this connection's 'salt' (magic value used when encoding password) from server
		getPasswordSaltRequest = EncodeClientRequest( [ "login.hashed" ] )
		serverSocket.send(getPasswordSaltRequest)

		getPasswordSaltResponse = serverSocket.recv(4096)
		printPacket(DecodePacket(getPasswordSaltResponse))

		[isFromServer, isResponse, sequence, words] = DecodePacket(getPasswordSaltResponse)

		# if the server doesn't understand "login.hashed" command, abort
		if words[0] != "OK":
			sys.exit(0);

		print 'Received salt: ' + words[1]

		# Given the salt and the password, combine them and compute hash value
		salt = words[1].decode("hex")
		passwordHash = generatePasswordHash(salt, pw)
		passwordHashHexString = string.upper(passwordHash.encode("hex"))

		print 'Computed password hash: ' + passwordHashHexString
		
		# Send password hash to server
		print 'Logging in - 2: sending hash...'

		loginRequest = EncodeClientRequest( [ "login.hashed", passwordHashHexString ] )
		serverSocket.send(loginRequest)

		loginResponse = serverSocket.recv(4096)	
		printPacket(DecodePacket(loginResponse))

		[isFromServer, isResponse, sequence, words] = DecodePacket(loginResponse)

		# if the server didn't like our password, abort
		if words[0] != "OK":
			sys.exit(0);

		print 'Logged in.'
		
		print 'Enabling events...'
	
		enableEventsRequest = EncodeClientRequest( [ "eventsEnabled", "true" ] )
		serverSocket.send(enableEventsRequest)

		enableEventsResponse = serverSocket.recv(4096)	
		printPacket(DecodePacket(enableEventsResponse))

		[isFromServer, isResponse, sequence, words] = DecodePacket(enableEventsResponse)

		# if the server didn't know about the command, abort
		if words[0] != "OK":
			sys.exit(0);
		
		print 'Now waiting for events.'

		while True:
			# Wait for packet from server
			packet = serverSocket.recv(4096)	

			[isFromServer, isResponse, sequence, words] = DecodePacket(packet)

			# If this was a command from the server, we should respond to it
			# For now, we always respond with an "OK"
			if not isResponse:
				response = EncodeClientResponse(sequence, ["OK"])
				serverSocket.send(response)
			else:
				print 'Received an unexpected response packet from server, ignoring:'

			printPacket(DecodePacket(packet))


	except socket.error, detail:
		print 'Network error:', detail[1]

	except EOFError, KeyboardInterrupt:
		pass

	except:
		raise