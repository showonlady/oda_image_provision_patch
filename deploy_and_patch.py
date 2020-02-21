#!/usr/bin/env python
#encoding utf-8
"""
Usage:
    deploy_and_patch.py -h
    deploy_and_patch.py -s <servername> [-u <username>] [-p <password>]

Options:
    -h,--help       Show this help message
    -v,--version     Show version
    -s <servername>  hostname of machine, if vlan,use ip instead
    -u <username>  username [default: root]
    -p <password>  password [default: welcome1]
"""
from docopt import docopt
import oda_patch as o_p
import oda_deploy as o_d
import oda_lib
import time
import common_fun as cf
import create_multiple_db as c_m_d
import sys
import logging
import initlogging

def provision_patch(host):
    if not host.is_deployed_or_not():
        o_d.oda_deploy(host)
    cf.extend_space_u01(host)
    create_db(host)
    if not host.is_latest_or_not():
        o_p.dcs_patch(host)
        o_p.server_patch(host)
        time.sleep(300)
        cf.wait_until_ping(host.hostname)
        host2 = oda_lib.Oda_ha(host.hostname, host.username, host.password)
        o_p.dbhome_patch(host2)


def create_db(host):
    cmd = "/opt/oracle/dcs/bin/odacli list-dbhomes|grep -i OraDb|wc -l"
    out = host.ssh2node(cmd)
    if int(out) < 3:
        c_m_d.create_multiple_db(host)
    else:
        pass



def patch_deploy(host):
    if not host.is_latest_or_not():
        o_p.dcs_patch(host)
        o_p.server_patch(host)
        time.sleep(300)
        cf.wait_until_ping(host.hostname)
        host = oda_lib.Oda_ha(host.hostname, host.username, host.password)
    if not host.is_deployed_or_not():
        o_d.oda_deploy(host)



def initlogger(hostname):
    global logfile
    logname = "deploy_and_patch_%s.log" % hostname
    logfile = os.path.join(log_dir, logname)
    log = initlogging.initLogging("deploy_patch", logfile, logging.WARN, logging.DEBUG)
    return log


def initlog(plog):
    oda_lib.initlog(plog)
    o_p.initlog(plog)
    o_d.initlog(plog)
    c_m_d.initlog(plog)
    global log
    log = plog


def log_management(hostname):
    log = initlogger(hostname)
    initlog(log)


def main(hostname,username,password ):
    #logfile_name = 'check_deploy_patch_%s.log' % hostname
    #fp, out, err,log = cf.logfile_name_gen_open(logfile_name)
    log_management(hostname)
    host = oda_lib.Oda_ha(hostname, username, password)
    provision_patch(host)
    #patch_deploy(host)
    print "Done, please check the log %s for details!" % logfile



if __name__ == '__main__':
    arg = docopt(__doc__)
    print arg
    hostname = arg['-s']
    username = arg['-u']
    password = arg['-p']
    #main("scaoda7s005", 'root','welcome1')
    main(hostname, username, password)
