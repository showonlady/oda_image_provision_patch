#!/usr/bin/env python
# -*- coding:UTF-8 -*-
#
# Copyright (c) 2018, Oracle and/or its affiliates. All rights reserved.
#
#    NAME
#      odaadmcli.py
#
#    DESCRIPTION
#      test odaadmcli command
#
#    NOTES
#      odaadmcli show/stordiag
#
#    MODIFIED   (MM/DD/YY)
#    weiwei    09/07/18 - Creation
#
"""
Usage:
 odaadmcli.py -s <hostname> [-u <username>] [-p <password>]

Options:
  -h, --help  Show this screen
  -s <hostname>  hostname
  -u <username>  username [default: root]
  -p <password>  password [default: welcome1]
"""


import os
import random
import oda_lib
from docopt import docopt
import common_fun as cf
import logging
import initlogging
import pexpect
import datetime

ODAADMCLI = "/opt/oracle/oak/bin/odaadmcli "


def odaadmcli(host):
    show_object = ['disk', 'diskgroup', 'fs', 'raidsyncstatus', 'controller', 'env_hw', 'server',
                   'processor', 'memory', 'iraid', 'power', 'cooling', 'network','storage']
    for i in show_object:
        show(i,'-h')
        show(i, ' ')
        if(i == 'disk'):
            show(i, '-shared')
            show(i, '-local')
            disk_name()
            show_disk()
        if(i == 'diskgroup'):
            show_diskgroup()
        if(i == 'controller'):
            controllernum = run_cmd(ODAADMCLI + "show storage | awk -F: '/controllers/{print $2}'")
            if not(int(controllernum) == 0):
                for num in range(0, int(controllernum)):
                 show(i, bytes(num))
        if(i == 'storage'):
            show(i, '-errors')

    stordiag(host)


def show(object,options):
    cmd = ODAADMCLI +'show '+ object + ' ' + options
    result = run_cmd(cmd)
    return result


def show_disk():
    cmd1 = ODAADMCLI + "show disk | awk 'NR>2{print $4}'"
    cmd2 = ODAADMCLI + "show disk | awk 'NR>2{print $5}'"
    result1 = run_cmd(cmd1)
    result2 = run_cmd(cmd2)
    num = len(result1.split())
    if result1:
        state = result1.split()
        #print len(state)
        for i in state:
            if not (i == 'ONLINE'):
                logger.error("Disk is not ONLINE!")
    if result2:
        detail = result2.split()
        for i in detail:
            if not (i == 'Good'):
                logger.error("Disk is not Good!")
    if diskname:
        cmd3 = ODAADMCLI + "show disk " + diskname +" -all"
        cmd4 = ODAADMCLI + "show disk " + diskname + " -getlog"
        run_cmd(cmd3)
        run_cmd(cmd4)
    if not host.is_ha_not():
        cmd5 = "fwupdate list controller | grep 'NVMe'| wc -l"
        num1 = int(run_cmd(cmd5))
        if not (num == num1):
            logger.error("The number of disks is incorrect!")
    else:
        cmd6 = "fwupdate list disk | grep 'c1d' | wc -l "
        num2 = int(run_cmd(cmd6))
        if not (num == num2):
            logger.error("The number of disks is incorrect!")

def show_diskgroup():
    cmd1 = ODAADMCLI + "show diskgroup | awk 'NR>2'"
    result1 = run_cmd(cmd1)
    dgname = result1.split()
    for i in dgname :
        cmd2= ODAADMCLI + "show diskgroup " + i
        result2 = run_cmd(cmd2)
        if result2 :
            cmd3 = cmd2 + " | awk 'NR>2{print $4}'"
            cmd4 = cmd2 + " | awk 'NR>2{print $5}'"
            result3 = run_cmd(cmd3)
            result4 = run_cmd(cmd4)
            if result3:
                state = result3.split()
                for i in state:
                    if not (i == 'ONLINE'):
                        logger.error("Disk is not ONLINE!")
            if result4:
                detail = result4.split()
                for i in detail:
                    if not (i == 'Good'):
                        logger.error("Disk is not Good!")


def stordiag(host):
    cmd1 = ODAADMCLI + 'stordiag -h'
    run_cmd(cmd1)
    if host.is_ha_not():
        child = pexpect.spawn("ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@%s" % (host.hostname))
        child.expect('[Pp]assword: ')
        child.sendline(password)
        child.expect(' ')
        child.sendline("/opt/oracle/oak/bin/odaadmcli stordiag %s" % diskname)
        if not child.expect('password: ', timeout=1000):
            child.sendline(password)
            logger.info('%s %s' % (child.before, child.after))
            child.expect('password: ', timeout=1000)
            child.sendline(password)
            logger.info('%s %s' % (child.before, child.after))
            child.expect('password: ', timeout=1000)
            child.sendline(password)
            logger.info('%s %s' % (child.before, child.after))
            child.expect_exact('.log', timeout=1000)
            logger.info('%s %s' % (child.before, child.after))
        else:
            child.expect_exact('.log', timeout=1000)
            logger.info('%s %s' % (child.before, child.after))
        child.close()
    else:
        cmd2 = ODAADMCLI + 'stordiag '+ diskname
        run_cmd(cmd2)



def run_cmd(cmd):
    logger.info(cmd)
    result, error = host.ssh2node_job(cmd)
    if error:
       logger.error(error)
       return 0
    else:
       logger.info('\n'+result)
       return result


def disk_name():
    cmd = ODAADMCLI + "show disk -shared | awk 'NR>2{print $1}'"
    result = run_cmd(cmd)
    global diskname
    diskname = random.choice(result.split())
    return diskname


def log_management(hostname):
    global logfile
    logname = "odaadmcli_%s_%s.log" %(hostname, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    logfile = os.path.join(cf.log_dir, logname)
    log = initlogging.initLogging("odaadmcli", logfile, logging.WARN, logging.DEBUG)
    initlog(log)


def initlog(plog):
    oda_lib.initlog(plog)
    global logger
    logger = plog

if __name__ == '__main__':
    arg = docopt(__doc__)
    print arg
    hostname = arg['-s']
    username = arg['-u']
    password = arg['-p']
    log_management(hostname)
    host = oda_lib.Oda_ha(hostname, username, password)
    odaadmcli(host)
    print("Finished odaadmcli test, please check log %s for details" % logfile)