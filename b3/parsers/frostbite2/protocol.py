#!/usr/local/bin/python

# Changelog
# 2010/07/23 - xlr8or - v1.0.1
# * fixed infinite loop in a python socket thread in receivePacket() on gameserver restart

__version__ = '1.0.1'

import logging
from struct import pack, unpack
import time
import asyncore
import socket
import threading
import hashlib

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
# isFromServer = the command in this command/response packet pair originated on the server
#     isResponse = True if this is a response, False otherwise
#     sequence = sequence number
#     words = list of words
    
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
    return EncodePacket(True, True, sequence, words)


###################################################################################
# Display contents of packet in user-friendly format, useful for debugging purposes
    
def printPacket(packet):

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

###################################################################################

def generatePasswordHash(salt, password):
    m = hashlib.new('md5')
    m.update(salt)
    m.update(password)
    return m.digest()
    
###################################################################################

def containsCompletePacket(data):
    if len(data) < 8:
        return False
    if len(data) < DecodeInt32(data[4:8]):
        return False
    return True

# Wait until the local receive buffer contains a full packet (appending data from the network socket),
# then split receive buffer into first packet and remaining buffer data
    
def receivePacket(_socket, receiveBuffer):

    while not containsCompletePacket(receiveBuffer):
        data = _socket.recv(4096) #was 16384
        #Make sure we raise a socket error when the socket is hanging on a loose end (receiving no data after server restart) 
        if not data:
            raise socket.error('No data received - Remote end unexpectedly closed socket')
        receiveBuffer += data

    packetSize = DecodeInt32(receiveBuffer[4:8])

    packet = receiveBuffer[0:packetSize]
    receiveBuffer = receiveBuffer[packetSize:len(receiveBuffer)]

    return [packet, receiveBuffer]

#####################################################################################
class FrostbiteError(Exception): pass

class CommandError(FrostbiteError): pass
class CommandTimeoutError(CommandError): pass
class CommandFailedError(CommandError): pass

class NetworkError(FrostbiteError): pass

class FrostbiteDispatcher(asyncore.dispatcher_with_send):

    def __init__(self, host, port):
        asyncore.dispatcher_with_send.__init__(self)
        self._buffer_in = ''
        self.getLogger().info("connecting")
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        asyncore.dispatcher_with_send.connect(self, (host, port))
        self._frostbite_event_handler = None
        self._frostbite_command_response_handler = None

    #===============================================================================
    # 
    #        Public API
    #    
    #===============================================================================

    def set_frostbite_event_hander(self, func):
        """register a function that will be called when the Frosbite server
        sends us a game event."""
        self._frostbite_event_handler = func

    def set_frostbite_command_response_handler(self, func):
        """register a function that will be called when the Frosbite server
        sends us a command reply."""
        self._frostbite_command_response_handler = func
        
    def send_command(self, *command):
        """Send a command to the Frosbite server and return the command id
        which can be used to find the matching reply later on."""
        self.getLogger().info("command : %s " % repr(command))
        if len(command) == 1 and type(command[0]) == tuple:
            words = command[0]
        else:
            words = command
        request = EncodeClientRequest(words)
        [sequence, words] = DecodePacket(request)[2:]

        self.getLogger().debug("sending command request #%i: %s " % (sequence, words))
        asyncore.dispatcher_with_send.send(self, request)

        return sequence

    #===========================================================================
    # 
    # Other methods
    # 
    #===========================================================================

    def getLogger(self):
        return logging.getLogger("FrostbiteDispatcher")
    
    def handle_connect(self):
        self.getLogger().debug("handle_connect")
    
    def handle_close(self):
        """Called when the socket is closed."""
        self.getLogger().debug("handle_close")
        self.close()

    def handle_read(self):
        """Called when the asynchronous loop detects that a read() call on the channel's socket will succeed."""
        # received raw data
        data = self.recv(8192)
        self._buffer_in += data
        self.getLogger().debug('read %s char from Frostbite2 gameserver' % len(data))

        # cook it into Frosbite packets
        while containsCompletePacket(self._buffer_in):
            packetSize = DecodeInt32(self._buffer_in[4:8])
            packet = self._buffer_in[0:packetSize]
            self._buffer_in = self._buffer_in[packetSize:len(self._buffer_in)]
            self.handle_packet(packet)
            
    def handle_packet(self, packet):
        """Called when a full Frosbite packet has been received."""
        [originServer, isResponse, sequence, words] = DecodePacket(packet)
        self.getLogger().info("handle_packet(%s)" % repr([originServer, isResponse, sequence, words]))
        if not isResponse:
            # acknowledge the server
            self.send(EncodePacket(originServer, True, sequence, ("OK",)))
        if originServer:
            if isResponse:
                self.getLogger().warn("received a bad packet from frosbite server pretending being a response for a server request. %s" % repr(packet))
            else:
                self.handle_frostbite_event(words)
        else:
            if isResponse:
                self.handle_frostbite_command_response(sequence, words)
            else:
                self.getLogger().warn("received a bad packet from frosbite server pretending being a request from us. %s" % repr(DecodePacket(packet)))

    def handle_frostbite_event(self, words):
        self.getLogger().debug("received a game event from frosbite server. %s" % repr(words))
        if self._frostbite_event_handler is not None:
            self._frostbite_event_handler(words)

    def handle_frostbite_command_response(self, command_id, words):
        self.getLogger().debug("received a response for command #%i from frosbite server. %s" % (command_id, repr(words)))
        if self._frostbite_command_response_handler is not None:
            self._frostbite_command_response_handler(command_id, words)
    
    

class FrostbiteServer(threading.Thread):
    """thread opening a connection to a Frostbite game server and providing
    means of observing Frostbite events and sending commands"""
    def __init__(self, host, port, password=None, command_timeout=5.0):
        threading.Thread.__init__(self, name="FrosbiteServerThread")
        self.frostbite_dispatcher = FrostbiteDispatcher(host, port)
        self._stopEvent = threading.Event()
        self.password = password
        self.command_timeout = command_timeout
        self.frostbite_dispatcher.set_frostbite_event_hander(self._on_event)
        self.frostbite_dispatcher.set_frostbite_command_response_handler(self._on_command_response)
        self.pending_commands = {}
        self.__command_reply_event = threading.Event()
        self.observers = set()
        # test connection
        sock = socket.create_connection((host, port), timeout=2)
        sock.close()
        # ok start working
        self.start()
        time.sleep(1.5)

    #===============================================================================
    # 
    #    Public API
    #
    #===============================================================================

    def subscribe(self, func):
        """Add func from Frosbite events listeners."""
        self.observers.add(func)
        
    def unsubscribe(self, func):
        """Remove func from Frosbite events listeners."""
        self.observers.remove(func)

    def command(self, *command):
        """send command to the Frostbite server in a synchronous way.
        Calling this method will block until we receive the reply packet from the
        game server or until we reach the timeout.
        """
        if not self.connected:
            raise NetworkError("not connected")
        
        self.getLogger().info("command : %s " % repr(command))
        if command is None:
            return None

        command_id = self.frostbite_dispatcher.send_command(*command)
        self.pending_commands[command_id] = None
        self.getLogger().debug("command #%i sent. %s " % (command_id, repr(command)))
        
        response = self._wait_for_response(command_id)
        if response[0] != "OK":
            raise CommandFailedError(response)
        else:
            return response[1:]

    def auth(self):
        """authenticate on the Frosbite server with given password"""
        self.getLogger().info("starting authentication")
        hash_token = self.command('login.hashed')
        # Given the salt and the password, combine them and compute hash value
        salt = hash_token[0].decode("hex")
        passwordHash = generatePasswordHash(salt, self.password)
        passwordHashHexString = passwordHash.encode("hex").upper()
        # Send password hash to server
        self.command("login.hashed", passwordHashHexString)
        self.getLogger().info("authentication done")

    def close(self):
        self.frostbite_dispatcher.close()

    def stop(self):
        self._stopEvent.set()
        self.close()
    
    #===============================================================================
    # 
    # Other methods
    #
    #===============================================================================

    def __getattr__(self, name):
        if name == 'connected':
            return self.frostbite_dispatcher.connected
        else:
            raise AttributeError

    def getLogger(self):
        return logging.getLogger("FrostbiteServer")

    def isStopped(self):
        return self._stopEvent.is_set()

    def run(self):
        """Threaded code"""
        self.getLogger().info('start loop')
        try:
            while not self.isStopped():
                asyncore.loop(count=1, timeout=1)
        except KeyboardInterrupt:
            pass
        finally:
            self.frostbite_dispatcher.close()
        self.getLogger().info('end loop')

    def _on_event(self, words):
        self.getLogger().debug("received Frostbite event : %s" % repr(words))
        for func in self.observers:
            func(words)

    def _on_command_response(self, command_id, words):
        self.getLogger().debug("received Frostbite command #%i response : %s" % (command_id, repr(words)))
        if command_id not in self.pending_commands:
            self.getLogger().warn("dropping Frostbite command #%i response as we are not waiting for it anymore" % command_id)
        else:
            self.pending_commands[command_id] = words
            self.__command_reply_event.set()


    def _wait_for_response(self, command_id):
        """block until response to for given command_id has been received or until timeout is reached."""
        expire_time = time.time() + self.command_timeout
        while not self.isStopped() and command_id in self.pending_commands and self.pending_commands[command_id] is None:
            if not self.connected:
                raise NetworkError("Lost connection to Frostbite2 server")
            if time.time() >= expire_time:
                del self.pending_commands[command_id]
                raise CommandTimeoutError("Did not receive any response for sequence #%i." % command_id)
            self.getLogger().debug("waiting for some command reply #%i : %r " % (command_id, self.pending_commands))
            self.__command_reply_event.clear()
            self.__command_reply_event.wait(self.command_timeout)
        try:
            response = self.pending_commands[command_id]
            del self.pending_commands[command_id]
            return response
        except KeyError:
            raise CommandTimeoutError("Did not receive any response for sequence #%i." % command_id)



###################################################################################
# Example program

if __name__ == '__main__':
    from getopt import getopt
    import sys

    print "Remote administration event listener for Frosbite"
    # history_file = os.path.join( os.environ["HOME"], ".bfbc2_rcon_history" )

    host = None
    port = None
    pw = None
    serverSocket = None

    opts, args = getopt(sys.argv[1:], 'h:p:e:a:')
    for k, v in opts:
        if k == '-h':
            host = v
        elif k == '-p':
            port = int(v)
        elif k == '-a':
            pw = v
    
    if not host:
        host = raw_input('Enter game server host IP/name: ')
    if not port:
        port = int(raw_input('Enter host port: '))
    if not pw:
        pw = raw_input('Enter password: ')


    def run_low_level():
        try:
            serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
            print 'Connecting to port: %s:%d...' % ( host, port )
            serverSocket.connect( ( host, port ) )
            serverSocket.setblocking(1)
            receiveBuffer = ''
    
            print 'Logging in - 1: retrieving salt...'
    
            # Retrieve this connection's 'salt' (magic value used when encoding password) from server
            getPasswordSaltRequest = EncodeClientRequest( [ "login.hashed" ] )
            serverSocket.send(getPasswordSaltRequest)
    
            [getPasswordSaltResponse, receiveBuffer] = receivePacket(serverSocket, receiveBuffer)
            printPacket(DecodePacket(getPasswordSaltResponse))
    
            [isResponse, sequence, words] = DecodePacket(getPasswordSaltResponse)[1:]
    
            # if the server doesn't understand "login.hashed" command, abort
            if words[0] != "OK":
                sys.exit(0)
    
            print 'Received salt: ' + words[1]
    
            # Given the salt and the password, combine them and compute hash value
            salt = words[1].decode("hex")
            passwordHash = generatePasswordHash(salt, pw)
            passwordHashHexString = passwordHash.encode("hex").upper()
    
            print 'Computed password hash: ' + passwordHashHexString
            
            # Send password hash to server
            print 'Logging in - 2: sending hash...'
    
            loginRequest = EncodeClientRequest( [ "login.hashed", passwordHashHexString ] )
            serverSocket.send(loginRequest)
    
            [loginResponse, receiveBuffer] = receivePacket(serverSocket, receiveBuffer)
    
            printPacket(DecodePacket(loginResponse))
    
            [isResponse, sequence, words] = DecodePacket(loginResponse)[1:]
    
            # if the server didn't like our password, abort
            if words[0] != "OK":
                sys.exit(0)
    
            print 'Logged in.'
            
            print 'Enabling events...'
        
            enableEventsRequest = EncodeClientRequest(("admin.eventsEnabled", "true"))
            serverSocket.send(enableEventsRequest)
    
            [enableEventsResponse, receiveBuffer] = receivePacket(serverSocket, receiveBuffer)
            printPacket(DecodePacket(enableEventsResponse))
    
            [isResponse, sequence, words] = DecodePacket(enableEventsResponse)[1:]
    
            # if the server didn't know about the command, abort
            if words[0] != "OK":
                sys.exit(0)
            
            print 'Now waiting for events.'
    
            while True:
                # Wait for packet from server
                [packet, receiveBuffer] = receivePacket(serverSocket, receiveBuffer)
    
                [isResponse, sequence, words] = DecodePacket(packet)[1:]
    
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
    
        except (EOFError, KeyboardInterrupt):
            pass
    
        except:
            raise


    def run_FrosbiteServer():
        from b3.output import OutputHandler
        
        FORMAT = "%(name)-20s [%(thread)-4d] %(threadName)-15s %(levelname)-8s %(message)s"
        handler = logging.StreamHandler()
        formatter = logging.Formatter(FORMAT)
        handler.setFormatter(formatter)
        
        myConsole = OutputHandler('console')
        myConsole.addHandler(handler)
        myConsole.setLevel(logging.NOTSET)
        
        #logging.getLogger('FrostbiteServer').addHandler(handler)
        #logging.getLogger('FrostbiteDispatcher').addHandler(handler)

        def frosbiteEventListener(words):
            myConsole.console(">>> %s" % words)    
                

        from random import sample, random
        class CommandRequester(threading.Thread):
            _stop = threading.Event()
            nb_instances = 0
            def __init__(self, frostbite_server, commands=('serverInfo',), delay=5):
                self.__class__.nb_instances += 1
                threading.Thread.__init__(self, name="CommandRequester%s" % self.__class__.nb_instances)
                self.frostbite_server = frostbite_server
                self.commands = commands
                self.delay = delay

            def getLogger(self):
                return logging.getLogger("CommandRequester")
            
            def run(self):
                self.getLogger().info("starting spamming commands")
                while not self.__class__._stop.is_set():
                    cmd = sample(self.commands, 1)[0]
                    self.getLogger().info("###\trequesting \t%s" % repr(cmd))
                    try:
                        response = self.frostbite_server.command(cmd)
                        self.getLogger().info("###\treceived \t%s" % repr(response))
                    except CommandFailedError, err:
                        self.getLogger().info("###\treceived \t%s" % repr(err.message))
                    time.sleep(self.delay + random())
                self.getLogger().info("stopped spamming commands")

            @classmethod
            def stopAll(cls):
                cls._stop.set()

        logging.basicConfig(level=logging.NOTSET, format=FORMAT)
        logging.info("here we go")
                    
        t_conn = FrostbiteServer(host, port, pw)
        t_conn.subscribe(frosbiteEventListener)

#        try:
#            t_conn.command('logout')
#        except CommandError, err:
#            logging.error(err)
        try:
            t_conn.auth()
            t_conn.command('admin.eventsEnabled', 'true')
        except FrostbiteError, err:
            logging.error(err)

        time.sleep(1)
        CommandRequester(t_conn).start()
        time.sleep(.5)
        CommandRequester(t_conn, ('version', ('listPlayers', 'all'), 'serverInfo', 'login.plainText')).start()
#        time.sleep(.5)
#        CommandRequester(t_conn, ('version', ('listPlayers', 'all'), 'serverInfo', ('login.plainText', 'faux password'), 'login.plainText')).start()
#        time.sleep(.5)
#        CommandRequester(t_conn, ('version', ('listPlayers', 'all'), 'serverInfo', ('login.plainText', 'faux password'), 'login.plainText')).start()
#        time.sleep(.5)
#        CommandRequester(t_conn, ('version', ('listPlayers', 'all'), 'serverInfo', ('login.plainText', 'faux password'), 'login.plainText')).start()
#        time.sleep(.5)
#        CommandRequester(t_conn, ('version', ('listPlayers', 'all'), 'serverInfo', ('login.plainText', 'faux password'), 'login.plainText')).start()
#        time.sleep(.5)
#        CommandRequester(t_conn, ('version', ('listPlayers', 'all'), 'serverInfo', ('login.plainText', 'faux password'), 'login.plainText')).start()
#        time.sleep(.5)
#        CommandRequester(t_conn, (('login.plainText', 'faux password'), 'login.plainText')).start()
#        time.sleep(.5)
#        CommandRequester(t_conn, ('version', ('listPlayers', 'all'), 'serverInfo', ('login.plainText', 'faux password'), 'login.plainText')).start()
#        time.sleep(.5)
#        CommandRequester(t_conn, ('version', ('listPlayers', 'all'), 'serverInfo', ('login.plainText', 'faux password'), 'login.plainText')).start()
#        time.sleep(.5)
#        CommandRequester(t_conn, ('version', ('listPlayers', 'all'), 'serverInfo', ('login.plainText', 'faux password'), 'login.plainText')).start()
#        time.sleep(.5)
#        CommandRequester(t_conn, (('login.plainText', 'faux password'), 'login.plainText')).start()
#        time.sleep(.5)
#        CommandRequester(t_conn, ('version', ('listPlayers', 'all'), 'serverInfo', ('login.plainText', 'faux password'), 'login.plainText')).start()
#        time.sleep(.5)
#        CommandRequester(t_conn, ('version', ('listPlayers', 'all'), 'serverInfo', ('login.plainText', 'faux password'), 'login.plainText')).start()
#        time.sleep(.5)
#        CommandRequester(t_conn, ('version', ('listPlayers', 'all'), 'serverInfo', ('login.plainText', 'faux password'), 'login.plainText')).start()
#        time.sleep(.5)
#        CommandRequester(t_conn, (('login.plainText', 'faux password'), 'login.plainText')).start()
        
        time.sleep(5)
        t_conn.stop()
        CommandRequester.stopAll()
        logging.info("here we die")

    #run_low_level()
    run_FrosbiteServer()
    