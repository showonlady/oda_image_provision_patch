#!/usr/bin/env python
#coding:utf-8
#
# Copyright (c) 2018, Oracle and/or its affiliates. All rights reserved.
#
#    NAME
#      dbhome_check.py
#
#    DESCRIPTION
#      Sanity check for the dbhome commands
#
#    NOTES
#
#
#    MODIFIED   (MM/DD/YY)
#    chqin    4/15/18 - Creation
#
"""
Usage:
    dbhome_check.py -h
    dbhome_check.py -s <servername> [-u <username>] [-p <password>]

Options:
    -h,--help       Show this help message
    -s <servername>  hostname of machine, if vlan,use ip instead
    -u <username>  username [default: root]
    -p <password>  password [default: welcome1]
"""
from docopt import docopt
import create_multiple_db as c_m_d
import random
import common_fun as cf
import oda_lib
import string
import sys
import os
import re
import datetime
import logging
import initlogging

def check_dbhome(*a):
    host = a[0]
    if len(a) == 1:
        s_v = host.system_version()
        s_v = cf.trim_version(s_v)
        version = c_m_d.d_version[s_v]
        log.info(version)
    else:
        version = a[1]
    version_list = c_m_d.db_versions(host,version)
    if len(version_list) == 0:
        sys.exit(1)
    log.info(version_list)
    for i in version_list:
        if not c_m_d.is_clone_exists_or_not(host, i):
            c_m_d.scp_unpack_clone_file(host, i)
        v = i.split('_')[0]
        if not host.create_dbhome("-de SE -v %s" % v):
            log.error("create SE dbhome with version %s fail!" % v)
        else:
            dbhomeid = get_dbhomeid(host)
            if not delete_dbhome(host,dbhomeid):
                log.error("delete dbhome fail %s" % dbhomeid)

        if not host.create_dbhome("-de EE -v %s" % v):
            log.error("create EE dbhome with version %s fail!" % v)
        else:
            dbhomeid = get_dbhomeid(host)
            if not delete_dbhome(host, dbhomeid):
                log.error("delete dbhome fail %s" % dbhomeid)
        delete_dbcone(host, version)


def delete_dbcone(host, version):
    cmd = "ls /opt/oracle/oak/pkgrepos/orapkgs/clones/*%s*tar.gz" % version
    clone = host.ssh2node(cmd)
    cmd = "rm -rf %s" % clone
    host.ssh2node(cmd)
    if host.is_ha_not():
        node2 = cf.node2_name(host.hostname)
        host2 = oda_lib.Oda_ha(node2, host.username, host.password)
        host2.ssh2node(cmd)


def get_dbhomeid(host):
    cmd = "/opt/oracle/dcs/bin/odacli list-dbhomes|tail -n 2|awk '{print $1}'"
    dbhomeid = host.ssh2node(cmd)
    return dbhomeid


def delete_dbhome(host, dbhomeid):
    if not host.delete_dbhome("-i %s" % dbhomeid):
        log.error("delete dbhome %s fail!" % dbhomeid)
        return 0
    else:
        return 1


def initlogger(hostname):
    global logfile
    logname = "create_dbhome_%s.log" % hostname
    logfile = os.path.join(cf.log_dir, logname)
    log = initlogging.initLogging("dbhome_check", logfile, logging.WARN, logging.DEBUG)
    return log


def initlog(plog):
    oda_lib.initlog(plog)
    c_m_d.initlog(plog)
    global log
    log = plog

def log_management(hostname):
    log = initlogger(hostname)
    initlog(log)


def main(hostname, username, password):
    #logfile_name = 'check_dbhome_create_delete_%s.log' % hostname
    #fp, out, err,log = cf.logfile_name_gen_open(logfile_name)
    log_management(hostname)
    host = oda_lib.Oda_ha(hostname, username, password)
    #ver = random.choice(['170814','171017','180116','180417'])
    ver = random.choice(c_m_d.d_version.values())
    check_dbhome(host,ver)
    error = cf.check_log(logfile)
    return error


if __name__ == '__main__':
    arg = docopt (__doc__)
    print arg
    hostname = arg['-s']
    username = arg['-u']
    password = arg['-p']
    main (hostname, username, password)