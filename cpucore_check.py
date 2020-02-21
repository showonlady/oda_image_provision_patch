#!/usr/bin/env python
#coding utf-8
#
# Copyright (c) 2018, Oracle and/or its affiliates. All rights reserved.
#
#    NAME
#      cpucore_check.py
#
#    DESCRIPTION
#      Sanity check for the cpucore commands
#
#    NOTES
#
#
#    MODIFIED   (MM/DD/YY)
#    chqin    4/15/18 - Creation
#
"""
Usage:
    cpucore_check.py -h
    cpucore_check.py -s <servername> [-u <username>] [-p <password>]

Options:
    -h,--help       Show this help message
    -s <servername>  hostname of machine, if vlan,use ip instead
    -u <username>  username [default: root]
    -p <password>  password [default: welcome1]
"""
from docopt import docopt
import oda_lib
import random
import common_fun as cf
import sys
import logging
import initlogging
import os

def positive_case(host,num):
    cpucores = range(2,num+2,2)
    log.info(cpucores)
    for i in cpucores:
        op = "-c %s" % i
        if not host.update_cpucore(op):
            log.error("update cpucore to %s fail!" % i)
        else:
            log.info("update cpucore to %s!" % i)
            if not check_cpucore(host,i):
                log.error("check fail! %s" % i)
                sys.exit(0)


def negative_case(host):
    cpucores = ['0','3','-1','5.5','40','a', '2']
    for i in cpucores:
        op = "-c %s" % i
        if host.update_cpucore(op):
            log.error("negative case fail!")


def positive_case2(host, num):
    cpucores = [4, 6, 8, 16, 2, num]
    for i in cpucores:
        op = "-c %s -f" % i
        if not host.update_cpucore(op):
            log.error("update cpucore to %s fail!" % i)
        else:
            log.info("update cpucore to %s!" % i)
            if not check_cpucore(host,i):
                log.error("check fail! %s" % i)
                sys.exit(0)



def check_cpucore(host, i):
    num1 = host.decribe_cpucore()[0]['cpuCores']
    cmd1 = "lscpu|grep Core|awk '{print $4}'"
    cmd2 = "lscpu|grep Socket|awk '{print $2}'"
    core = host.ssh2node(cmd1)
    socket = host.ssh2node(cmd2)
    num2 = int(core) * int(socket)
    if int(num1) == num2 and i == num2:
        return 1
    else:
        return 0


def initlogger(hostname):
    global logfile
    logname = "cpu_core_check_%s.log" % hostname
    logfile = os.path.join(cf.log_dir, logname)
    log = initlogging.initLogging("cpu_check", logfile, logging.WARN, logging.DEBUG)
    return log


def initlog(plog):
    oda_lib.initlog(plog)
    global log
    log = plog


def log_management(hostname):
    log = initlogger(hostname)
    initlog(log)


def main(hostname, username, password):
    #logfile_name = 'check_cpucore_%s.log' % hostname
    #fp, out, err,log = cf.logfile_name_gen_open(logfile_name)
    log_management(hostname)
    host = oda_lib.Oda_ha(hostname, username, password)
    cpucore_org = host.decribe_cpucore()[0]['cpuCores']
    positive_case(host, int(cpucore_org))
    negative_case(host)
    positive_case2(host, int(cpucore_org))
    error = cf.check_log(logfile)
    return error

if __name__ == '__main__':
    arg = docopt (__doc__)
    print arg
    hostname = arg['-s']
    username = arg['-u']
    password = arg['-p']
    main(hostname, username, password)



