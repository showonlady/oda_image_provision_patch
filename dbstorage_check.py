#!/usr/bin/env python
#coding utf-8
#
# Copyright (c) 2018, Oracle and/or its affiliates. All rights reserved.
#
#    NAME
#      dbstorage_check.py
#
#    DESCRIPTION
#      Sanity check for the dbstorage commands
#
#    NOTES
#
#
#    MODIFIED   (MM/DD/YY)
#    chqin    4/15/18 - Creation
#
"""
Usage:
    dbstorage_check.py -h
    dbstorage_check.py -s <servername> [-u <username>] [-p <password>]

Options:
    -h,--help       Show this help message
    -s <servername>  hostname of machine, if vlan,use ip instead
    -u <username>  username [default: root]
    -p <password>  password [default: welcome1]
"""
from docopt import docopt
import common_fun as cf
import random
import re
import oda_lib
import os
import logging
import initlogging

def dbstorage_asm_create(host):

    size = ['-s 100 ','-s 200 ']

    for i in size:
        dbname = cf.generate_string(cf.string1, 8)
        op = "-n %s -r ASM %s" % (dbname,i)
        if random.choice(['True','False']):
            dbuniqname = cf.generate_string(cf.string2, 20)
            op += '-u %s ' % dbuniqname
        if host.is_flash():
            flash = random.choice(['-f ', '-no-f '])
            op += flash
        if not host.create_dbstorage(op):
            log.error("create dbstorage fail! %s" % op)
        else:
            dbstorage_id = host.ssh2node("/opt/oracle/dcs/bin/odacli list-dbstorages|tail -n 1|awk '{print $1}'")
            if not check_asm_dbstorage(host,op,dbstorage_id):
                log.error("describe dbstorage fail! %s" % op)
            else:
                if not host.delete_dbstorage("-i %s" % dbstorage_id):
                    log.error("delete dbstorage fail! %s" % op)



def check_asm_dbstorage(host,op,dbstorage_id):
    log.info(dbstorage_id)
    a = host.describe_dbstorage("-i %s" % dbstorage_id)
    if not a:
        log.error("Describe dbstorage return none.")
        return 0

    list = [a['name'], a['dbStorage'],a['recoDestination'],
            a['redoDestination'],a['dataDestination'],
            a['databaseUniqueName'],a['state']['status']]

    n_s = re.search('-n\s+(\S+)\s+-r\s+(\S+)',op).groups()
    list1 = [n_s[0],n_s[1], 'RECO']
    if host.is_ha_not():
        list1.append('REDO')
    else:
        list1.append('RECO')
    f_n = re.search('( -f)', op)
    if f_n:
        list1.append('FLASH')
    else:
        list1.append('DATA')
    u_n = re.search('-u\s+(\S+)',op)
    if u_n:
        list1.append(u_n.group(1))
    else:
        list1.append(n_s[0])
    list1.append('CONFIGURED')
    if list == list1:
        return 1
    else:
        log.info(list1)
        return 0



def dbstorage_acfs_create(host):
    size = ['-s 100 ', '-s 200 ']

    for i in size:
        dbname = cf.generate_string(cf.string1, 8)
        op = "-n %s -r ACFS %s" % (dbname, i)
        if random.choice(['True', 'False']):
            dbuniqname = cf.generate_string(cf.string2, 20)
            op += '-u %s ' % dbuniqname
        if host.is_flash():
            flash = random.choice(['-f ', '-no-f '])
            op += flash
        if not host.create_dbstorage(op):
            log.error("create dbstorage fail! %s" % op)
        else:
            dbstorage_id = host.ssh2node("/opt/oracle/dcs/bin/odacli list-dbstorages|tail -n 1|awk '{print $1}'")
            if not check_acfs_dbstorage(host, op, dbstorage_id):
                log.error("describe dbstorage fail! %s" % op)
            else:
                if not host.delete_dbstorage("-i %s" % dbstorage_id):
                    log.error("delete dbstorage fail! %s" % op)

def check_acfs_dbstorage(host,op,dbstorage_id):
    log.info(dbstorage_id)
    a = host.describe_dbstorage("-i %s" % dbstorage_id)
    if not a:
        log.error("Describe-storage return none.")
        return 0
    list = [a['name'], a['dbStorage'],a['recoDestination'],
            a['redoDestination'],a['dataDestination'],
            a['databaseUniqueName'],a['state']['status']]

    n_s = re.search('-n\s+(\S+)\s+-r\s+(\S+)',op).groups()
    oracle_user = host.racuser()
    reco = "/u03/app/%s/fast_recovery_area/" % oracle_user
    list1 = [n_s[0],n_s[1],reco]
    if host.is_ha_not():
        redo = "/u04/app/%s/redo/" % oracle_user
    else:
        redo = "/u03/app/%s/redo/" % oracle_user
    list1.append(redo)
    u_n = re.search('-u\s+(\S+)',op)
    if u_n:
        uniquename = u_n.group(1)
    else:
        uniquename = n_s[0]
    f_n = re.search(' -f', op)
    if f_n:
        data = "/u02/app/%s/flashdata/%s" %(oracle_user,uniquename)
    else:
        data = "/u02/app/%s/oradata/%s" % (oracle_user,uniquename)

    list1.append(data)
    list1.append(uniquename)
    list1.append('CONFIGURED')
    if list != list1:
        log.info(list1)
        return 0

    s = re.search('-s\s+(\S+)',op)
    if s:
        size = s.group(1)
    else:
        size = '100'
    df = host.ssh2node("df -h %s" % data)
    data_size = df.split()[8]
    if path_exist_or_not(host,data) and path_exist_or_not(host, reco) and path_exist_or_not(host, redo) and data_size[:-1] == size:
        return 1
    else:
        return 0


def path_exist_or_not(host, a):
    cmd = "ls %s" % a
    result = host.ssh2node(cmd)
    if re.search("No such", result):
        return 0
    else:
        return 1


def initlogger(hostname):
    global logfile
    logname = "create_dbstorage_%s.log" % hostname
    logfile = os.path.join(cf.log_dir, logname)
    log = initlogging.initLogging("dbstorage_check", logfile, logging.WARN, logging.DEBUG)
    return log


def initlog(plog):
    oda_lib.initlog(plog)
    global log
    log = plog

def log_management(hostname):
    log = initlogger(hostname)
    initlog(log)


def main(hostname, username, password):
    #logfile_name = 'check_create_dbstorage_%s.log' % hostname
    #fp, out, err,log = cf.logfile_name_gen_open(logfile_name)
    log_management(hostname)
    host = oda_lib.Oda_ha(hostname, username, password)
    dbstorage_asm_create(host)
    dbstorage_acfs_create(host)
    error = cf.check_log(logfile)
    return error



if __name__ == '__main__':
    arg = docopt (__doc__)
    print arg
    hostname = arg['-s']
    username = arg['-u']
    password = arg['-p']
    main(hostname, username, password)