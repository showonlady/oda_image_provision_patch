#!/usr/bin/env python
#encoding utf-8
"""
Usage:
    oda_patch_storch.py -h
    oda_patch_storch.py [nopatch] -s <servername> [-u <username>] [-p <password>][-v <version>][--base_version <187_188>]

Options:
    -h,--help       Show this help message
    -s <servername>  hostname of machine, if vlan,use ip instead
    -u <username>  username [default: root]
    -p <password>  password [default: welcome1]
    -v <version>   The version number you want to patch
    --base_version <187_188>   The version number you want to be base, 18.7 or 18.8 [default: 18.7.0.0]
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


def main(arg):
    hostname = arg['-s']
    username = arg['-u']
    password = arg['-p']
    nopatchflag = arg['nopatch']
    # logfile_name = 'check_deploy_patch_%s.log' % hostname
    # fp, out, err,log = cf.logfile_name_gen_open(logfile_name)
    log_management(hostname)
    host = oda_lib.Oda_ha(hostname, username, password)
    base_version = arg["--base_version"]
    if arg['-v']:
        version = arg['-v']
    else:
        version = oda_lib.Oda_ha.Current_version

    if cf.equal_version(host, version):
        log.info("The system is already the latest version!")
    else:
        log.info ("Will patch the system!")
        d_p_p.dcs_patch (host, nopatchflag, version, base_version)

    # if not host.is_latest_or_not ():
    #     log.info ("Will patch the system!")
    #     d_p_p.dcs_patch (host, nopatchflag, version, base_version)
    # else:
    #     log.info("The system is already the latest version!")

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
