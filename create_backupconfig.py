#!/usr/bin/env python
#coding utf-8
#
# Copyright (c) 2018, Oracle and/or its affiliates. All rights reserved.
#
#    NAME
#      backupconfig_check.py
#
#    DESCRIPTION
#      Sanity check for the backupconfig commands
#
#    NOTES
#
#
#    MODIFIED   (MM/DD/YY)
#    chqin    4/15/18 - Creation
#
"""
Usage:
    create_backupconfig.py -h
    create_backupconfig.py -s <servername> [-u <username>] [-p <password>]

Options:
    -h,--help       Show this help message
    -s <servername>  hostname of machine, if vlan,use ip instead
    -u <username>  username [default: root]
    -p <password>  password [default: welcome1]
"""
from docopt import docopt
import oda_lib
import random
import string
import common_fun as cf
import logging
import initlogging
import os, sys

def describe_check(d,dest, i, j):
    if d['backupDestination'] == dest and d['recoveryWindow'] == j:
        if i == '-cr ' and d['crosscheckEnabled'] == True or i == '-no-cr ' and d['crosscheckEnabled'] == False:
            return 1
        else:
            return 0

def delete_backupconfig(host, name, id):
    if random.choice([True, False]):
        op = "-in %s" % name
    else:
        op = "-i %s" % id
    return host.delete_backupconfig(op)



def create_bkc_disk(host):
    op = "-d Disk "
    for i in ['-cr ', '-no-cr ']:
        for j in ['0','-1','15']:
            bkname = cf.generate_string(cf.string1, 8)
            op1 = op + i + '-w %s -n %s' %(j, bkname)
            if host.create_backupconfig(op1):
                log.error("Nigtive case for backupconfig fail! %s \n" % op1)

    for i in ['-cr ', '-no-cr ']:
        for j in ['1','7','14']:
            bkname = cf.generate_string(cf.string1, 8)
            op2 = op + i + '-w %s -n %s' %(j, bkname)
            if not host.create_backupconfig(op2):
                log.error("Create backupconfig fail! %s \n" % op2)
            else:
                describe_info = host.describe_backupconfig("-in %s" % bkname)
                if not describe_info:
                    log.error ("Describe-backupconfig return none.")
                    return 0
                bkid = describe_info['id']
                if not describe_check(describe_info,'Disk', i, j):
                    log.error("describe backupconfig %s fail!" % bkname)
                else:
                    if not delete_backupconfig(host, bkname, bkid):
                        log.error("delete backupconfig %s fail!\n" % bkname)


def create_bkc_oss(host):
    #cf.add_line_ecthosts(host)
    if not host.update_agentproxy():
        log.error("Fail to set the agent proxy!")
        sys.exit(0)
    oss_name = cf.generate_string(cf.string2, 8)
    log.info(oss_name)
    oss_result = host.create_objectstoreswift(oss_name)
    if not oss_result :
        return 0

    op = "-d ObjectStore -c chqin -on %s " % oss_name
    #op = "-d ObjectStore -c oda-oss -on %s " % oss_name

    for i in ['-cr ', '-no-cr ']:
        for j in ['0','-1','31']:
            bkname = cf.generate_string(cf.string1, 8)
            op1 = op + i + '-w %s -n %s' %(j, bkname)
            if host.create_backupconfig(op1):
                log.error("Nigtive case for backupconfig fail! %s \n" % op1)

    for i in ['-cr ', '-no-cr ']:
        for j in ['1','15','30']:
            bkname = cf.generate_string(cf.string1, 8)
            op2 = op + i + '-w %s -n %s' %(j, bkname)
            if not host.create_backupconfig(op2):
                log.error("Create backupconfig fail! %s \n" % op2)
            else:
                describe_info = host.describe_backupconfig("-in %s" % bkname)
                if not describe_info:
                    log.error ("Describe-backupconfig return none.")
                    return 0
                bkid = describe_info['id']
                if not describe_check(describe_info, 'ObjectStore', i, j):
                    log.error("describe backupconfig %s fail!" % bkname)
                else:
                    if not delete_backupconfig(host, bkname, bkid):
                        log.error("delete backupconfig %s fail!\n" % bkname)

def create_bkc_none(host):
    op = "-d None "
    bkname = cf.generate_string(cf.string1, 8)
    op = op + '-n %s' % bkname
    if not host.create_backupconfig(op):
        log.error("Create backupconfig fail! %s \n" % op)
    else:
        describe_info = host.describe_backupconfig("-in %s" % bkname)
        if not describe_info:
            log.error ("Describe-backupconfig return none.")
            return 0
        bkid = describe_info['id']
        if describe_info['backupDestination'] != 'NONE':
            log.error("describe backupconfig %s fail!" % bkname)
        else:
            if not delete_backupconfig(host, bkname, bkid):
                log.error("delete backupconfig %s fail!\n" % bkname)


def initlogger(hostname):
    global logfile
    logname = "backupconfig_check_%s.log" % hostname
    logfile = os.path.join(cf.log_dir, logname)
    log = initlogging.initLogging("backupconfig_check", logfile, logging.WARN, logging.DEBUG)
    return log


def initlog(plog):
    oda_lib.initlog(plog)
    global log
    log = plog


def log_management(hostname):
    log = initlogger(hostname)
    initlog(log)


  
def main(hostname, username, password):
    #logfile_name = 'check_create_backupconfig_%s.log' % hostname
    #fp, out, err,log = cf.logfile_name_gen_open(logfile_name)
    #out, err = sys.stdout, sys.stderr
    #fp = open(logfile_name_stamp, 'a')
    #sys.stdout, sys.stderr = fp, fp
    log_management(hostname)
    host = oda_lib.Oda_ha(hostname, username, password)
    #create_bkc_disk(host)
    create_bkc_oss(host)
    #create_bkc_none(host)
    error = cf.check_log(logfile)
    return error

if __name__ == '__main__':
    arg = docopt (__doc__)
    print arg
    hostname = arg['-s']
    username = arg['-u']
    password = arg['-p']
    main(hostname, username, password)