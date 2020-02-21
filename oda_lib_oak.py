import re
import os
import paramiko
import traceback
import time
import simplejson
import common_fun as cf
import sys
import logging
import initlogging

def initlog(plog):
    global log
    log = plog

class Oda_ha(object):
    Current_version = "18.4.0.0"
    ODACLI = "/opt/oracle/dcs/bin/odacli "

    def __init__(self, hostname, username, password):
        self.hostname = hostname
        self.username = username
        self.password = password
        self.newpassword = "WElcome12_-"
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            self.ssh.connect(hostname=self.hostname, port=22, username=self.username, password=self.password)
        except Exception as e:
            self.ssh.connect(hostname=self.hostname, port=22, username=self.username, password=self.newpassword)
        try:
            self.transport = paramiko.Transport((self.hostname, 22))
            self.transport.connect(username=self.username, password=self.password)
        except Exception as e:
            self.transport = paramiko.Transport((self.hostname, 22))
            self.transport.connect(username=self.username, password=self.newpassword)

    def ssh2node(self, cmd):
        log.info(cmd)
        sys.stdout.flush()
        stdin, stdout, stderr = self.ssh.exec_command(cmd)
        result = stdout.read().strip()
        errormsg = stderr.read().strip()
        # ssh.close()
        return result + errormsg

    def ssh2node_input(self, cmd):
        log.info(cmd)
        sys.stdout.flush()
        stdin, stdout, stderr = self.ssh.exec_command(cmd)
        stdin.write("%s\n" % self.newpassword)
        result = stdout.read().strip()
        errormsg = stderr.read().strip()
        # ssh.close()
        return result + errormsg


    def scp2node(self, scp_file, remote_file):

        sftp = paramiko.SFTPClient.from_transport(self.transport)
        sftp.put(scp_file, remote_file)

    def system_version(self):
        cmd = "rpm -qa|grep oak"
        result = self.ssh2node(cmd)
        b = re.search('oak-(\S+)_L', result).group(1)
        c = cf.trim_version(b)
        return c

    def is_vm_or_not(self):
        cmd = "rpm -qa|grep ovm-template"
        result = self.ssh2node(cmd)
        if result:
            return 1
        else:
            return 0




