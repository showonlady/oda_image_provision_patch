#!/usr/bin/env python
# -*- coding: utf-8 -*-

import paramiko
import os
import datetime
import difflib
import re
import time
import string
import random
import sys
import subprocess
import oda_lib
import pexpect
import simplejson

WORK_DIR = "/home/chqin/new_test/venv"
log_stamp = datetime.datetime.today().strftime("%Y%m%d")
scr_dir = os.path.join(WORK_DIR, 'src')
log_dir = os.path.join(WORK_DIR, 'result')
script_dir = os.path.join(WORK_DIR, 'script')
string1 = string.ascii_letters + string.digits
string2 = string.ascii_letters + string.digits + "_"
machine_file = os.path.join(WORK_DIR, 'machine.json')
allmachine_file = os.path.join(WORK_DIR, 'allmachine.json')
with open (allmachine_file, 'r') as f:
    host_info = simplejson.load (f)
with open (machine_file, 'r') as f:
    host_notv2v3 = simplejson.load (f)
host_all = {}
host_all.update(host_info)
host_all.update(host_notv2v3)


def generate_string(source, length):
    len1 = random.randint(1, length)
    cha = random.choice(string.ascii_letters)
    chb = ''.join(random.sample(source, len1-1))
    return cha+chb

def openfile(filename):
    out, err = sys.stdout, sys.stderr
    fp = open(filename, 'a')
    sys.stdout, sys.stderr = fp, fp
    return fp, out, err

def closefile(fp, out, error):
    fp.close()
    sys.stdout, sys.stderr = out, error



"""
class logfile(object):
    out, err = sys.stdout, sys.stderr
    def __init__(self, name):
        self.name = name
        self.out, self.err = sys.stdout, sys.stderr

    def openfile(self):
        fp = open(self.name, 'w')
        sys.stdout = fp
        sys.stderr = fp
        return fp

    def closefile(self, fp):
        fp.close()
        sys.stdout, sys.stderr= self.out, self.err

"""

def logfile_name_gen_open(logfile_name):
    log_stamp = datetime.datetime.today().strftime("%Y%m%d")
    logfile_name_stamp = logfile_name+ '_' + log_stamp
    log = os.path.join(log_dir, logfile_name_stamp)
    fp, out, err = openfile(log)
    return fp, out, err,log

def logfile_close(fp, out, err):
    closefile(fp, out, err)

def logfile_close_check_error(fp, out, err,log):
    closefile(fp, out, err)
    error = check_log(log)
    return error

def check_error(result):
    p = re.compile("DCS-|fail|error|exception|warn|No such file", re.IGNORECASE)
    if p.search(result):
        return 1
    else:
        return 0

def change_hm(options):
    a = re.sub("-hm\s+\S+","-m ",options)
    return a

def change_hbp(options):
    a = re.sub("-hbp\s+\S+","-bp ",options)
    return a

def change_hp(options):
    a = re.sub("-hp\s+\S+","-p ",options)
    return a

def check_log(log_name):
    #cmd = "egrep -B1 -i 'DCS-|fail|error|exception|warn|No such file' %s" % log_name
    cmd = "egrep -B1 -i 'fail' %s" % log_name
    output = exc_cmd(cmd)
    log_error = os.path.join(log_dir,'log_error_%s' % log_stamp)
    fp = open(log_error, 'a')
    fp.write("\n\n%s === Summary: Here is the errors:\n\n" % log_name)
    if not output:
        fp.write("No error!\n")
        fp.close()
        return 1
    else:
        fp.write(output)
        fp.close()
        return 0

def exc_cmd(cmd):
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (stdout, stderr) = p.communicate()
    return stdout + stderr


def exc_cmd_new(cmd):
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (stdout, stderr) = p.communicate()
    recode = p.returncode
    return stdout + stderr, recode


# def trim_version(x):
#     while x[-1] == '0':
#         x = x[:-2]
#     return x

def trim_version(x):
    y = x.split('.')
    while y[-1] == '0':
        y = y[:-1]
    x = '.'.join(y)
    return x


def ping_host(hostname):
    cmd = "ping -c 3 %s | grep '3 received' | wc -l" % hostname
    result = int(exc_cmd(cmd))
    return result

def wait_until_ping(hostname, waittime = 300):
    while(not ping_host(hostname)):
        time.sleep(10)
    time.sleep(waittime)

def extend_space_u01(host):
    host.extend_u01()
    if host.is_ha_not():
        node2 = node2_name(host.hostname)
        host2 = oda_lib.Oda_ha(node2, host.username, host.password)
        host2.extend_u01()

def extend_space_opt(host):
    host.extend_opt()
    if host.is_ha_not():
        node2 = node2_name(host.hostname)
        host2 = oda_lib.Oda_ha(node2, host.username, host.password)
        host2.extend_opt()

def extend_space_tmp(host):
    if host.is_vm_or_not():
        log.info("We could not extend the space of tmp on VM stack!")
        return 0
    host.extend_tmp()
    if host.is_ha_not():
        node2 = node2_name(host.hostname)
        host2 = oda_lib.Oda_ha(node2, host.username, host.password)
        host2.extend_tmp()


def node2_name(a):
    if re.search('com', a):
        name = a.split('.',1)
        n1 = name[0]
        b = n1[:-1] + str(int(n1[-1]) + 1) + '.' + name[1]
    elif re.match('\d', a):
        c = str (int (a.split (".")[-1]) + 1)
        b = ".".join (a.split (".")[:-1])
        b = b + '.' + c
    else:
        b = a[:-1] + str(int(a[-1]) + 1)
    return b


def dom0_name(hostname):
    if re.search('com', hostname):
        a = hostname.split('.')
        c = re.search('(\D+\d+)', a[0]).group(1)
        name1 =  [c + '1'] + a [1:]
        name2 =  [c + '2'] + a [1:]
        dom1 = '.'.join(name1)
        dom2 = '.'.join(name2)
        return dom1, dom2
    else:
        b = re.search('(\D+\d+)', hostname).group(1)
        return b+'1', b+'2'


def host_reachable(hostname):
    result = 0
    cmd = "ping -c 3 %s | grep '3 received' | wc -l" % hostname
    for i in range(5):
        out,err = exc_cmd_new(cmd)
        if err:
            log.error(err)
            return result
        else:
            if int(out):
                result = 1
                return result
            else:
                time.sleep(60)
    return result

def add_line_ecthosts(host):
    ###Check if dns is configured
    ## if not, add "10.241.247.6  storage.oraclecorp.com" to /etc/hosts
    cmd1 = "cat /etc/resolv.conf"
    output = host.ssh2node(cmd1)
    if not re.search("nameserver", output):
        cmd2 = """echo "10.241.247.6  storage.oraclecorp.com" >>/etc/hosts"""
        host.ssh2node(cmd2)


def covertlog(logname):
    cmd = "dos2unix -q %s" % logname
    exc_cmd(cmd)

def equal_version(host, version):
    s_v = host.system_version()
    s_v = trim_version(s_v)
    if trim_version(version) == s_v:
        return 1
    else:
        return 0


def run_expect_dbhome(*a):
    #logfile = '/tmp/ssh.log'
    host = a[0]
    expectlist = a[1]
    logfile = a[2]
    time1 = a[3]
    fout = open(logfile, 'wb')
    cmd = "ssh -o UserKnownHostsFile=/dev/null %s" % (host.hostname)
    child = pexpect.spawn (cmd, logfile = fout)
    child = login(child, host)
    child.sendline(expectlist[0])
    for line in expectlist[1:]:
        if len(line) != 2:
            print "expectlist format is not correct!"
            sys.exit(0)
        index = child.expect ([pexpect.TIMEOUT, line[0]], timeout=time1)
        if index == 1:
            child.sendline (line[1])
        if "patch all the above" in line[0]:
            time.sleep(1000)
        else:
            time.sleep(10)
    if len(a) == 4:
        return child
    elif len(a) == 5:
        time2 = a[4]
    else:
        print "The number of parameters is not correct, exit!"
        sys.exit(0)
    i  = child.expect ([pexpect.TIMEOUT, ".*#", pexpect.EOF], timeout=time2)
    print i
    child.close()
    fout.close()
    covertlog(logfile)


def run_expect(*a):
    #logfile = '/tmp/ssh.log'
    host = a[0]
    expectlist = a[1]
    logfile = a[2]
    time1 = a[3]
    fout = open(logfile, 'wb')
    cmd = "ssh -o UserKnownHostsFile=/dev/null %s" % (host.hostname)
    child = pexpect.spawn (cmd, logfile = fout)
    child = login(child, host)
    child.sendline(expectlist[0])
    for line in expectlist[1:]:
        if len(line) != 2:
            print "expectlist format is not correct!"
            sys.exit(0)
        index = child.expect ([pexpect.TIMEOUT, line[0]], timeout=time1)
        if index == 1:
            child.sendline (line[1])
        time.sleep(10)

    if len(a) == 4:
        return child
    elif len(a) == 5:
        time2 = a[4]
    else:
        print "The number of parameters is not correct, exit!"
        sys.exit(0)
    i  = child.expect ([pexpect.TIMEOUT, ".*#", pexpect.EOF], timeout=time2)
    #print i
    child.close()
    fout.close()
    covertlog(logfile)

    # with open (logfile, 'r')as f:
    #     res = f.read()
    # return res

def oak_server_patch(host, cmd):
    logfile = os.path.join (log_dir, "oak_server_patch_%s_%s.log" % (host.hostname, log_stamp))
    cmdlist = ["%s" % cmd, ["assword", "%s" % host.password], ["assword", "%s" % host.password],
               ["continue", "Y"], ["second Node", "Y"], ["shutdown", "Y"],
               ["assword", "%s" % host.password], ["assword", "%s" % host.password]]
    child = run_expect (host, cmdlist, logfile, 60)
    i = child.expect (['(?i)Running /tmp/pending_actions on node 0', pexpect.TIMEOUT, ".*#", pexpect.EOF], timeout = 14400)
    #print i
    time.sleep(60)
    child.close()
    child.logfile.close()
    covertlog (logfile)
    return logfile

def oak_dbhome_patch(host, cmd):
    logfile = os.path.join (log_dir, "oak_dbhome_patch_%s_%s.log" % (host.hostname, log_stamp))
    cmdlist = ["%s" % cmd, ["assword", "%s" % host.password], ["assword", "%s" % host.password],
               ["patch all the above homes: Y | N", "Y"], ["patch all the above homes: Y | N", "Y"], ["patch all the above homes: Y | N", "Y"], ["patch all the above homes: Y | N", "Y"]]
    child = run_expect_dbhome (host, cmdlist, logfile, 60)
    i = child.expect ([ ".*#", pexpect.TIMEOUT, pexpect.EOF], timeout = 3600)
    #print i
    time.sleep(60)
    child.close()
    child.logfile.close()
    covertlog (logfile)
    return logfile


def cleanup_deployment(host, cmd):
    logfile = os.path.join (log_dir, "cleanup_%s_%s.log" % (host.hostname, log_stamp))
    cmdlist = ["%s" % cmd, ["assword", "%s" % host.password], ["assword", "%s" % host.password],
               ["yes", "yes"], ["yes", "yes"]]
    run_expect (host, cmdlist, logfile, 60, 1200)
    return logfile

def login(child, host):
    i = child.expect(["continue connecting", 'password: ', pexpect.TIMEOUT])
    if i == 0:
        child.sendline("yes")
        child.expect("[pP]assword")
        child.sendline("%s" % host.password)
    elif i == 1:
        child.sendline("%s" % host.password)
    else:
        print "connect to host %s timeout!" % host.hostname
        sys.exit(0)
    i = child.expect([".*#", 'assword: ', pexpect.TIMEOUT])
    if i == 0:
        return child
    elif i == 1:
        child.sendline("%s" % host.newpassword)
        child.expect(".*#")
        return child
    else:
        print "Could not connect!"
        sys.exit(0)


