#!/usr/bin/env python
# -*- encoding=utf-8 -*-
#
# Copyright (c) 2018, Oracle and/or its affiliates. All rights reserved.
#
#    NAME
#      vm_deploy.py
#
#    DESCRIPTION
#      Deploy odabase, and deploy gi/rac on dom1
#
#    NOTES
#
#
#    MODIFIED   (MM/DD/YY)
#    chqin    08/07/18 - Creation
#

"""
Usage:
    vm_deploy.py -h
    vm_deploy.py  -s <servername> [-v <version>] [-u <username>] [-p <password>] [-o <jsonfile>]

Options:
    -h,--help       Show this help message
    -s <servername>  hostname of dom0
    -v <version>   the version you want to deploy
    -u <username>  username [default: root]
    -p <password>  password [default: welcome1]
    -o <jsonfile>   The onecommand file with path
"""


from docopt import docopt
import oda_lib
import common_fun as cf
import os
import sys
import logging
import initlogging
import pexpect
import datetime
import time
import oak_deploy
import re

def vm_deploy(*a):
    flag = 0
    host = a[0]
    version = a[1]
    version = cf.trim_version(version)
    if not check_dom1_exist_or_not(host):
        temp = scp_template_file(host, version)
        deploy_odabase(host, temp)
        time.sleep(300)
    else:
        log.info("The odabase is already deployed!")
    if len(a) == 3:
        onecmd_file = a[2]
    else:
        onecmd_file = oak_deploy.onecommand_file(host.hostname, version, 1)
    onecmd_file1 = scp_onecommand_to_dom0(host,onecmd_file)
    flag = deploy_dom1(host, onecmd_file1)
    return flag

def deploy_dom1(host, onecmd_file):
    flag = 0
    log_stamp = datetime.datetime.today().strftime("%Y%m%d")
    logfile = os.path.join(cf.log_dir, "dom1_girac_deploy_%s_%s.log" % (host.hostname, log_stamp))
    cmd = "ssh -o UserKnownHostsFile=/dev/null %s" % (host.hostname)
    A = open(logfile, "w")
    child = pexpect.spawn(cmd, logfile = A)
    child = login(child, host.password)
    child.expect(".*#")
    child.sendline("ssh 192.168.16.27")
    child = login(child, "welcome1")
    child.expect(".*#")
    child.sendline("scp 192.168.16.24:%s /tmp" % onecmd_file)
    child = login(child, "welcome1")
    child.expect("100", timeout=120)
    child.sendline ("/opt/oracle/oak/bin/oakcli copy -conf %s" % onecmd_file)
    child.expect("[Ss]uccess")
    child.expect(".*#")
    child.sendline("/opt/oracle/oak/onecmd/GridInst.pl -o -r 0-23")
    try:
        child.expect("The Log file is", timeout=9000)
        print "Successfully finished gi/rac deployment!"
        flag = 1
        log.info("Successfully finished gi/rac deployment!")
    except Exception as e:
        log.error("Fail to depoy the gi/rac on dom1! logfile:%s" % logfile)
    time.sleep(60)
    child.close()
    A.close()
    cf.covertlog(logfile)
    return flag


def login(child, password):
    i = child.expect(["continue connecting", 'password: ', pexpect.TIMEOUT],timeout=600)
    if i == 0:
        child.sendline("yes")
        child.expect("password")
        child.sendline("%s" % password)
    elif i == 1:
        child.sendline("%s" % password)
    else:
        print "timeout!"
        sys.exit(0)
    return child


def scp_onecommand_to_dom0(host,onecmd_file):
    hostname = host.hostname
    remote_dir = "/tmp"
    remote_file = os.path.join(remote_dir, os.path.basename(onecmd_file))
    host.scp2node(onecmd_file, remote_file)
    return remote_file


def check_dom1_exist_or_not(host):
    dom1name = "oakDom1"
    dom1_path = "ls /OVS/Repositories/odabaseRepo/VirtualMachines/oakDom1"
    cmd = "xm domid %s" % dom1name
    flag = 0
    result, err = host.ssh2node_job(cmd)
    if not err and result:
        flag =1
        return flag
    else:
        result, err = host.ssh2node_job(dom1_path)
        if not err:
            host.ssh2node("rm -rf /OVS/Repositories/odabaseRepo/VirtualMachines/oakDom1")
            print "Removed the path /OVS/Repositories/odabaseRepo/VirtualMachines/oakDom1"
    return flag




def deploy_odabase(host, temp):
    flag = 1
    cmd1 = "/opt/oracle/oak/bin/oakcli deploy oda_base"
    cmd = "ssh -o UserKnownHostsFile=/dev/null %s %s" % (host.hostname, cmd1)
    log_stamp = datetime.datetime.today().strftime("%Y%m%d")
    logfile = os.path.join(cf.log_dir, "odabase_deploy_%s_%s.log" % (host.hostname, log_stamp))
    A = open(logfile, "w")
    child = pexpect.spawn(cmd, logfile=A)
    i = child.expect(["continue connecting", 'password: ', pexpect.TIMEOUT])
    if i == 0:
        child.sendline("yes")
        child.expect("password")
        child.sendline("%s" % host.password)
    elif i == 1:
        child.sendline("%s" % host.password)
    else:
        print "timeout!"
        sys.exit(0)

    child.expect("template location:", timeout=600)
    child.sendline("%s" % temp)
    child.expect("CPU Cores")
    child.sendline("4")
    child.expect("memory in GB")
    child.sendline("120")
    child.expect("vlan networks")
    child.sendline('n')
    index = child.expect ([pexpect.TIMEOUT, "VNC password for oda_base"], timeout = 120)
    if index == 1:
        child.sendline ("n")
    try:
        child.expect("the odabase configuration information", timeout=7200)
    except Exception as e:
        log.error("Fail to deploy odabase! logfile: %s" % logfile)
        flag = 0
    try:
        child.expect ("the odabase configuration information", timeout=7200)
        log.info("Success deploy odabase! logfile: %s" % logfile)
    except Exception as e:
        log.error ("Fail to deploy odabase! logfile: %s" % logfile)
        flag = 0
    time.sleep(300)
    child.close()
    A.close()
    cf.covertlog(logfile)
    if flag == 0:
        sys.exit(0)
    cmd = "rm -rf /tmp/templateBuild*"
    host.ssh2node(cmd)

def scp_template_file(host, version):
    remote_dir = '/tmp'
    template_file = '/chqin/ODA%s/templateBuild*' % version
    file, err = cf.exc_cmd_new("ls %s" % template_file)
    if err != 0:
        print file, err
        log.error("Could not find the template under dir %s" % template_file)
        sys.exit(0)
    files = file.split()
    if len(files) != 1:
        log.error("Found not only one template under the dir %s" % template_file)
        sys.exit(0)
    else:
        temp = files[0].strip()
    remote_file = os.path.join(remote_dir, os.path.basename(temp))
    host.scp2node(temp, remote_file)
    return remote_file


def log_management(hostname):
    global logfile_vm
    logname = "Dom1_deploy_%s.log" % hostname
    logfile_vm = os.path.join(cf.log_dir, logname)
    log = initlogging.initLogging("dom1_deploy", logfile_vm, logging.WARN, logging.DEBUG)
    initlog(log)


def initlog(plog):
    oda_lib.initlog(plog)
    oak_deploy.initlog(plog)
    global log
    log = plog


def get_version(host):
    oak_version = host.ssh2node("rpm -qa|grep oak")
    try:
        version = re.search('oakdom0-(.*)_LI',oak_version).group(1)
    except Exception as e:
        log.error("Could not get the oak version: %s" % oak_version)
        sys.exit(0)
    return version


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
        version = get_version(host)

    if arg['-o']:
        jsonfile = arg['-o']
        vm_deploy(host, version, jsonfile)
    else:
        vm_deploy(host, version)
    print "Please check the log %s for details!" % logfile_vm