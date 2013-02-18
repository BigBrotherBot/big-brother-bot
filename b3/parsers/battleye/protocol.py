# coding=UTF-8
#
# BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2012 Courgette
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
#
# Changelog
# ---------
# 1.0.x - 82ndab-Bravo17
#   * implement BattlEye network protocol
#   * fully functional module that can connects to a BattlEye server, send commands, receive packets
#   * external function can subscribe to get notified of received packets (event, command full response or commands response parts)
# 1.1 - Courgette
#   * make sending command synchronous (does not block receiving events though)
#   * external functions subscribing will only be notified of BattlEye events (and won't receive command response packets)
#   * CommandTimeoutError will be raised if a command does not get any response in a timely manner
# 1.1.1 - 82ndab-Bravo17
#   * correct race condition
#
import sys
import logging
import time
import socket
from threading import Thread, Event, Lock
import binascii
import select
import Queue
from collections import deque

__author__ = '82ndab-Bravo17, Courgette'
__version__ = '1.11'

#####################################################################################
#
# USAGE :
#
"""
    def handle_event(data):
        print "EVENT RECEIVED: %s" % data

    conn = BattleyeServer("11.22.33.44", 2304, "*****")

    try:
        # register a function that will get notified of BattlEye events
        conn.subscribe(handle_event)

        # try a one command
        try:
            for line in conn.command('players').split('\n'):
                print "players response : " + line
        except CommandError, err:
            print "command failed : %s" % err

        # let it bake for some time so we can see eventual events being received
        time.sleep(60)
    finally:
        # stop the connection
        conn.stop()
"""
#
#   See fully functional program at the end of this module. To try it out, just run :
#      > c:\python27\python.exe battleye\protocol.py
#
#   and you will be prompted for the BattlEye server ip, port and password.
#
#####################################################################################


# tuple of BattlEye command for which we should not expect any response
COMMANDS_WITH_NO_RESPONSE = ('say', )

class BattleyeError(Exception): pass
class NetworkError(BattleyeError): pass
class CommandError(BattleyeError): pass
class CommandTimeoutError(CommandError): pass
class CommandFailedError(CommandError): pass


class BattleyeServer(Thread):

    def __init__(self, host, port, password):
        Thread.__init__(self, name="BattleyeServerThread")
        #self.logger = logging.getLogger(__name__)
        #hdlr = logging.FileHandler('G:/b3-182/arma/logs/battleye.log')
        #formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        #hdlr.setFormatter(formatter)
        #self.logger.addHandler(hdlr)
        #self.logger.setLevel(logging.DEBUG)
        self.host = host
        self.port = port
        self.password = password

        self.read_queue = Queue.Queue([]) # get here packets received
        self.write_queue = deque([]) # put here packets to be sent
        self.command_queue = Queue.Queue([]) # put here commands to be sent

        self.sent_data_seq = []
        self._multi_packet_response = {} # some responses comes in multiple parts which are hold in this dict

        self._command_lock = Lock() # only one command than be managed at once. The lock will be set when sending the command and released when a response is received or timeout
        self.pending_command = None # holds the current command we are waitting a response for
        self.pending_command_response = None # holds the current command full response once received
        self.__command_reply_event = Event() # thread event used to notify the thread waitting for a response that the response is available (saves CPU)
        self.command_timeout = 3 # after how long should the thread waitting for the command response decides that no response will ever come

        self.observers = set() # functions to call when a BattleEye event is received
        self._stopEvent = Event() # can make the threads stop


        self.server_thread = Thread(target=self.polling_thread, name="BE_polling")
        self.server_thread.setDaemon(True)
        self.server_thread.start()
        time.sleep(.5)

        self.getLogger().info("start running BattleyeServer")
        self.start()
        time.sleep(1)


    def polling_thread(self):
        """Starts a thread for reading/writing to the Battleye server."""
        self.getLogger().info("connecting to BattlEye server at %s:%s" % (self.host, self.port))
        self._isconnected = False
        self.server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server.connect((self.host, self.port))

        while not self.isStopped():
            #self.getLogger().debug("Is socket ready")
            readable, writable, exception = select.select([self.server],[self.server],[self.server], .5)
            
            if not exception:
                if readable:
                    try:
                        data, addr = self.server.recvfrom(8192)
                        self.read_queue.put(data)
                        self.getLogger().debug("Read data: %s" % repr(data))
                    except socket.error, (value,message): 
                        self.getLogger().error("Socket error %s %s" % (value, message))
                        self.stop()
                if writable:
                    if len(self.write_queue):
                        data = self.write_queue.popleft()
                        self.getLogger().debug("Data to send: %s" % repr(data))
                        try:
                            self.server.send(data)
                        except Exception, err:
                            self.getLogger().error("Data send error, trying again. %s" % err, exc_info=err)
                            self.write_queue.appendleft(data)
                        else:
                            #store seq_no, type, data
                            if data[7:8] == chr(1):
                                seq = ord(data[8:9])
                                self.getLogger().debug("Sent sequence was %s" % seq)
                                self.sent_data_seq.append(seq)
                time.sleep(.05)
            else:
                self.stop()
        self.getLogger().debug("Ending Polling Thread")



    def run(self):
        self.crc_error_count = 0
        self._isconnected = self.login()

        if self._isconnected:

            self.read_thread = Thread(target=self.reading_thread, name="BE_read")
            self.read_thread.setDaemon(True)
            self.read_thread.start()

            self.write_thread = Thread(target=self.writing_thread, name="BE_write")
            self.write_thread.setDaemon(True)
            self.write_thread.start()

        while self._isconnected and not self.isStopped():
            if self.crc_error_count > 10 or len(self.sent_data_seq) > 10:
                self.getLogger().debug('CRC Errors %s   Commands not replied to %s' % (self.crc_error_count, self.sent_data_seq))
                # 10 + consecutive crc errors or 10 commands not replied to
                self.stop()
            time.sleep(10)
        self.getLogger().debug("Ending Server Thread")


    def reading_thread(self):
        self.getLogger().info("Starting Reading Thread")
        while self._isconnected and not self.isStopped():
            try:
                packet = self.read_queue.get(timeout=2)
                type, sequence, data = self.decode_server_packet(packet)
                if type == 2:
                    # Acknowledge server message receipt
                    packet = self.encode_packet(2, sequence, None)
                    self.getLogger().debug("Server Message sequence was %s" % sequence)
                    self.write_queue.append(packet)
                    self._on_event(data.decode('UTF-8', 'replace'))
                elif type == 1:
                    #self.getLogger().debug('Command Response : %s' % repr(data))
                    try:
                        self.sent_data_seq.remove(sequence)
                    except ValueError:
                        pass
                    self.crc_error_count = 0
                    if data[0:1] == chr(0):
                        data = self._handle_multipacket_part(ord(data[1]), ord(data[2]), data[3:])
                    if data:
                        self._on_command_response(data.decode('UTF-8', 'replace'))
                elif type == 255:
                    #CRC Error
                    self.crc_error_count += 1
            except Queue.Empty:
                pass
            except Exception, err:
                self.getLogger().error("error in reading_thread", exc_info=err)
                
        self.getLogger().info("Ending Reading Thread")


    def writing_thread(self):
        self.getLogger().info("Starting Writing Thread")

        self.write_seq = 0
        self.last_write_time = time.time()

        def enqueue_packet(data):
            self.write_queue.append(self.encode_packet(1, self.write_seq, data))
            self.last_write_time = time.time()
            self.write_seq += 1
            if self.write_seq > 255:
                self.write_seq -= 256

        while self._isconnected and not self.isStopped():
            try:
                enqueue_packet(self.command_queue.get(timeout=2))
            except Queue.Empty:
                if self.last_write_time + 30 < time.time():
                    enqueue_packet(None) # keep connection alive
            except Exception, err:
                self.getLogger().error("error in writing_thread", exc_info=err)
        self.getLogger().info("Ending Writing Thread")


    def login(self):
        """authenticate on the Battleye server with given password"""
        self.getLogger().info("Starting Login")
        request =  self.encode_packet(0, None, self.password)
#        self.getLogger().debug(self.write_queue)
        self.write_queue.append(request)
#        self.getLogger().debug(self.write_queue)
        login_response = False
        t = time.time()
        logged_in = None
        while time.time() < t+3 and not login_response:
            try:
                packet = self.read_queue.get(timeout = 0.1)
                type, logged_in, data =  self.decode_server_packet(packet)
                self.getLogger().debug("login response was %s %s %s" % (type, logged_in, data))
                if type == chr(255):
                    self.getLogger().warning('Invalid packet')
                elif type == 0:
                    login_response = True
            except Queue.Empty:
                pass

        if login_response:
            if logged_in == 1:
                self.getLogger().info("Login Successful")
                return True
        else:
            self.getLogger().warning("Login Failed")
            return False


    def _disconnect(self):
        self.getLogger().info("Disconnecting")
        if self._isconnected:
            try:
                self.server.close()
            except:
                pass
            self._isconnected = False


    def command(self, cmd, timeout=None):
        if not cmd:
            return
        if not self._isconnected:
            raise NetworkError("not connected to BattlEye server")
        if self.isStopped():
            raise BattleyeError("BattlEyeServer stopped")


        self._command_lock.acquire() # this will eventually wait for the lock to be released
        try:
            if timeout or not any(filter(lambda x: cmd.startswith(x + ' '), COMMANDS_WITH_NO_RESPONSE)):
                return self._command_and_wait(cmd, timeout)
            else:
                return self._command_no_wait(cmd)
        except CommandTimeoutError:
            raise
        except BattleyeError:
            raise
        except Exception, err:
            type, value, traceback = sys.exc_info()
            raise CommandFailedError, ("command \"%s\" failed: %s" % (cmd, err), type, value), traceback
        finally:
            self._command_lock.release() # release the lock so another command can be sent


    def _command_no_wait(self, cmd):
        """send a command and do not expect any response"""
        self.command_queue.put(cmd)


    def _command_and_wait(self, cmd, timeout=None):
        """send command to the BattlEye server in a synchronous way.
        Calling this method will block until we receive the command response from the
        game server or until we reach the timeout.
        """
        self.pending_command = cmd
        self.pending_command_response = None
        self._command_no_wait(cmd)
        response = self._wait_for_response(timeout)
        if response == "Unknown command":
            raise CommandFailedError("Unknown command: %s" % cmd)
        return response


    def _wait_for_response(self, timeout):
        """block until response to for the current command has been received or until timeout is reached."""
        if self.isStopped():
            return

        if timeout is None:
            timeout = self.command_timeout

        self.getLogger().debug("waiting response for command: %s " % self.pending_command)
        self.__command_reply_event.clear()
        self.__command_reply_event.wait(timeout) # will wait until either the __command_reply_event is set or command_timeout is reached

        cmd = self.pending_command
        self.pending_command = None

        response = self.pending_command_response
        self.pending_command_response = None

        if not response:
            # then we stopped waitting because the timeout is reached
            raise CommandTimeoutError("no response for command : %s" % cmd)
        else:
            # we have our response \o/
            return response


    def compute_crc(self, data):
        buf = buffer(data)
        crc = binascii.crc32(buf) & 0xffffffff
        crc32 = '0x%08x' % crc
        # self.getLogger().debug("crc32 = %s" % crc)
        return int(crc32[8:10], 16), int(crc32[6:8], 16), int(crc32[4:6], 16), int(crc32[2:4], 16)


    def decode_server_packet(self, packet):
        if packet[0:2] != b'BE':
            return 255, '', ''

        packet_crc = packet[2:6]
        #self.getLogger().debug("Packet crc: %s" % repr(packet_crc))
        crc1, crc2, crc3, crc4 =  self.compute_crc(packet[6:])
        computed_crc = chr(crc1) + chr(crc2) + chr(crc3) + chr(crc4)
        # self.getLogger().debug("Computed crc: %s" % repr(computed_crc))
        if packet_crc != computed_crc:
            self.getLogger().debug('Invalid crc')
            return 255, '', ''

        type = ord(packet[7:8])
        sequence_no = ord(packet[8:9])
        data = packet[9:]
        return type, sequence_no, data


    def encode_packet(self, packet_type, seq, data):
        data_to_send = bytearray()

        #self.getLogger().debug('Encoded data is %s' % data)
        #data_to_send = data_to_send + chr(255) + packet_type + bytearray(data, 'Latin-1', 'ignore')
        data_to_send.append(255)
        data_to_send.append(packet_type)
        if seq is not None:
            data_to_send.append(seq)
        if data:
            data_to_send.extend(unicode(data).encode('UTF-8', 'replace'))
        crc1, crc2, crc3, crc4 = self.compute_crc(data_to_send)
        # request =  "B" + "E" + chr(crc1) + chr(crc2) + chr(crc3) + chr(crc4) + data_to_send
        request = bytearray(b'BE')
        request.append(crc1)
        request.append(crc2)
        request.append(crc3)
        request.append(crc4)
        request.extend(data_to_send)
        #self.getLogger().debug("Request is type : %s" % type(request))
        return request


    def _handle_multipacket_part(self, total_num_packets, current_packet_index, data):
        """Command responses can be received over multiple packest"""
        self._multi_packet_response[current_packet_index] = data
        if current_packet_index == total_num_packets - 1:
            # we got all the packets that make a full command response
            data = ''
            for p in range(0, total_num_packets):
                if len(self._multi_packet_response[p]):
                    data = data + self._multi_packet_response[p]
                else:
                    self.debug('Part of Multi packet response is missing')
                    for pp in range(0, total_num_packets-1):
                        self._multi_packet_response[pp] = ''
                    return

            # Packet reconstituted, so delete segments
            for pp in range(0, total_num_packets-1):
                del self._multi_packet_response[pp]

            return data
        else:
            return


    def _on_event(self, message):
        """We received a full Server message packet (type 2 BattlEye packet)"""
        self.getLogger().debug("received BattlEye event : %s" % message)
        for func in self.observers:
            func(message)


    def _on_command_response(self, message):
        """We received a full Command response message (one or more type 1 BattlEye packets)"""
        self.getLogger().debug("received BattlEye command response : %s" % message)
        self.pending_command_response = message
        self.__command_reply_event.set() # notify the waitting thread that a response is ready


    def __getattr__(self, name):
        if name == 'connected':
            return self._isconnected
        else:
            return self.name


    def getLogger(self):
        return logging.getLogger("BattleyeServer")


    def subscribe(self, func):
        """Add func from Battleye events listeners."""
        self.getLogger().info("func %s subscribed to BattlEye events" % func)
        self.observers.add(func)


    def unsubscribe(self, func):
        """Remove func from Battleye events listeners."""
        self.getLogger().info("func %s unsubscribed to BattlEye events" % func)
        self.observers.remove(func)


    def stop(self):
        self.getLogger().debug("stopping Threads...")
        self._stopEvent.set()
        self._disconnect()


    def isStopped(self):
        return self._stopEvent.is_set()


########################################################################################################################
# Example program
if __name__ == '__main__':

    import sys, os
    from ConfigParser import SafeConfigParser
    from random import sample, random

    print "Remote administration event listener for BattlEye"

    host = port = pw = None

    # load previous config
    test_config_file = os.path.join(os.path.dirname(__file__), 'test_rcon.ini')
    if os.path.isfile(test_config_file):
        try:
            conf = SafeConfigParser()
            conf.read(test_config_file)
            host = conf.get("server", "host")
            port = int(conf.get("server", "port"))
            pw = conf.get("server", "password")
        except:
            pass

    # prompt user if missing config info
    if not host and not port and not pw:
        if len(sys.argv) != 4:
            host = raw_input('Enter game server host IP/name: ')
            port = int(raw_input('Enter host port: '))
            pw = raw_input('Enter password: ')
        else:
            host = sys.argv[1]
            port = int(sys.argv[2])
            pw = sys.argv[3]

    # save config
    with open(test_config_file, "w") as f:
        conf = SafeConfigParser()
        conf.add_section('server')
        conf.set("server", "host", host)
        conf.set("server", "port", str(port))
        conf.set("server", "password", pw)
        conf.write(f)


    # prepare a class that will be able to spam commands randomly
    class CommandRequester(Thread):
        """Thread that spams commands"""
        _stop = Event()
        nb_instances = 0
        def __init__(self, battleye_server, commands=('status',), delay=5):
            self.__class__.nb_instances += 1
            Thread.__init__(self, name="CommandRequester%s" % self.__class__.nb_instances)
            self.battleye_server = battleye_server
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
                    response = self.battleye_server.command(cmd)
                    self.getLogger().info("###\treceived \t%s" % repr(response))
                except CommandError, err:
                    self.getLogger().info("###\tcommand failed \t%s" % repr(err.message))
                time.sleep(self.delay + random())
            self.getLogger().info("stopped spamming commands")

        @classmethod
        def stopAll(cls):
            cls._stop.set()



    # setup logging
    logging.basicConfig(level=logging.INFO, format="%(name)-20s [%(thread)-4d] %(threadName)-15s %(levelname)-8s %(message)s")
    logging.info("here we go")


    # prepare a function that will subscribe to BattleEye events
    def battleyeEventListener(event):
        print "BATTLEYE EVENT: %s" % event


    # connect to the BattlEye server
    t_conn = BattleyeServer(host, port, pw)

    try:
        t_conn.subscribe(battleyeEventListener)

        # 1st try just one command
        for line in t_conn.command('players').split('\n'):
            print "players response : " + line

        time.sleep(1)
        # unleash the command spammers !
        CommandRequester(t_conn, ('bans', 'missions', 'players', 'f00', 'say -1 hello', u'say -1 ---- b³ ----')).start()
        time.sleep(.5)
        CommandRequester(t_conn, ('bans', 'missions', 'players', 'f00', 'say -1 hello', u'say -1 ---- b³ ----')).start()
        time.sleep(.5)
        CommandRequester(t_conn, ('bans', 'missions', 'players', 'f00', 'say -1 hello', u'say -1 ---- b³ ----')).start()

        # let it bake for some time
        time.sleep(20)

    finally:
        # clean our mess
        t_conn.stop()
        CommandRequester.stopAll()
        logging.info("here we die")

