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
    oak_patch_storch.py -s <servername> [-u <username>] [-p <password>]

Options:
    -h,--help       Show this help message
    -s <servername>  hostname of machine
    -u <username>  username [default: root]
    -p <password>  password [default: welcome1]
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
import oak_patch

log_dir = cf.log_dir
need_to_183_version = ['12.1.2.12', '12.2.1.1', '12.2.1.2', '12.2.1.3', '12.2.1.4']
need_to_187_version = ['18.3', '18.5']

def server_patch(host, version=oda_lib.Oda_ha.Current_version):
    o_p_p.main(host, version)
    cmd = "/opt/oracle/oak/bin/oakcli update -patch %s --server" % version
    logfile = cf.oak_server_patch(host, cmd)
    cmd = "egrep -i 'fail|error|warning' %s|egrep -v 'Permanently added|no fail|ILOM update will not be performed'" % logfile
    result = cf.exc_cmd(cmd)
    if result:
        return 0
    else:
        return 1

def oak_dbhome_patch(host, version=oda_lib.Oda_ha.Current_version):
    cmd = "/opt/oracle/oak/bin/oakcli update -patch %s --database" % version
    logfile = cf.oak_dbhome_patch (host, cmd)
    cmd = "egrep -i 'fail|error|warning' %s|egrep -v 'Permanently added|no fail'" % logfile
    result = cf.exc_cmd (cmd)
    if result:
        return 0
    else:
        return 1




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

def remove_clone(host):
    cmd = "rm -rf /opt/oracle/oak/pkgrepos/orapkgs/DB/*/Base/*tar.gz"
    host.ssh2node(cmd)
    node2 = cf.node2_name(host.hostname)
    host2 = oda_lib.Oda_ha(node2, host.username, host.password)
    host2.ssh2node(cmd)

def main(host, nopatchflag = False, version = oda_lib.Oda_ha.Current_version):
    s_v = host.system_version ()
    a = cf.trim_version (s_v)
    if not host.is_vm_or_not():
        cf.extend_space_u01(host)
        cf.extend_space_opt(host)
    else:
        remove_clone(host)
    ###If the version is 12.1.2.12, we first patch it to 12.2.1.4
    # if a == "12.1.2.12":
    #     if server_patch (host, "12.2.1.4.0"):
    #         print "Successfully patch the host to 12.2.1.4!"
    #         log.info ("Successfully patch the host to 12.2.1.4!")
    #     else:
    #         log.error ("Fail to patch the host to 12.2.1.4!")
    #         sys.exit (0)
    #     time.sleep (600)
    #     cf.wait_until_ping (host.hostname)
    #     host = oda_lib.Oda_ha (host.hostname, host.username, host.password)
    ####################################################################

    if a in need_to_183_version:
        if server_patch(host, "18.3.0.0"):
            print "Successfully patch the host to 18.3!"
            log.info("Successfully patch the host to 18.3!")
        else:
            log.error("Fail to patch the host to 18.3!")
            sys.exit (0)
        time.sleep(600)
        cf.wait_until_ping (host.hostname)
        host = oda_lib.Oda_ha(host.hostname, host.username, host.password)
# ###18,7 will be new base, we need to first updated to 18,7
#     s_v = host.system_version ()
#     a = cf.trim_version (s_v)
#     if a in need_to_187_version:
#         if host.is_vm_or_not ():
#             if server_patch (host, "18.7.0.0"):
#                 print "Successfully patch the host to 18.7.0.0!"
#                 log.info ("Successfully patch the host to 18.7.0.0!")
#             else:
#                 log.error ("Fail to patch the host to 18.7.0.0!")
#                 sys.exit (0)
#             time.sleep (600)
#             cf.wait_until_ping (host.hostname)
#
#         elif host.is_dcs_or_oak ():
#             o_p.new_dcs_patch (host, "18.7.0.0")
#             host = oda_lib.Oda_ha (host.hostname, host.username, host.password)
#             o_p.simple_update_server (host, "18.7.0.0")
#             time.sleep (300)
#             cf.wait_until_ping (host.hostname)
#             host = oda_lib.Oda_ha (host.hostname, host.username, host.password)
#         else:
#             log.error("It is not a vm env or a dcs stack!")

    if nopatchflag:
        print "Will not patch to the latest version!"
        log.info("Will not patch to the latest version!")
        return 0

    ver = cf.trim_version(version)
    if ver == '18.3':
        print "Already patched to the latest version 18.3!"
        log.info("Already patched to the latest version 18.3!")
        return 0

    # ver = cf.trim_version(version)
    # if ver == '18.7':
    #     print "Already patched to the latest version 18.7!"
    #     log.info("Already patched to the latest version 18.7!")
    #     return 0

    if host.is_vm_or_not():
        if server_patch(host,version):
            print "Successfully patch the host to the latest version!"
            log.info ("Successfully patch the host to the latest version!")
        else:
            log.error ("Fail to patch the host to the latest version!")
            sys.exit(0)
        time.sleep (600)
        cf.wait_until_ping (host.hostname)
        host = oda_lib.Oda_ha (host.hostname, host.username, host.password)
        if oak_dbhome_patch(host):
            print "Successfully patch the dbhome to the latest version!"
            log.info ("Successfully patch the dbhome to the latest version!")
        else:
            log.error ("Fail to patch the dbhome to the latest version!")

    elif host.is_dcs_or_oak():
        if not host.is_latest_or_not ():
            o_p.new_dcs_patch (host,version)
            host = oda_lib.Oda_ha (host.hostname, host.username, host.password)
            o_p.server_patch (host,version)
            time.sleep (500)
            cf.wait_until_ping (host.hostname)
            host2 = oda_lib.Oda_ha (host.hostname, host.username, host.password)
            o_p.dbhome_patch (host2,version)

    else:
        pass




if __name__ == '__main__':
    arg = docopt(__doc__)
    print arg
    hostname = arg['-s']
    username = arg['-u']
    password = arg['-p']
    log_management(hostname)
    host = oda_lib.Oda_ha(hostname, username, password)
    if not host.is_latest_or_not ():
        log.info ("Will patch the system!")
        version = oda_lib.Oda_ha.Current_version
        oak_patch.main(host,version=version)
    else:
        log.info("The system is already the latest version!")
    print "Done, please check the log %s for details!" % logfile