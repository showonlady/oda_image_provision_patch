#!/usr/bin/env python
#coding utf-8
#
# Copyright (c) 2018, Oracle and/or its affiliates. All rights reserved.
#
#    NAME
#      deploy_patch_patch.py
#
#    DESCRIPTION
#      Path dcs env to the latest version
#
#    NOTES
#
#
#    MODIFIED   (MM/DD/YY)
#    chqin    12/24/18 - Creation
#    chqin    03/10/20 - Add a new 18.7/18.8 as the base version
#

"""
Usage:
    deploy_patch_patch.py -h
    deploy_patch_patch.py [nopatch] -s <servername> [-u <username>] [-p <password>] [-v <version>] [--pbd]
    deploy_patch_patch.py [nopatch] -s <servername> [-u <username>] [-p <password>] [-v <version>] [--base_version <187_188>]

Options:
    -h,--help       Show this help message
    -s <servername>  hostname of machine, if vlan,use ip instead
    -u <username>  username [default: root]
    -p <password>  password [default: welcome1]
    -v <version>   The version number you want to patch
    --pbd   patch before deployment
    nopatch    Don't do the patch, only prepare the environment
    --base_version <187_188>   The version number you want to be base, 18.7 or 18.8 [default: 18.7.0.0]

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
log_dir = cf.log_dir

####This function is abandoned####
def provision_patch(host, nopatchflag = False):
    if not host.is_dcs_or_oak():
        sys.exit(0)
    if not host.is_deployed_or_not():
        o_d.oda_deploy_new(host)
        host = oda_lib.Oda_ha(host.hostname, host.username, host.password)
    cf.extend_space_u01(host)
    cf.extend_space_opt(host)
    create_db(host)
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


def provision_patch2(host, nopatchflag = False, version=oda_lib.Oda_ha.Current_version, base_version="18.7.0.0"):
    if cf.trim_version(base_version) not in ["18.7", "18.8"]:
        log.error("The base version should be 18.7 or 18.8!")
        sys.exit(0)

    if not host.is_dcs_or_oak():
        sys.exit(0)
    if not host.is_deployed_or_not():
        o_d.oda_deploy_new(host)
        host = oda_lib.Oda_ha(host.hostname, host.username, host.password)
    cf.extend_space_u01(host)
    cf.extend_space_opt(host)
    create_db(host)
    if not cf.equal_version (host, version):
        log.info ("Will patch the system!")
        dcs_patch (host, nopatchflag, version, base_version)
    else:
        log.info ("The system is already the version %s!" % version)


def dcs_patch(host, nopatchflag = False, version=oda_lib.Oda_ha.Current_version, base_version="18.7.0.0"):
    if cf.trim_version(base_version) not in ["18.7", "18.8"]:
        log.error("The base version should be 18.7 or 18.8!")
        sys.exit(0)

    need_to_12_version = ['12.1.2.8', '12.1.2.8.1', '12.1.2.9', '12.1.2.10', '12.1.2.11']
    need_to_183_version = ['12.1.2.12', '12.2.1.1', '12.2.1.2', '12.2.1.3', '12.2.1.4']
    need_to_187_version = ["18.3", "18.5"]
    need_to_188_version = ["18.3", "18.5", "18.7"]

    no_patch_version = ['18.2.1', "19.4", "19.5"]

    s_v = host.system_version ()
    s_v = cf.trim_version (s_v)
    if s_v in need_to_12_version:
        o_p.dcs_patch (host, "12.1.2.12.0")
        o_p.simple_update_server (host, "12.1.2.12.0")
        time.sleep (300)
        cf.wait_until_ping (host.hostname)
        host = oda_lib.Oda_ha (host.hostname, host.username, host.password)
        o_p.simple_update_dbhome (host, "12.1.2.12.0")

    s_v = host.system_version ()
    s_v = cf.trim_version (s_v)
    if s_v in need_to_183_version:
        o_p.dcs_patch (host, "18.3.0.0")
        o_p.simple_update_server (host, "18.3.0.0")
        time.sleep (300)
        cf.wait_until_ping (host.hostname)
        host = oda_lib.Oda_ha (host.hostname, host.username, host.password)
        # o_p.simple_update_dbhome(host, "18.3.0.0")
    ver = cf.trim_version(version)
    if ver == '18.3':
        print "Already patched to the latest version 18.3!"
        log.info("Already patched to the latest version 18.3!")
        return 0

    ###18.7/18.8 will be new base, we need to first updated to 18.7 or 18.8

    s_v = host.system_version ()
    s_v = cf.trim_version (s_v)
    if cf.trim_version(base_version) == "18.7":
        need_to_base_version = need_to_187_version
    else:
        need_to_base_version = need_to_188_version

    if s_v in need_to_base_version:
        o_p.new_dcs_patch(host, base_version)
        host = oda_lib.Oda_ha (host.hostname, host.username, host.password)
        o_p.simple_update_server(host,base_version)
        time.sleep(300)
        cf.wait_until_ping(host.hostname)
        host = oda_lib.Oda_ha(host.hostname, host.username, host.password)
    if ver == cf.trim_version(base_version):
        print "Already patched to the version %s!" % base_version
        log.info("Already patched to the version %s!" % base_version)
        return 0

    ###if specify the nopatchflag, then don't need to do the patch
    if nopatchflag:
        print "Will not patch to the latest version!"
        log.info ("Will not patch to the latest version!")
        return 0

    s_v = host.system_version ()
    s_v = cf.trim_version (s_v)

    if not cf.equal_version (host,version) and s_v not in no_patch_version:
        if ver in ["18.3", "18.5"]:
            o_p.dcs_patch (host, version)
        else:
            o_p.new_dcs_patch (host, version)
        host = oda_lib.Oda_ha (host.hostname, host.username, host.password)
        o_p.server_patch (host, version)
        print "Successfully patch server to %s version!" % version
        time.sleep (300)
        cf.wait_until_ping (host.hostname)
        host2 = oda_lib.Oda_ha (host.hostname, host.username, host.password)
        o_p.dbhome_patch (host2, version)
        time.sleep (300)
        o_p.storage_patch (host2, version)
        time.sleep (600)
        cf.wait_until_ping (host2.hostname)
    else:
        print "Will not patch the host!"
        log.info ("The host version is %s, will not patch the host to version %s" % (s_v, version))


def create_db(host):
    cmd = "/opt/oracle/dcs/bin/odacli list-dbhomes|grep -i OraDb|wc -l"
    out, err = host.ssh2node_job(cmd)
    if int(out) < 3:
        c_m_d.create_multiple_db(host)
    else:
        pass



def patch_deploy(host):
    need_to_12_vesion = ['12.1.2.8', '12.1.2.8.1', '12.1.2.9', '12.1.2.10', '12.1.2.11']
    need_to_183_version = ['12.1.2.12', '12.2.1.1','12.2.1.2','12.2.1.3','12.2.1.4']

    s_v = host.system_version()
    s_v = cf.trim_version(s_v)
    if s_v in need_to_12_vesion:
        o_p.dcs_patch(host, "12.1.2.12.0")
        o_p.simple_update_server(host, "12.1.2.12.0")
        time.sleep(300)
        cf.wait_until_ping(host.hostname)
        host = oda_lib.Oda_ha(host.hostname, host.username, host.password)

    s_v = host.system_version()
    s_v = cf.trim_version(s_v)
    if s_v in need_to_183_version:
        o_p.dcs_patch(host, "18.3.0.0")
        o_p.simple_update_server(host,"18.3.0.0")
        time.sleep(300)
        cf.wait_until_ping (host.hostname)
        host = oda_lib.Oda_ha (host.hostname, host.username, host.password)

    s_v = host.system_version()
    s_v = cf.trim_version(s_v)
    if s_v in need_to_187_version:
        o_p.new_dcs_patch(host, "18.7.0.0")
        o_p.simple_update_server(host,"18.7.0.0")
        time.sleep(300)
        cf.wait_until_ping(host.hostname)
        host = oda_lib.Oda_ha(host.hostname, host.username, host.password)

    if not host.is_latest_or_not():
        o_p.dcs_patch(host)
        host = oda_lib.Oda_ha(host.hostname, host.username, host.password)
        if not o_p.update_server(host, version = oda_lib.Oda_ha.Current_version):
            log.error("update server failed")
            sys.exit(0)
        time.sleep(300)
        cf.wait_until_ping(host.hostname)
        host2 = oda_lib.Oda_ha(host.hostname, host.username, host.password)
        o_p.storage_patch(host2)
        time.sleep(600)
        cf.wait_until_ping(host2.hostname)

    if not host.is_deployed_or_not():
        o_d.oda_deploy_new(host)




def main(arg):
    hostname = arg['-s']
    username = arg['-u']
    password = arg['-p']
    nopatchflag = arg['nopatch']
    base_version = arg["--base_version"]
    # logfile_name = 'check_deploy_patch_%s.log' % hostname
    # fp, out, err,log = cf.logfile_name_gen_open(logfile_name)
    log_management(hostname)
    host = oda_lib.Oda_ha(hostname, username, password)
    if arg['-v']:
        version = arg['-v']
    else:
        version = oda_lib.Oda_ha.Current_version
    if arg['--pbd']:
        patch_deploy(host)
    else:
        provision_patch2(host, nopatchflag, version, base_version)
    #cf.closefile(fp, out, err)
    print "Done, please check the log %s for details!" % logfile


def initlogger(hostname):
    global logfile
    logname = "deploy_and_patch_%s.log" % hostname
    logfile = os.path.join(log_dir, logname)
    log = initlogging.initLogging("deploy_patch_patch", logfile, logging.WARN, logging.DEBUG)
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



if __name__ == '__main__':
    arg = docopt(__doc__)
    print arg
    main(arg)
