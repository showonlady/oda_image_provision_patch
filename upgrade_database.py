#!/usr/bin/env python
# -*- coding:UTF-8 -*-
#
# Copyright (c) 2018, Oracle and/or its affiliates. All rights reserved.
#
#    NAME
#      upgrade_database.py
#
#    DESCRIPTION
#      Check the command of upgrade-database
#
#    NOTES
#      odacli upgrade-database
#
#    MODIFIED   (MM/DD/YY)
#    weiwei    01/08/19 - Creation
#
"""
Usage:
 upgrade_database.py -s <hostname> [-u <username>] [-p <password>]
 
Options:
  -h, --help  Show this screen
  -s <hostname>  hostname, if vlan,use ip instead
  -u <username>  username [default: root]
  -p <password>  password [default: welcome1]
"""


import os
import random
import oda_lib
from docopt import docopt
import common_fun as cf
import create_multiple_db as c_m_d
import logging
import initlogging
import datetime
import re

password_new = "WElcome12_-"


def upgrade_database(host,databaseid,sourceDbHomeId,dbedition):
    if dbedition == "SE":
        destDbHomeId = se_destDbHomeId
    else:
        destDbHomeId = ee_destDbHomeId
    if random.choice(["true","false"]):
        options = "-i %s -from %s -to %s " % (databaseid, sourceDbHomeId, destDbHomeId)
    else:
        options = "-i %s -to %s " % (databaseid, destDbHomeId)
    if host.upgrade_database(options):
        logger.info("upgrade database success with option %s" % options)
        return 1
    else:
        logger.error("upgrade database with option %s fail!" % options)
        return 0


def get_destDbHomeId(host):
    global se_destDbHomeId
    global ee_destDbHomeId
    se_destDbHomeId = 0
    ee_destDbHomeId = 0
    cmd = "%s list-dbhomes | grep Configured| grep %s |awk '{print $1}'" % (host.ODACLI,host.Current_version)
    DbHomeIdstr = host.ssh2node(cmd)
    if not re.search("DCS-10032:Resource database home is not found", DbHomeIdstr):
        DbHomeId = DbHomeIdstr.split()
        for i in DbHomeId:
            edition = host.describe_dbhome("-i %s" % i)["dbEdition"]
            if edition == "SE":
                se_destDbHomeId = i
            else:
                ee_destDbHomeId = i


    if not se_destDbHomeId or not ee_destDbHomeId:
        if not c_m_d.is_clone_exists_or_not(host, host.db_versions[-1]):
            c_m_d.scp_unpack_clone_file(host, host.db_versions[-1])

    if not se_destDbHomeId:
        if host.create_dbhome("-v %s -de se" % host.db_versions[-1]):
            cmd = "%s list-dbhomes|tail -n 2|head -n 1|awk '{print $1}'" % (host.ODACLI)
            se_destDbHomeId = host.ssh2node(cmd)

    if not ee_destDbHomeId:
        if host.create_dbhome("-v %s -de ee" % host.db_versions[-1]):
            cmd = "%s list-dbhomes|tail -n 2|head -n 1|awk '{print $1}'" % (host.ODACLI)
            ee_destDbHomeId = host.ssh2node(cmd)


def upgrade_existing_db(host):
    dbid = get_existing_db(host)
    if dbid:
        for i in dbid:
            sourceDbHomeId = host.describe_database("-i %s" % i)["dbHomeId"]
            dbedition = host.describe_database("-i %s" % i)["dbEdition"]
            upgrade_database(host, i, sourceDbHomeId, dbedition)
    else:
        logger.warning("There is no db to upgrade!")
        result = host.ssh2node("%s list-databases" % host.ODACLI)
        logger.info(result)


def get_existing_db(host):
    cmd = "%s list-databases | awk 'BEGIN {IGNORECASE=1} NR>3&&$4!~/%s/&&$9~/Configured/ {print $1}'" % (host.ODACLI,host.Current_version)
    resultstr = host.ssh2node(cmd)
    if not re.search ("DCS-10032:Resource database is not found", resultstr):
        result = resultstr.split()
    else:
        result = None
    logger.info(resultstr)
    return result


def upgrade_new_db(host):
    cf.extend_space_u01(host)
    options = []
    for i in host.db_versions:
        if not c_m_d.is_clone_exists_or_not(host, i):
            c_m_d.scp_unpack_clone_file(host, i)

    if host.is_ha_not():
        dbtype = ['racone', 'rac', 'SI']
    else:
        dbtype = ["SI"]
    db_versions = host.db_versions
    db_versions.pop()
    for i in db_versions:
        for j in dbtype:
            str, name = create_database_options(host,i,j)
            str += "-v %s " % i
            options.append([str, name])
            if host.is_flash():
                str1, name1 = create_database_options(host,i,j)
                str1 += "-v %s -f " % i + random.choice(['-fc ', ''])
                options.append([str1, name1])
    for i in options:
        logger.info("Will create a db with option: %s" % i[0])
        if host.create_database(i[0]):
            logger.info("Created database successfully with option: %s " % i[0])
            databaseid = host.describe_database("-in %s" % i[1])["id"]
            sourceDbHomeId = host.describe_database("-in %s" % i[1])["dbHomeId"]
            dbedition = host.describe_database("-in %s" % i[1])["dbEdition"]
            if upgrade_database(host, databaseid,sourceDbHomeId,dbedition):
                logger.info("Will delete the db %s " % i[1])
                result = host.describe_database("-in %s" % i[1])
                if not result:
                    logger.error("Describe-database return none.")
                    return 0
                option = "-in %s" % i[1]
                if host.delete_database(option):
                    logger.info("The db %s is deleted successfully!" % i[1])
                else:
                    logger.error("The db %s deletion fail!" % i[1])
                logger.info("Will delete the dbhome %s " % sourceDbHomeId)
                if host.delete_dbhome("-i %s"% sourceDbHomeId):
                    logger.info("The dbhome %s is deleted successfully!" % sourceDbHomeId)
                else:
                    logger.error("The dbhome %s deletion fail!" % sourceDbHomeId)

        else:
            logger.info("Fail to create database with option %s" % i[0])


def create_database_options(host,db_versions,dbtype):
    dbname = cf.generate_string(cf.string1, 8)
    uniqname = cf.generate_string(cf.string2, 20)
    de = random.choice(['EE','SE'])
    # if host.is_ha_not():
    #     dbtype = random.choice(['racone','rac','SI'])
    # else:
    #     dbtype = "SI"
    if de == "SE":
        dbclass = 'OLTP'
    elif db_versions[0:4] == "11.2":
        dbclass = random.choice(['OLTP', 'DSS'])
    else:
        dbclass = random.choice(['IMDB','OLTP','DSS'])

    if db_versions[0:4] == "11.2":
        dbstorage = "ACFS"
    elif db_versions[0:4] == "12.1" and is_flex(host):
        dbstorage = "ACFS"
    else:
        dbstorage = random.choice(['ACFS', 'ASM'])
    dbshape = random.choice(['odb1','odb2','odb4','odb6'])
    if dbtype != "rac" and host.is_ha_not():
        node_number = random.choice(["0","1"])
        options = "-hm %s -n %s -u %s -de %s -cl %s -s %s -r %s -y %s -g %s " %(password_new, dbname, uniqname,
                                                                                 de, dbclass, dbshape, dbstorage,dbtype, node_number)
    else:
        options = "-hm %s -n %s -u %s -de %s -cl %s -s %s -r %s -y %s " %(password_new, dbname, uniqname,
                                                                                 de, dbclass, dbshape,dbstorage, dbtype)
    return options, dbname


def is_flex(host):
    cmd = "%s list-dgstorages -r all|grep -i FLEX"% (host.ODACLI)
    result = host.ssh2node(cmd)
    if result:
        return 1
    else:
        return 0


def log_management(hostname):
    global logfile
    logname = "upgrade_db_%s_%s.log" %(hostname, datetime.datetime.now().strftime('%Y-%m-%d'))
    logfile = os.path.join(cf.log_dir, logname)
    log = initlogging.initLogging("upgrade_db", logfile, logging.WARN, logging.DEBUG)
    initlog(log)


def initlog(plog):
    oda_lib.initlog(plog)
    c_m_d.initlog(plog)
    global logger
    logger = plog

def main(host):
    log_management(host.hostname)
    get_destDbHomeId (host)
    upgrade_existing_db (host)
    upgrade_new_db (host)
    error = cf.check_log(logfile)
    return error

if __name__ == '__main__':
    arg = docopt(__doc__)
    print arg
    hostname = arg['-s']
    username = arg['-u']
    password = arg['-p']
    log_management(hostname)
    host = oda_lib.Oda_ha(hostname, username, password)
    get_destDbHomeId(host)
    upgrade_existing_db(host)
    upgrade_new_db(host)
    print("Finished upgrade_database test, please check log %s for details." % logfile)
