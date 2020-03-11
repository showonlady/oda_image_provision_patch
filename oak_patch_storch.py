#!/usr/bin/env python
#coding utf-8
#
# Copyright (c) 2018, Oracle and/or its affiliates. All rights reserved.
#
#    NAME
#      oak_patch_storch.py
#
#    DESCRIPTION
#      Path oak env to the latest version
#
#    NOTES
#
#
#    MODIFIED   (MM/DD/YY)
#    chqin    12/24/18 - Creation
#    chqin    02/07/20 - Modified
#


"""
Usage:
    oak_patch_storch.py -h
    oak_patch_storch.py -s <servername> [-u <username>] [-p <password>] [-v <version>][--base_version <187_188>]

Options:
    -h,--help       Show this help message
    -s <servername>  hostname of machine
    -u <username>  username [default: root]
    -p <password>  password [default: welcome1]
    -v <version>   The version number you want to patch
    --base_version <187_188>   The version number you want to be base, 18.7 or 18.8 [default: 18.7.0.0]
"""

from docopt import docopt
import oda_lib
import sys
import common_fun as cf
import oak_prepare_patch as o_p_p
import os, sys
import re
import random
import time
import logging
import initlogging
import oda_patch as o_p
import oak_patch as oak_patch

log_dir = cf.log_dir





def initlogger(hostname):
    global logfile
    logname = "oak_patch_storch_%s.log" % hostname
    logfile = os.path.join(log_dir, logname)
    log = initlogging.initLogging("oak_patch_storch", logfile, logging.WARN, logging.DEBUG)
    return log


def initlog(plog):
    oda_lib.initlog(plog)
    o_p_p.initlog(plog)
    o_p.initlog(plog)
    oak_patch.initlog(plog)
    global log
    log = plog


def log_management(hostname):
    log = initlogger(hostname)
    initlog(log)




if __name__ == '__main__':
    arg = docopt(__doc__)
    print arg
    hostname = arg['-s']
    username = arg['-u']
    password = arg['-p']
    log_management(hostname)
    host = oda_lib.Oda_ha(hostname, username, password)
    if arg['-v']:
        version = arg['-v']
    else:
        version = oda_lib.Oda_ha.Current_version
    base_version = arg["--base_version"]

    if cf.equal_version(host, version):
        log.info ("The system is already the latest version!")
    else:
        log.info ("Will patch the system!")
        oak_patch.main(host,version=version, base_version=base_version)
    # if not host.is_latest_or_not ():
    #     log.info ("Will patch the system!")
    #     oak_patch.main(host,version=version, base_version=base_version)
    # else:
    #     log.info("The system is already the latest version!")
    print "Done, please check the log %s for details!" % logfile