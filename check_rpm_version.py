#!/usr/bin/env python
#coding utf-8
#
# Copyright (c) 2018, Oracle and/or its affiliates. All rights reserved.
#
#    NAME
#      check_rpm_version.py
#
#    DESCRIPTION
#      Check the version of some common rpms
#
#    NOTES
#
#
#    MODIFIED   (MM/DD/YY)
#    chqin    12/10/18 - Creation
#

"""
Usage:
    check_rpm_version.py -h
    check_rpm_version.py -s <servername> [-u <username>] [-p <password>]

Options:
    -h,--help       Show this help message
    -s <servername>  hostname of machine, if vlan,use ip instead
    -u <username>  username [default: root]
    -p <password>  password [default: welcome1]
"""
from docopt import docopt
import oda_lib
import common_fun as cf
import random
import os
import initlogging
import logging

hmp_version = "oracle-hmp-hwmgmt-2.4.5.0.1-1.el6.x86_64\n\
oracle-hmp-libs-2.4.5.0.1-1.el6.x86_64\n\
oracle-hmp-snmp-2.4.5.0.1-1.el6.x86_64\n\
oracle-hmp-tools-2.4.5.0.1-1.el6.x86_64\n\
oracle-hmp-tools-biosconfig-2.4.5.0.1-1.el6.x86_64\n\
oracle-hmp-tools-ubiosconfig-2.4.5.0.1-1.el6.x86_64\n\
oracle-hmp-utils-2.4.5.0.1-1.el6.x86_64"

ipmi_version = "ipmiflash-1.8.15.0-0.el6.x86_64\n\
ipmitool-1.8.15-2.el6.x86_64"


kernel_version = "4.1.12-124.33.4.el6uek.x86_64"
java_version = "1.8.0_231-b11"
sg3_util_version ="sg3_utils-1.28-13.el6.x86_64\n\
sg3_utils-libs-1.28-13.el6.x86_64"
    
hmp_cmd = "rpm -qa|grep hmp|sort"
ipmi_cmd = "rpm -qa|grep ipmi|sort"
kernel_cmd = "uname -r"
java_cmd = "java -fullversion 2>&1 | awk -F '\"' '{print $2}'"
sg3_cmd = "rpm -qa|grep sg3_utils|sort"

Check_list = [["HMP", hmp_cmd, hmp_version],
              ["IPMI", ipmi_cmd, ipmi_version],
              ["Kernel", kernel_cmd, kernel_version],
              ["Java", java_cmd, java_version],
              ["sg3_utils", sg3_cmd, sg3_util_version]

]

def check_rpm(host, check_item):
    flag = 1
    log.info("*"*10 + "%s check on host %s" % (check_item[0], host.hostname) + "*"*10)
    result = host.ssh2node(check_item[1])
    if result == check_item[2]:
        log.info("%s version on host %s is correct!" % (check_item[0], host.hostname))
    else:
        log.error ("%s version on host %s is wrong!" % (check_item[0], host.hostname))
        log.error ("The correct rpms should be:\n%s" % check_item[2])
        log.error ("The rpm on host %s is:\n%s" % (host.hostname, result))
        flag = 0
    return flag


def check_selinux(host):
    cmd1 = "cat /etc/selinux/config |grep SELINUX= | awk -F = 'END{print $NF}'"
    cmd2 = "getenforce"
    result1 = host.ssh2node(cmd1)
    result2 = host.ssh2node(cmd2)
    if result1.lower() == 'disabled' and result2.lower() == 'disabled':
        log.info("The selinux status on %s is correct: disabled" % host.hostname)
    else:
        log.error("The selinux status on %s is wrong: %s, %s" %(host.hostname, result1, result2))



def check_rds_not(host):
    crs_home = host.gi_home()
    cmd = "%s/bin/skgxpinfo" % crs_home
    flag = 1
    log.info ("*" * 10 + "RDS check on host %s" % host.hostname + "*" * 10)
    result = host.ssh2node (cmd)
    if host.is_ib_not():
        if result.lower() == 'rds':
            log.info ("RDS check on host %s is correct!" % host.hostname)
        else:
            flag = 0
            log.error("IB env are not using rds on host %s, it is using %s!" % (host.hostname,result))
    else:
        if result.lower () == 'udp':
            log.info ("UDP check on host %s is correct!" % host.hostname)
        else:
            flag = 0
            log.error ("non-IB env are not using UDP on host %s, it is using %s!" % (host.hostname,result))
    return flag


def initlog(plog):
    oda_lib.initlog(plog)
    global log
    log = plog


def log_management(hostname):
    logname = "Check_rpm_version_%s.log" % hostname
    logfile = os.path.join(cf.log_dir, logname)
    log = initlogging.initLogging("check_version", logfile, logging.WARN, logging.DEBUG)
    initlog(log)

def check(host):
    for i in Check_list:
        check_rpm(host,i )
    check_rds_not(host)
    check_selinux(host)

def main(host):
    log_management(host.hostname)
    check(host)
    if host.is_ha_not():
        node2 = cf.node2_name(host.hostname)
        host2 = oda_lib.Oda_ha(node2, host.username, host.password)
        check(host2)

if __name__ == '__main__':
    arg = docopt(__doc__)
    print arg
    hostname = arg['-s']
    username = arg['-u']
    password = arg['-p']
    host = oda_lib.Oda_ha(hostname, username, password)
    main(host)