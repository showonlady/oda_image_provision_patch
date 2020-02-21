#!/usr/bin/env python
#coding utf-8
#
# Copyright (c) 2018, Oracle and/or its affiliates. All rights reserved.
#
#    NAME
#      clone_database_test.py
#
#    DESCRIPTION
#      Check the command of clone-database
#
#    NOTES
#
#
#    MODIFIED   (MM/DD/YY)
#    chqin    12/07/18 - Creation
#

"""
Usage:
    clone_database_test.py -h
    clone_database_test.py -s <servername> [-u <username>] [-p <password>]

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
import create_multiple_db as c_m_d
#odacli = "/opt/oracle/dcs/bin/odacli"
password_new = "WElcome12_-"


def get_database(host):
    cmd1 = "%s list-databases" % host.ODACLI
    cmd = "%s list-databases |" \
          "awk 'BEGIN {IGNORECASE=1} NR>3&&$5~/false/&&$8~/acfs/&&$9~/Configured/ {print $2}'" % host.ODACLI
    result, err = host.ssh2node_job(cmd1)
    if err:
        return None
    else:
        result1 = host.ssh2node(cmd)
        list = result1.split()
        log.info(list)
        return list


def check_existing_db(host):
    databases = get_database(host)
    if not databases:
        log.warning("Will not check the existing db!")
        result = host.ssh2node("%s list-databases" % host.ODACLI)
        log.info(result)
    else:
        for i in databases:
            print i
            clone_db(host, i)




def clone_db(host, source):
    result = 1
    if host.is_ha_not():
        dbtype = ['racone','rac','si']
    else:
        dbtype = ["SI"]
    for i in dbtype:
        dbname = cf.generate_string (cf.string1, 8).lower()
        uniqname = cf.generate_string (cf.string2, 20)
        dbshape = random.choice (['odb1s', 'odb2', 'odb4', 'odb1', 'odb6'])
        #options = "-u %s -n %s -s %s -t %s -hm %s -f %s" %(uniqname, dbname, dbshape, i, password_new, source)
        #Due to the uniqname and dbname same issue
        options = "-u %s -n %s -s %s -t %s -hm %s -f %s" %(dbname, dbname, dbshape, i, password_new, source)

        if host.clone_database(options):
            log.info("clone database success with option %s" % options)
            dbnamesnap = cf.generate_string (cf.string1, 8).lower()
            uniqnamesnap = dbnamesnap
            #uniqnamesnap = cf.generate_string (cf.string2, 20)
            dbshapesnap = "odb1s"
            dbtypesnap = random.choice(dbtype)
            optionsnap = "-u %s -n %s -s %s -t %s -hm %s -f %s" % (uniqnamesnap,
                                                                dbnamesnap, dbshapesnap, dbtypesnap, password_new, dbname)
            if host.clone_database(optionsnap):
                log.info ("clone database success with option %s" % optionsnap)
                log.info("Will delete the database %s and %s" % (dbname, dbnamesnap))
                delete_database(host,dbname)
                delete_database(host, dbnamesnap)
            else:
                result = 0
                log.error("Fail to clone db from snapshot db with option %s" % optionsnap)
        else:
            result = 0
            log.error("clone database with option %s fail!" % options)
    return result

def delete_database(host, dbname):
    option = "-in %s" % dbname
    if host.delete_database(option):
        log.info("The db %s is deleted successfully!" % dbname)
    else:
        log.error("The db %s deletion fail!" % dbname)

def delete_database_dbhome(host, dbname):
    result = host.describe_database ("-in %s" % dbname)
    if not result:
        log.error ("Describe-database return none.")
        return 0
    dbhomeid = result["dbHomeId"]
    option = "-in %s" % dbname
    if host.delete_database (option):
        log.info ("The db %s is deleted successfully!" % dbname)
    else:
        log.error ("The db %s deletion fail!" % dbname)

    if not host.delete_dbhome ("-i %s" % dbhomeid):
        log.error ("Delete dbhome %s for db %s fail!\n" % (dbhomeid, dbname))
    else:
        log.info ("Successfull delete the dbhome for db %s!" % dbname)



def create_database_options(host):
    dbname = cf.generate_string (cf.string1, 8).lower()
    #uniqname = cf.generate_string (cf.string2, 20)
    uniqname = dbname
    de = "EE"
    if host.is_ha_not():
        dbtype = random.choice(['racone','rac','SI'])
    else:
        dbtype = "SI"

    dbclass = random.choice(['OLTP','DSS'])
    dbshape = random.choice(['odb1','odb2','odb4','odb6' ])
    if dbtype != "rac" and host.is_ha_not():
        #node_number = random.choice(["0","1"])
        node_number = random.choice(["0"])
        options = "-hm %s -n %s -u %s -de %s -cl %s -s %s -r ACFS -y %s -g %s " %(password_new, dbname, uniqname,
                                                                                 de, dbclass, dbshape, dbtype, node_number)
    else:
        options = "-hm %s -n %s -u %s -de %s -cl %s -s %s -r ACFS -y %s " %(password_new, dbname, uniqname,
                                                                                 de, dbclass, dbshape, dbtype)
    return options, dbname

def check_create_db(host):
    cf.extend_space_u01 (host)
    options = []
    for i in host.db_versions:
        if not c_m_d.is_clone_exists_or_not(host, i):
            c_m_d.scp_unpack_clone_file(host, i)

    for i in host.db_versions:
        str, name = create_database_options(host)
        str += "-v %s " % i
        options.append([str, name])
        if host.is_flash():
            str1, name1 = create_database_options (host)
            str1 += "-v %s -f " % i + random.choice (['-fc ', ''])
            options.append ([str1, name1])
    for i in options:
        log.info("Will create a db with option: %s" % i[0])
        if host.create_database(i[0]):
            log.info("Created database successfully with option: %s " % i[0])
            if clone_db (host, i[1]):
                log.info("Will delete the db %s and dbhome" % i[1])
                delete_database_dbhome(host, i[1])
        else:
            log.info("Fail to create database with option %s" % i[0])



def initlog(plog):
    oda_lib.initlog(plog)
    c_m_d.initlog (plog)
    global log
    log = plog


def log_management(hostname):
    logname = "clone_databases_test_%s.log" % hostname
    logfile = os.path.join(cf.log_dir, logname)
    log = initlogging.initLogging("clone_db", logfile, logging.WARN, logging.DEBUG)
    initlog(log)


if __name__ == '__main__':
    arg = docopt(__doc__)
    print arg
    hostname = arg['-s']
    username = arg['-u']
    password = arg['-p']
    log_management(hostname)
    host = oda_lib.Oda_ha(hostname, username, password)
    check_existing_db(host)
    check_create_db(host)
