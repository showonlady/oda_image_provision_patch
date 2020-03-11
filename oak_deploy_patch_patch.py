#!/usr/bin/env python
#coding utf-8
#
# Copyright (c) 2018, Oracle and/or its affiliates. All rights reserved.
#
#    NAME
#      oak_deploy_patch_patch.py
#
#    DESCRIPTION
#      deploy, create multiple databases, patch on oak env for both bm and vm
#
#    NOTES
#
#
#    MODIFIED   (MM/DD/YY)
#    chqin    01/10/19 - Creation
#    chqin    03/10/20 - Modified, add two new options for the patch, add 18.7/18.8 as the base version

#

"""
Usage:
    oak_deploy_patch_patch.py -h
    oak_deploy_patch_patch.py [nopatch] -s <servername> [-u <username>] [-p <password>] [--to_version <version>] [--base_version <187_188>]

Options:
    -h,--help       Show this help message
    -s <servername>  hostname of machine, if no odabase, please give the dom0 ip instead
    -u <username>  username [default: root]
    -p <password>  password [default: welcome1]
    nopatch    Don't do the patch, only prepare the environment
    --to_version <version>   The version number you want to patch
    --base_version <187_188>   The version number you want to be base, 18.7 or 18.8 [default: 18.7.0.0]
"""

from docopt import docopt
import oak_patch
import oak_deploy
import vm_deploy
import image
import configure_firstnet
import oak_create_db
import oda_lib
import simplejson
import time
import common_fun as cf
import sys
import logging
import initlogging
import os
import re

log_dir = cf.log_dir


def deploy(host):
    if is_dom0(host):
        version = vm_deploy.get_version (host)
        flag =  vm_deploy.vm_deploy(host, version)
        if flag == 0:
            host_odabase = convert_dom0_to_dom1(host)
            image.cleanup(host_odabase.hostname, host_odabase.username, host_odabase.password)
            time.sleep(300)
            flag = vm_deploy.vm_deploy(host, version)
    else:
        if host.is_deployed_or_not():
            log.info("The system is already deployed!")
            return 1
        else:
            flag = oak_deploy.oak_deploy(host)
            if flag == 0:
                version = host.system_version ()
                if not host.is_vm_or_not():
                    image.cleanup(host.hostname, host.username, host.password)
                    time.sleep (300)
                    ips = configure_firstnet.configure_firstnet(host.hostname, version, False)
                    host = oda_lib.Oda_ha (ips[0], "root", "welcome1")
                    flag = oak_deploy.oak_deploy(host)
                else:
                    image.cleanup(host.hostname, host.username, host.password)
                    time.sleep (300)
                    dom0_ip = cf.dom0_name(host.hostname)
                    host_dom0 = oda_lib.Oda_ha(dom0_ip[0], "root", "welcome1")
                    flag = vm_deploy.vm_deploy(host_dom0, version)
    return flag

def is_dom0(host):
    cmd = "/opt/oracle/oak/bin/oakcli show env_hw"
    env = host.ssh2node(cmd)
    if re.search("DOM0", env, re.I):
        return 1
    else:
        return 0

def convert_dom0_to_dom1(host):
    # with open ('/chqin/new_test/venv/allmachine.json', 'r') as f:
    #     host_info = simplejson.load(f)
    host_info = cf.host_all
    host_str = host.hostname.split(".")[0][:-1]
    for i in host_info.keys():
        if re.search(host_str, i):
            hostname = i
            break;
    try:
        host = oda_lib.Oda_ha(hostname, host.username, host.password)
    except Exception as e:
        log.error("Fail to connect to odabase!")
        sys.exit(0)
    return host

def create_db(host):
    if is_dom0(host):
        host = convert_dom0_to_dom1(host)
    cmd = "/opt/oracle/oak/bin/oakcli show dbhomes|grep -i OraDb|wc -l"
    out, err = host.ssh2node_job(cmd)
    if int(out) < 3:
        oak_create_db.main(host)
    else:
        log.info("There are %s databases, will not create databases!" % int(out))

def deploy_patch(host, nopatchflag = False,version = oda_lib.Oda_ha.Current_version, base_version = "18.7.0.0"):
    if host.is_dcs_or_oak():
        log.warn("This is an dcs stack, please run 'python deploy_patch_patch.py' to do the patch!")
        sys.exit(0)
    flag = deploy(host)
    if flag:
        log.info("Successfully deployed the system!")
        host = oda_lib.Oda_ha(host.hostname, host.username, host.password)
        if is_dom0(host):
            host = convert_dom0_to_dom1(host)
        else:
            host = oda_lib.Oda_ha(host.hostname, host.username, host.password)
        log.info("Will create multiple databases on host %s!" % host.hostname)
        create_db(host)
        if not cf.equal_version(host, version):
            log.info("Will patch the system!")
            oak_patch.main(host, nopatchflag, version, base_version)
        else:
            log.info("The system is already the version %s!" % version)


def initlogger(hostname):
    global logfile
    logname = "oak_deploy_and_patch_%s.log" % hostname
    logfile = os.path.join(log_dir, logname)
    log = initlogging.initLogging("oak_deploy_patch", logfile, logging.WARN, logging.DEBUG)
    return log


def initlog(plog):
    oda_lib.initlog(plog)
    oak_patch.initlog(plog)
    oak_deploy.initlog(plog)
    vm_deploy.initlog(plog)
    oak_create_db.initlog(plog)
    image.initlog(plog)
    configure_firstnet.initlog(plog)
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
    nopatchflag = arg['nopatch']
    log_management (hostname)
    host = oda_lib.Oda_ha (hostname, username, password)
    if arg['--to_version']:
        to_version = arg["--to_version"]
    else:
        to_version = oda_lib.Oda_ha.Current_version
    base_version = arg["--base_version"]

    deploy_patch(host, nopatchflag, to_version, base_version)
    print "Done, please check the log %s for details!" % logfile