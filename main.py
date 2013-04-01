#!/usr/bin/python

import paramiko, time, re, sys, conf
from datetime import datetime

class God:
    def __init__(self):
        self.last_ping = 0
        self.last_file_write = conf.else_fname
    
    def create_client(self):
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh.connect('192.168.2.1', username='root', password=conf.r_pw)
        time.sleep(1)
        
        for _ in xrange(5):
            if hasattr(self, "s") == False or self.s.closed == True:
                self.s = self.ssh.invoke_shell()
                time.sleep(1)
        
        if hasattr(self, "s") == False or self.s.closed == True:
            print "Cannot connect to router and invoke shell" # TODO: add to some logging
            return False
        else:
            return True
        
    def connect_to_modem(self):
        while not self.s.send_ready():
            time.sleep(1)
        self.s.send('telnet 192.168.1.1\r\n')
        return None
    
    def login_to_modem(self):
        # send username
        while not self.s.send_ready():
            time.sleep(1)
        while not "Login:" in self.s.in_buffer._buffer[:].tostring():
            time.sleep(1)
        self.s.send(conf.m_un+'\r\n')
        # send password
        while not self.s.send_ready():
            # expect Password:
            time.sleep(1)
        while not "Password:" in self.s.in_buffer._buffer[:].tostring():
            time.sleep(1)
        self.s.send(conf.m_pw+'\r\n')
        return True
    
    def enable_logging_on_modem(self):
        commands=[
                  "system log enable 802_1x filter",
                  "system log enable 802_1x supp-events",
                  "system log enable 802_1x supp-keys",
                  "system log enable 802_1x eapol",
                  "system log enable 802_1x supp-trace",
                  "system log enable 802_1x eap",
                  
                  "system log enable dapi error",
                  "system log enable dapi warn",
                  "system log enable dapi info",
                  
                  "system log enable dslhome fatal",
                  "system log enable dslhome error",
                  
                  "system log enable eapauth auth",
                  "system log enable eapauth wsc",

                  "system log enable igd actions",
                  "system log enable igd bun",
                  "system log enable igd database",
                  "system log enable igd events",
                  "system log enable igd resvmaps",

                  #"system log enable ip arp", # halfly floody
                  "system log enable ip config",
                  "system log enable ip icmp",
                  "system log enable ip l2cyan",
                  #"system log enable ip rawip", # flood
                  #"system log enable ip socket",# flood
                  ##"system log enable ip tcp", # don't want to try
                  "system log enable ip udperr",
                  ##"system log enable ip udp",# don't want to try
                  
                  "system log enable ipoa trace",
                  "system log enable ipoa debug",

                  "system log enable l2tp config",
                  "system log enable l2tp control",
                  "system log enable l2tp data",

                  "system log enable pctrl UT",
                  "system log enable pctrl trace",

                  "system log enable rip errors",
                  #"system log enable rip rx", # halfly floody
                  #"system log enable rip tx", # halfly floody

                  "system log enable upload info",
                  "system log enable upload preserve",
                  "system log enable upload get",

                  "system log enable upnp gena",
                  "system log enable upnp inst",
                  "system log enable upnp soap",
                  "system log enable upnp ssdp",

                  "system log enable voip callc",
                  "system log enable voip control",
                  "system log enable voip mgal",
                  "system log enable voip pots",
                  "system log enable voip parser",
                  "system log enable voip bm",
                  "system log enable voip pem",

                  "system log enable webserver ssl",
                  "system log enable webserver file",
                  "system log enable webserver access",
                  "system log enable webserver_cwm error",
                  "system log enable webserver_cwm warn",
                  "system log enable webserver_cwm inform",

                  "system log enable wpa errors",
                  "system log enable wpa states",
                  "system log enable wpa gtk",
                  "system log enable wpa events",

                  "system log enable zipb errors",
                  "system log enable zipb warnings",
                  "system log enable zipb trace",
                  
                  ]
        for command in commands:
            while not self.s.send_ready():
                time.sleep(1)
            time.sleep(0.3)
            self.s.send(command+'\r\n')
        time.sleep(0.3)
        return None
    
    
    def log_saving(self):
        while True:
            # send ping every 100 seconds
            if self.last_ping + 100 < time.time():
                self.last_ping = time.time()
                print "sending ping"
                check_for_broken_session(self)
            
            # read all console debug messages and sort it to separated log files
            if not self.s.recv_ready():
                time.sleep(1)
                continue
            
            # fetch logs
            all_logs = self.s.recv(1000000000000000000000000000000000)
            
            # parse and write logs into files
            for log in all_logs.split("\r\n"):
                if log=="" or log=="--> ":
                    # skip empty or "ping" line
                    continue
                
                # pick timestamp
                log_time=datetime.fromtimestamp(time.time()).strftime("%d_%m_%Y__%H_%M_%S")
                
                # cut ping prompt in the front
                if log.startswith("--> "):
                    log = log[4:]
                    
                # check if that line is new log entry
                change_logfile = re.match("^[^ \n\r\t]+:.*", log)
                
                # don't change logfile in that cases
                
                #change_logfile = False
                
                if change_logfile:
                    # prefix is recognized. Sort log entries into separated log files
                    fname = log[0:log.find(":")]+"_.log"
                    
                    # remember last file name
                    self.last_file_write = fname
                
                # write to file. If there is unrecognized prefix than it isn't
                # updated so still write to the same file
                file(conf.dirprefix+self.last_file_write,"ab").write(log_time+" : "+log+"\n")
        pass
            

def restart_ssh_connection(self):
    # if it's not than try to invoke it again
    for _ in xrange(500):
        if self.create_client() == True:
            return True
        time.sleep(5)
    else:
        # Cannot connect to the router or invoke shell
        return False
    
def restart_telnet_connection(self):
    # restart ssh session
    if not restart_ssh_connection(self):
        #TODO: logging
        print "Cannot restart ssh session"
        sys.exit(3)
    # kill all telnet sessions if any
    self.s.send('killall telnet\n')
    time.sleep(0.3)
    
    # telnet again
    self.connect_to_modem()
    self.login_to_modem()
    self.enable_logging_on_modem()
    
    # send ping
    self.s.send('\r\n')
    
    if "-->" in self.s.in_buffer._buffer[:].tostring():
        return True
    else:
        return False
    
def check_that_session_is_alive(self):
    """
    function which will be used in thread for periodic sending ping that telnet
    session won't timed out 
    
    :param chan: instance of class paramiko.channel.Channel
    
    :returns: None
    """
    
    if self.s.closed == True:
        restart_telnet_connection(self)
        time.sleep(1)
        
    # send ping
    self.s.send('\r\n')
    
    if "-->" in self.s.in_buffer._buffer[:].tostring():
        return True
    else:
        if not restart_telnet_connection(self):
            #TODO: logging
            print "Cannot restart telnet connection"
            sys.exit(3)
    return True
def flush_logs_to_else_folder(self):
    # flush logs to else file
    self.last_file_write = conf.else_fname
    if self.s.recv_ready():
        all_logs = self.s.recv(1000000000000000000000000000000000)
        log_time=datetime.fromtimestamp(time.time()).strftime("%d_%m_%Y__%H_%M_%S")
        file(conf.dirprefix+self.last_file_write,"ab").write(log_time+" : "+all_logs+"\n")
    
def check_for_broken_session(self):
    # flush
    flush_logs_to_else_folder(self)
    
    # check that session is alive
    if not check_that_session_is_alive(self):
        #TODO: logging
        print "Cannot connect to the modem or invoke shell"
        sys.exit(3)
    
    # flush again
    flush_logs_to_else_folder(self)
        
    return True

def run():
    g = God()
    g.create_client()
    g.connect_to_modem()
    g.login_to_modem()
    g.enable_logging_on_modem()
    g.log_saving()
    
run()

