#!/usr/bin/env python
#encoding utf-8
"""
Usage:
    oak_create_db.py [crdb] -s <servername> [-u <username>] [-p <password>]
    oak_create_db.py [crvm] -s <servername> [-u <username>] [-p <password>]

Options:
    -h,--help       Show this help message
    -v,--version     Show version
    -s <servername>  hostname of machine, if vlan,use ip instead
    -u <username>  username [default: root]
    -p <password>  password [default: welcome1]
    crvm   create vm
    crdb   create database
"""
from docopt import docopt

import random
import sys
import oda_lib
import re
import os
import common_fun as cf
import sys
import logging
import initlogging

create_db_script = os.path.join(cf.WORK_DIR,"create_db_defineversion_storage.pl")
remote_dir = "/tmp"
remote_dir2 = "/root"
version_file = os.path.join(cf.WORK_DIR, 'version')
vm_script = os.path.join(cf.WORK_DIR, "create_vm.sh")

d = {"12.1.2.12": ["12.1.0.2.170814", "11.2.0.4.170814"],
     "12.2.1.2": ["12.1.0.2.171017", "11.2.0.4.171017", "12.2.0.1.171017"],
     "12.2.1.3": ["12.1.0.2.180116", "11.2.0.4.180116", "12.2.0.1.180116"],
     "12.2.1.4": ["12.1.0.2.180417", "11.2.0.4.180417", "12.2.0.1.180417"],
     "18.3": ["12.1.0.2.180717", "11.2.0.4.180717", "12.2.0.1.180717", "18.3.0.0.180717"],
     "18.4": ["12.1.0.2.181016", "11.2.0.4.181016", "12.2.0.1.181016", "18.4.0.0.181016"],
     "18.5": ["12.1.0.2.190115", "11.2.0.4.190115", "12.2.0.1.190115", "18.5.0.0.190115"],
     "18.7": ["12.1.0.2.190716", "11.2.0.4.190716", "12.2.0.1.190716", "18.7.0.0.190716"],
     "18.8": ["12.1.0.2.191015", "11.2.0.4.191015", "12.2.0.1.191015", "18.8.0.0.191015"]

     }

def exec_crdb_script(host):
    write_version_file(host)
    scp_scrips(host)
    remote_file = os.path.join(remote_dir, os.path.basename(create_db_script))
    cmd = "perl %s" % remote_file
    result = host.ssh2node(cmd)
    log.info(result)
    sys.stdout.flush()

def exec_crvm_scripts(host):
    if host.is_vm_or_not():
        scp_template_file(host)
        scp_crvm_script(host)
        remote_file = os.path.join(remote_dir, os.path.basename(vm_script))
        cmd = "sh %s" % remote_file
        log.info(cmd)
        result = host.ssh2node(cmd)
        log.info(result)
        sys.stdout.flush()

    else:
        pass




def write_version_file(host):
    s_v = host.system_version()
    s_v = cf.trim_version(s_v)
    if s_v not in d.keys():
        #log.error("fail: not support this version: %s " % s_v)
        #sys.exit(0)
        versions = host.db_versions
    else:
        versions = d[s_v]
    fp = open(version_file,'w')
    if host.is_vm_or_not():
        j = 1
    else:
        if len(versions) == 2:
            j = 3
        else:
            j = 2
    for i in versions:
        for a in range(j):
            fp.write("%s  %s\n" % (i, random.choice(['ASM','ACFS'])))
    fp.close()



def scp_scrips(host):

    remote_file = os.path.join(remote_dir, os.path.basename(create_db_script))
    remote_file2 = os.path.join(remote_dir2, os.path.basename(version_file))
    host.scp2node(create_db_script, remote_file)
    host.scp2node(version_file, remote_file2)



def scp_template_file(host):
    hostname = host.hostname
    oak1, oak2 = cf.dom0_name(hostname)
    script = os.path.join(cf.WORK_DIR, "scp_template.sh")
    cmd = "sh %s %s %s" %(script, oak1, oak2)
    log.info(cmd)
    result = cf.exc_cmd(cmd)
    log.info(result)

def scp_crvm_script(host):
    remote_file = os.path.join(remote_dir, os.path.basename(vm_script))
    host.scp2node(vm_script, remote_file)


def initlogger(hostname):
    global logfile
    logname = "oak_create_db_vm_%s.log" % hostname
    logfile = os.path.join(cf.log_dir, logname)
    log = initlogging.initLogging("oak_db_vm", logfile)
    return log


def initlog(plog):
    oda_lib.initlog(plog)
    global log
    log = plog

def log_management(hostname):
    log = initlogger(hostname)
    initlog(log)

def main(host):
    exec_crdb_script (host)
    exec_crvm_scripts (host)



if __name__ == '__main__':
    arg = docopt(__doc__)
    print arg
    hostname = arg['-s']
    username = arg['-u']
    password = arg['-p']
    host = oda_lib.Oda_ha(hostname, username, password)
    #logfile_name = 'check_oak_create_db_vm_%s.log' % hostname
    #fp, out, err,log = cf.logfile_name_gen_open(logfile_name)
    log_management(hostname)
    if arg['crdb']:
        exec_crdb_script(host)
    if arg['crvm']:
        exec_crvm_scripts(host)
    if not arg['crdb'] and not arg['crvm']:
        exec_crdb_script(host)
        exec_crvm_scripts(host)
    print "Done, please check the log %s for details!" % logfile


