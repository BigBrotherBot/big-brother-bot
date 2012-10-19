# coding=UTF-8
#
# Rcon client for Ravaged game server
# Copyright (C) 2012 Thomas LEVEIL
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
# CHANGELOG
# 1.1 - 2012/09/29
#   * updated for RavagedServer beta build [201209271447]
# 1.2 - 2012/10/17
#   * updated for RavagedServer beta build [201210140713]
#
from Queue import Queue, Empty
import logging
import asyncore
from socket import AF_INET, SOCK_STREAM
import re
from hashlib import sha1
from threading import Thread, Event, Lock
import time

__author__ = 'Thomas Leveil'
__version__ = '1.1'


class RavagedServerError(Exception):
    pass

class RavagedServerNetworkError(RavagedServerError):
    pass

class RavagedServerBlacklisted(RavagedServerNetworkError):
    pass

class RavagedServerCommandError(RavagedServerError):
    pass

class RavagedServerCommandTimeout(RavagedServerCommandError):
    pass

class RavagedServer(Thread):
    """thread opening a connection to a Ravaged game server and providing
    means of observing messages received and sending commands"""

    def __init__(self, host, port=13550, password='', user=None, command_timeout=1.0):
        Thread.__init__(self, name="RavagedServerThread")
        self.password = password
        self.command_timeout = command_timeout
        self.user = user if user else 'Admin'

        self._stopEvent = Event() # used to notify the thread to stop
        self.__command_reply_event = Event() # used to notify when we received a command response
        self.__command_lock = Lock() # used to make sure no 2nd command is sent while waiting for the response of a 1st command

        self._received_packets = Queue(maxsize=500)
        self.command_response = None # future command response to be received
        self.observers = set()
        self.log = logging.getLogger("RavagedServer")

        self.dispatcher = RavagedDispatcher(host, port, self._received_packets)
        self.packet_handler_thread = RavagedServerPacketHandler(self.log, self._received_packets, self._on_event, self._on_command_response)

        self.start()
        time.sleep(.2)

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

    def auth(self):
        self.log.info("authenticating %s" % self.user)
        try:
            response = self.command("LOGIN=%s" % self.user)
            self.log.debug("login response : %r" % response)
            if response.startswith('Suspicious activity detected'):
                raise RavagedServerBlacklisted(response)
        except RavagedServerCommandTimeout:
            pass
        response = self.command("PASS=" + sha1(self.password).hexdigest().upper())
        if response.startswith('Login success as '):
            self.log.info(response)
            # test we can send commands
            try:
                rv = self.command("testrcon")
                if rv != "Command not found, or invalid parameters given.":
                    raise RavagedServerNetworkError("not properly connected (%s)" % rv)
            except RavagedServerCommandTimeout:
                raise RavagedServerNetworkError("not properly connected")
            return
        elif response.startswith('Login failed'):
            self.log.warning(response)
            raise RavagedServerError(response)
        else:
            RavagedServerCommandError("unexpected response. %r" % response)


    def command(self, command):
        """send command to the server in a synchronous way.
        Calling this method will block until we receive the reply packet from the
        game server or until we reach the timeout.
        """
        if not self.connected:
            raise RavagedServerNetworkError("not connected")

        self.log.debug("command : %s " % repr(command))
        if not command or not len(command.strip()):
            return None

        with self.__command_lock:
            self.dispatcher.send_command(command)
            response = self._wait_for_response(command)
            return response


    def stop(self):
        self._stopEvent.set()
        self.dispatcher.close()

    #===============================================================================
    #
    # Other methods
    #
    #===============================================================================

    @property
    def connected(self):
        return self.dispatcher.connected


    def getLogger(self):
        return self.log


    def isStopped(self):
        return self._stopEvent.is_set()


    def run(self):
        """Threaded code"""
        self.packet_handler_thread.start()
        self.log.info('start server loop')
        try:
            while not self.isStopped():
                asyncore.loop(count=1, timeout=1)
        except KeyboardInterrupt:
            pass
        finally:
            self.dispatcher.close()
        self.log.info('end server loop')
        self.packet_handler_thread.stop()


    def _on_event(self, message):
        self.log.debug("received server event : %r" % message)
        for func in self.observers:
            func(message)


    def _on_command_response(self, command, response):
        self.log.debug("received server command %r response : %r" % (command, response))
        self.command_response = (command, response)
        self.__command_reply_event.set()


    def _wait_for_response(self, command):
        """block until response to for given command has been received or until timeout is reached."""
        l_command = command.lower()
        if l_command.startswith("login="):
            command_name = 'login'
        elif l_command.startswith("pass="):
            command_name = 'pass'
        else:
            command_name = command.split(' ', 1)[0].lower() # remove command parameters
        expire_time = time.time() + self.command_timeout
        while not self.isStopped() and self.dispatcher.connected:
            if not self.connected:
                raise RavagedServerNetworkError("lost connection to server")
            if time.time() >= expire_time:
                raise RavagedServerCommandTimeout("did not receive any response for %r" % command)
            self.log.debug("waiting for command %r response" % command)
            self.__command_reply_event.clear()
            self.__command_reply_event.wait(self.command_timeout)
            rv = self.command_response
            self.command_response = None
            if rv:
                cmd, response = rv
                if cmd and cmd.lower() != command_name:
                    self.log.debug("discarding command response %s:%s" % (cmd, response))
                    continue
                return response



class RavagedServerPacketHandler(Thread):
    """
    Thread that handles received packets found in received_packets_queue and call the event_handler or
    command_response_handler depending on the nature of the packets.
    """

    def __init__(self, logger, received_packets_queue, event_handler, command_response_handler):
        Thread.__init__(self, name="RavagedServerPacketHandlerThread")
        self.log = logger
        self._stopEvent = Event() # used to notify the thread to stop
        self._received_packets = received_packets_queue
        self.__event_handler = event_handler
        self.__command_response_handler = command_response_handler
        self.__stop_token = object()


    def run(self):
        self.log.info('start server packet handler loop')
        try:
            while not self.isStopped():
                try:
                    packet = self._received_packets.get(timeout=10)
                    if packet is self.__stop_token:
                        break
                    self.handle_packet(packet)
                    self._received_packets.task_done()
                except Empty:
                    pass
        finally:
            pass
        self.log.info('end server packet handler loop')


    def stop(self):
        self._stopEvent.set()
        self._received_packets.put(self.__stop_token)



    def isStopped(self):
        return self._stopEvent.is_set()


    def handle_packet(self, packet):
        """Called when a full packet has been received."""
        if packet[0] == '(' and packet[-1] == ')':
            self.handle_event(packet)
        elif packet.startswith('RCon:('):
            self.handle_event(packet)
        elif packet == 'You must be a superuser to run this command.':
            self.handle_command_response(None, packet)
        else:
            m = re.match(RE_COMMAND_RESPONSE, packet)
            if not m:
                self.handle_event(packet)
            else:
                self.handle_command_response(m.group('command'), m.group('response'))


    def handle_event(self, message):
        if self.__event_handler is not None:
            self.__event_handler(message)


    def handle_command_response(self, command, response):
        if self.__command_response_handler is not None:
            self.__command_response_handler(command, response)






MIN_MESSAGE_LENGTH = 4 # minimal response is "(1):"
RE_COMMAND_RESPONSE = re.compile(r'''^(?P<command>[\S^:]+):(?P<response>.*)$''', re.DOTALL)

class RavagedDispatcher(asyncore.dispatcher_with_send):
    """
    This asyncore dispatcher provides the send_command method to write to the socket
    and exposes a Queue.Queue that stores the received full packets.
    """

    def __init__(self, host, port, packet_queue=None):
        asyncore.dispatcher_with_send.__init__(self)
        self.log = logging.getLogger("RavagedDispatcher")
        self._buffer_in = ''
        self.packet_queue = packet_queue if packet_queue else Queue()
        self.log.info("connecting")
        self.create_socket(AF_INET, SOCK_STREAM)
        self.connect((host, port))

    #===============================================================================
    #
    #        Public API
    #
    #===============================================================================

    def send_command(self, command):
        """Send a command to the server."""
        self.log.debug("send_command : %s " % repr(command))
        self.send(unicode(command + "\n").encode('UTF-8'))

    def get_packet_queue(self):
        return self.packet_queue

    #===========================================================================
    #
    # asyncore handlers (low level)
    #
    #===========================================================================

    def handle_connect(self):
        self.log.debug("handle_connect")


    def handle_close(self):
        """Called when the socket is closed."""
        self.log.debug("handle_close")
        self.close()


    def handle_read(self):
        """Called when the asynchronous loop detects that a read() call on the channel's socket will succeed."""
        # received raw data
        data = self.recv(8192)
        self._buffer_in += data
        self.log.debug('read %s char from server' % len(data))

        # cook meaningful packets
        map(self.handle_packet, self.full_packets())


    def handle_packet(self, packet):
        """Called when a full packet has been received."""
        self.log.debug("handle_packet(%r)" % packet)
        self.packet_queue.put(packet)

    #===========================================================================
    #
    # Other methods
    #
    #===========================================================================

    def getLogger(self):
        return self.log


    def full_packets(self):
        """
        generator producing full packets from the data found in self._buffer_in
        :return: packet data (everything but the packet size header)
        """
        while len(self._buffer_in) >= MIN_MESSAGE_LENGTH:
            # read the size of this packet
            # 1st byte should be '('
            start_header_index = self._buffer_in.find('(')
            if start_header_index == -1:
                return

            # discard junk data before header
            self._buffer_in = self._buffer_in[start_header_index:]

            # packet header ends with ')'
            end_header_index = self._buffer_in.find(')')
            if end_header_index == -1:
                # we don't have a full header yet
                return

            data_size = int(self._buffer_in[1:end_header_index])
            start_data_index = end_header_index + 1
            end_data_index = start_data_index + data_size

            if len(self._buffer_in) < end_data_index:
                # we do not have enough data to make a full packer
                return

            packet_data = self._buffer_in[start_data_index:end_data_index]
            self._buffer_in = self._buffer_in[end_data_index:]

            unicode_data = packet_data.decode('UTF-8')
            yield unicode_data




if __name__ == '__main__':
    import logging, sys, os, argparse
    from ConfigParser import SafeConfigParser

    rcon_config_file = os.path.join(os.path.dirname(__file__), 'ravaged_rcon.ini')

    parser = argparse.ArgumentParser(description='Ravaged game server rcon client')
    parser.add_argument('host', type=str, nargs='?', default=None, help='Ravaged gameserver hostname or IP')
    parser.add_argument('port', type=int, nargs='?', default=None, help='Ravaged gameserver rcon port')
    parser.add_argument('password', type=str, nargs='?', default=None, help='Ravaged gameserver rcon password')
    parser.add_argument('--log', dest='loglevel', choices=('DEBUG', 'INFO', 'WARNING', 'ERROR'), default='ERROR', help='if you want additional log output')
    parser.add_argument('--user', type=str, help='optional Ravaged gameserver rcon user (default superadmin)')
    client_conf = parser.parse_args()

    if not all((client_conf.host, client_conf.port, client_conf.password)):
        if os.path.isfile(rcon_config_file):
            # load previous config
            try:
                conf = SafeConfigParser()
                conf.read(rcon_config_file)
                if not client_conf.host:
                    client_conf.host = conf.get("server", "host")
                if not client_conf.port:
                    client_conf.port = int(conf.get("server", "port"))
                if not client_conf.password:
                    client_conf.password = conf.get("server", "password")
                print "Server config loaded from %s" % rcon_config_file
            except:
                pass

    # prompt user if missing config info
    if not all((client_conf.host, client_conf.port, client_conf.password)):
        parser.print_help()

        client_conf.host = raw_input('Enter game server host IP/name: ')
        if not client_conf.host:
            print "incorrect host %r" % client_conf.host
            sys.exit(1)

        try:
            client_conf.port = int(raw_input('Enter host port: '))
        except ValueError:
            print "port must be a number"
            sys.exit(1)

        client_conf.password = raw_input('Enter password: ')
        if not client_conf.password:
            print "incorrect password"
            sys.exit(1)


    # save config
    with open(rcon_config_file, "w") as f:
        conf = SafeConfigParser()
        conf.add_section('server')
        conf.set("server", "host", client_conf.host)
        conf.set("server", "port", str(client_conf.port))
        conf.set("server", "password", client_conf.password)
        conf.write(f)
        print "Server config saved to %s" % rcon_config_file


    # set up logging
    logging.basicConfig(level=client_conf.loglevel.upper(), format="\t%(name)-20s [%(thread)-4d] %(threadName)-15s %(levelname)-8s %(message)s", stream=sys.stdout)
    logging.getLogger("RavagedDispatcher").setLevel(logging.WARNING)
    logging.getLogger("RavagedServer").setLevel(client_conf.loglevel.upper())


    def prompt_command():
        """
        python generator that prompt user for a command on the console until the command typed is either 'quit' or 'bye'
        """
        print "Type your commands below. To exit, type the command 'quit' or 'bye'."
        print "--------------------------------------------------------------------"
        rv = raw_input("$ ")
        while 1:
            if rv.lower() in ("quit", "bye"):
                return
            else:
                yield rv.decode(sys.stdin.encoding)
                try:
                    rv = raw_input("$ ")
                except KeyboardInterrupt:
                    return


    def serverevent_handler(message):
        """
        handles events received from the Ravaged server
        """
        print ">>> %s" % message


    # connect to Ravaged server
    try:
        t_conn = RavagedServer(client_conf.host, client_conf.port, client_conf.password, client_conf.user)
        t_conn.subscribe(serverevent_handler)

        # auth to Ravaged server
        t_conn.auth()

        # send user commands to Ravaged server
        for cmd in prompt_command():
            try:
                rv = t_conn.command(cmd)
                if rv:
                    print "%s" % rv
            except RavagedServerCommandTimeout, err:
                logging.warning(err)
            except RavagedServerCommandError, err:
                logging.error(err, exc_info=err)

    except RavagedServerBlacklisted, err:
        print "############## %s" % err
    except RavagedServerError, err:
        print err

    print "disconnecting..."
    t_conn.stop()
    logging.info("disconnected")


