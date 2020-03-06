#!/usr/bin/env python


"""
Usage:
    applypatch_29520544.py -h
    applypatch_29520544.py -s <servername> [-u <username>] [-p <password>]


Options:
    -h,--help       Show this help message
    -v,--version     Show version
    -s <servername>  hostname of machine, if vlan,use ip instead
    -u <username>  username [default: root]
    -p <password>  password [default: welcome1]
"""

from docopt import docopt
import re,os
import oda_lib
import common_fun as c_f
import initlogging
import logging


def apply_29520544(host):
    remote_file = scp_zip(host)
    unzip(host, remote_file)
    setupssh(host)
    apply_patch(host)
    if host.is_ha_not ():
        node2 = c_f.node2_name(host.hostname)
        host2 = oda_lib.Oda_ha(node2, host.username, host.password)
        remote_file = scp_zip (host2)
        unzip (host2, remote_file)
        apply_patch (host2)

def scp_zip(host):
    gi_home = host.gi_home()
    remote_dir = "/tmp"
    if re.search("12.1", gi_home):
        patchfile = "/net/rwsak13/oda/18.3.0.1/p29608813_12102170718forACFS_Linux-x86-64.zip"
    else:
        patchfile = "/net/rwsak13/oda/18.3.0.1/p29597701_12201180417ACFSApr2018RU_Linux-x86-64.zip"
    patch = os.path.basename(patchfile)
    remotefile = os.path.join(remote_dir, patch)
    host.scp2node(patchfile, remotefile)
    return remotefile

def unzip(host, remote_file):
    cmd = "unzip -o %s -d /tmp" % remote_file
    host.ssh2node(cmd)
    griduser = host.griduser()
    gridgroup = host.gridgroup()
    cmd = "chown -R %s:%s /tmp/2*" % (griduser, gridgroup)
    host.ssh2node(cmd)

def setupssh(host):
    file = os.path.join(c_f.scr_dir,"SetupAutoSSH.sh")
    #file = "/chqin/new_test/venv/src/SetupAutoSSH.sh"
    remotefile = os.path.join("/tmp",os.path.basename(file))
    host.scp2node(file, remotefile)
    if host.is_dcs_or_oak():
        password = host.newpassword
    else:
        password = "welcome1"
    if host.is_ha_not():
        node2 = c_f.node2_name(host.hostname)
        cmd = "/tmp/SetupAutoSSH.sh --nodes=%s,%s --password=%s" % (host.hostname, node2, password)
    else:
        cmd = "/tmp/SetupAutoSSH.sh --nodes=%s --password=%s" % (host.hostname, password)

    cmd1 = "chmod +x /tmp/SetupAutoSSH.sh"
    host.ssh2node(cmd1)
    wholecmd = 'su - %s -c "%s"' %(host.griduser, cmd)
    result = host.ssh2node(cmd)
    log.info(result)
    result = host.ssh2node(wholecmd)
    log.info(result)

def apply_patch(host):
    gi_home = host.gi_home()
    cmd1 = "export ORACLE_HOME=%s;%s/OPatch/opatchauto apply /tmp/29597701 -oh %s -analyze" % (gi_home, gi_home, gi_home)
    if re.search ("12.1", gi_home):
        cmd1 = "export ORACLE_HOME=%s;%s/OPatch/opatchauto apply /tmp/29608813 -oh %s -analyze" % (
        gi_home, gi_home, gi_home)

    result = host.ssh2node(cmd1)
    log.info(result)
    if re.search("error|fail", result, re.IGNORECASE):
        log.error("Fail to analyze patch!")
    else:
        print "Success analyze patch!"

    if host.is_ha_not():
        cmd2 = re.sub("-analyze", '',cmd1)
    else:
        cmd2 = re.sub("-analyze", '-nonrolling',cmd1)
    result = host.ssh2node (cmd2)
    log.info (result)
    if re.search ("error|fail", result, re.IGNORECASE):
        log.error ("Fail to apply patch!")
    else:
        print "Success apply patch!"

def initlog(plog):
    oda_lib.initlog(plog)
    global log
    log = plog

def log_management(hostname):
    global logfile
    logname = "apply_patch_%s.log" % hostname
    logfile = os.path.join (c_f.log_dir, logname)
    log = initlogging.initLogging ("apply_patch", logfile, logging.WARN, logging.DEBUG)
    initlog(log)


if __name__ == '__main__':
    arg = docopt(__doc__)
    print arg
    hostname = arg['-s']
    username = arg['-u']
    password = arg['-p']
    log_management(hostname)
    host = oda_lib.Oda_ha(hostname, username, password)
    apply_29520544(host)
    print "Done, please check the log %s for details!" % logfile