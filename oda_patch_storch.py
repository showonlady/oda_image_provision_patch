#!/usr/bin/env python
#encoding utf-8
"""
Usage:
    oda_patch_storch.py -h
    oda_patch_storch.py [nopatch] -s <servername> [-u <username>] [-p <password>]

Options:
    -h,--help       Show this help message
    -s <servername>  hostname of machine, if vlan,use ip instead
    -u <username>  username [default: root]
    -p <password>  password [default: welcome1]
    nopatch    Don't do the patch, only prepare the environment
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
import os
import deploy_patch_patch as d_p_p
log_dir = cf.log_dir

###########################################################
def dcs_patch(host, nopatchflag = False):
    if not host.is_dcs_or_oak():
        sys.exit(0)

    need_to_12_version = ['12.1.2.8','12.1.2.8.1','12.1.2.9','12.1.2.10','12.1.2.11']
    need_to_183_version = ['12.1.2.12', '12.2.1.1','12.2.1.2','12.2.1.3','12.2.1.4']
    need_to_187_version = ['12.1.2.12', '12.2.1.1','12.2.1.2','12.2.1.3','12.2.1.4',"18.3","18.5"]

    no_patch_version = ['18.2.1',"19.4","19.5"]
    s_v = host.system_version()
    s_v = cf.trim_version(s_v)
    if s_v in need_to_12_version:
        o_p.dcs_patch(host, "12.1.2.12.0")
        o_p.simple_update_server(host,"12.1.2.12.0")
        time.sleep(300)
        cf.wait_until_ping(host.hostname)
        host = oda_lib.Oda_ha(host.hostname, host.username, host.password)
        o_p.simple_update_dbhome(host, "12.1.2.12.0")

    s_v = host.system_version()
    s_v = cf.trim_version(s_v)
    if s_v in need_to_183_version:
        o_p.dcs_patch(host, "18.3.0.0")
        o_p.simple_update_server(host,"18.3.0.0")
        time.sleep(300)
        cf.wait_until_ping(host.hostname)
        host = oda_lib.Oda_ha(host.hostname, host.username, host.password)
        #o_p.simple_update_dbhome(host, "18.3.0.0")

    s_v = host.system_version()
    s_v = cf.trim_version(s_v)
    # if s_v in need_to_187_version:
    #     o_p.new_dcs_patch(host, "18.7.0.0")
    #     host = oda_lib.Oda_ha (host.hostname, host.username, host.password)
    #     o_p.simple_update_server(host,"18.7.0.0")
    #     time.sleep(300)
    #     cf.wait_until_ping(host.hostname)
    #     host = oda_lib.Oda_ha(host.hostname, host.username, host.password)
    ####if specify the nopatchflag, then don't need to do the patch
    if nopatchflag:
        print "Will not patch to the latest version!"
        log.info("Will not patch to the latest version!")
        return 0

    if not host.is_latest_or_not() and s_v not in no_patch_version:
        if cf.trim_version(host.Current_version) in ["18.3","18.5"]:
            o_p.dcs_patch(host)
        else:
            o_p.new_dcs_patch(host)
        host = oda_lib.Oda_ha(host.hostname, host.username, host.password)
        o_p.server_patch(host)
        print "Successfully patch server to latest version!"
        time.sleep(300)
        cf.wait_until_ping(host.hostname)
        host2 = oda_lib.Oda_ha(host.hostname, host.username, host.password)
        o_p.dbhome_patch(host2)
        time.sleep(300)
        o_p.storage_patch(host2)
        time.sleep(600)
        cf.wait_until_ping(host2.hostname)
    else:
        print "Will not patch the host!"
        log.info("The host version is %s, will not patch the host!" %s_v)
#######################################################################

def main(arg):
    hostname = arg['-s']
    username = arg['-u']
    password = arg['-p']
    nopatchflag = arg['nopatch']
    # logfile_name = 'check_deploy_patch_%s.log' % hostname
    # fp, out, err,log = cf.logfile_name_gen_open(logfile_name)
    log_management(hostname)
    host = oda_lib.Oda_ha(hostname, username, password)
    d_p_p.dcs_patch(host, nopatchflag)
    #cf.closefile(fp, out, err)
    print "Done, please check the log %s for details!" % logfile


def initlogger(hostname):
    global logfile
    logname = "oda_patch_storch_%s.log" % hostname
    logfile = os.path.join(log_dir, logname)
    log = initlogging.initLogging("dcs_patch_storch", logfile, logging.WARN, logging.DEBUG)
    return log


def initlog(plog):
    oda_lib.initlog(plog)
    o_p.initlog(plog)
    o_d.initlog(plog)
    c_m_d.initlog(plog)
    d_p_p.initlog(plog)
    global log
    log = plog


def log_management(hostname):
    log = initlogger(hostname)
    initlog(log)



if __name__ == '__main__':
    arg = docopt(__doc__)
    print arg

    main(arg)
