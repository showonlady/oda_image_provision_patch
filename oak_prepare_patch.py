#!/usr/bin/env python
#conding utf-8

"""
Usage:
    oak_prepare_patch.py -s <servername> [-u <username>] [-p <password>]

Options:
    -h,--help       Show this help message
    -v,--version     Show version
    -s <servername>  hostname of machine, if vlan,use ip instead
    -u <username>  username [default: root]
    -p <password>  password [default: welcome1]
"""

from docopt import docopt
import oda_lib
import os, sys
import common_fun as cf
import re
import logging
import initlogging

remote_dir = "/cloudfs"

def scp_unpack_pb(host,p_v):
    v = cf.trim_version(p_v)
    loc = "/chqin/ODA%s/OAKPB/" % v
    for i in os.listdir(loc):
        scp_file = os.path.join(loc, i)
        remote_file = os.path.join(remote_dir, i)
        host.scp2node(scp_file, remote_file)
        cmd = "/opt/oracle/oak/bin/oakcli unpack -package %s" % remote_file
        log.info(cmd)
        result = host.ssh2node(cmd)
        log.info(result)
        if re.search('successful', result,re.IGNORECASE):
            host.ssh2node('rm -rf %s' % remote_file)
        else:
            log.error("fail to unpack the patchbundle!")
            sys.exit(0)



# def scp_stat(host):
#     stat = "stats.sh"
#     remote_file = os.path.join(remote_dir, os.path.basename(stat))
#     host.scp2node(stat,remote_file)

def pre_patch_check(host):
    cmd1 = "/opt/oracle/oak/bin/oakcli show version -detail"
    #cmd2 = "sh /tmp/stats.sh"
    #cmd3 = "/opt/oracle/oak/bin/oakcli validate -a"
    cmd3 = "/opt/oracle/oak/bin/oakcli validate -d"
    cmd4 = "/opt/oracle/oak/bin/oakcli show databases"
    cmd5 = "/opt/oracle/oak/bin/oakcli show dbhomes"
    cmd8 = host.gi_home() + "/bin/srvctl status mgmtdb"
    log.info(host.ssh2node(cmd1))
    log.info(host.crs_status())
    log.info(host.ssh2node(cmd3))
    log.info(host.ssh2node(cmd4))
    log.info(host.ssh2node(cmd5))
    log.info(host.ssh2node(cmd8))
    if host.is_vm_or_not():
        cmd6 = "/opt/oracle/oak/bin/oakcli show vm"
        cmd7 = "/opt/oracle/oak/bin/oakcli show repo"
        log.info(host.ssh2node(cmd6))
        log.info(host.ssh2node(cmd7))

def post_unpack(host):
    cmd1 = "/opt/oracle/oak/bin/oakcli update -patch %s -verify" % host.Current_version
    log.info(host.ssh2node(cmd1))


def node2_host(host):
    oak2 = cf.node2_name(host.hostname)
    host2 = oda_lib.Oda_ha(oak2, host.username, host.password)
    return host2

def initlogger(hostname):
    global logfile
    logname = "oak_prepare_patch_%s.log" % hostname
    logfile = os.path.join(cf.log_dir, logname)
    log = initlogging.initLogging("oak_pb", logfile)
    return log


def initlog(plog):
    oda_lib.initlog(plog)
    global log
    log = plog

def log_management(hostname):
    log = initlogger(hostname)
    initlog(log)



def main(host, version=oda_lib.Oda_ha.Current_version):
    host2 = node2_host(host)
    pre_patch_check(host)
    pre_patch_check(host2)
    scp_unpack_pb(host, version)
    scp_unpack_pb(host2, version)
    post_unpack(host)
    post_unpack(host2)



if __name__ == '__main__':
    arg = docopt(__doc__)
    print arg
    hostname = arg['-s']
    username = arg['-u']
    password = arg['-p']
    log_management(host.hostname)
    host = oda_lib.Oda_ha(hostname, username, password)
    main(host)
    print "Done, please check the log %s for details!" % logfile



