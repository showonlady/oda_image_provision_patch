#!/usr/bin/env python
# -*- coding:UTF-8 -*-
#
# Copyright (c) 2018, Oracle and/or its affiliates. All rights reserved.
#
#    NAME
#      irestore_database.py
#
#    DESCRIPTION
#      Check the command of irestore-database
#
#    NOTES
#      odacli irestore-database
#
#    MODIFIED   (MM/DD/YY)
#    weiwei    01/23/19 - Creation
#
"""
Usage:
 irestore_database.py -s <hostname> [-u <username>] [-p <password>] [-d <dbname>]

Options:
  -h, --help  Show this screen
  -s <hostname>  hostname, if vlan,use ip instead
  -u <username>  username [default: root]
  -p <password>  password [default: welcome1]
  -d <dbname>   The db name
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
import sys
import time


remote_dir = '/tmp'
bkpassword = "WElcome12_-"
dbstatus = 'dbstatus_check.sh'
backupreport = 'backupreport.br'


def irestore_oss(host):
    ###Check if dns is configured
    update_hosts(host)
    if host.is_ha_not():
        host2name = cf.node2_name(host.hostname)
        host2 = oda_lib.Oda_ha(host2name, host.username, host.password)
        update_hosts(host2)
    ###set the agent proxy###
    if not host.update_agentproxy():
        logger.error("Fail to set the agent proxy!")
        sys.exit(0)
    oss_name = cf.generate_string(cf.string2, 8)
    logger.info(oss_name)
    oss_result = host.create_objectstoreswift(oss_name)
    if not oss_result:
        return 0
    op_oss = "-d ObjectStore -c chqin -on %s " % oss_name
    # op_oss = "-d ObjectStore -c 'oda-oss' -on %s " % oss_name
    op = random.choice(['-cr -w 1', '-no-cr -w 15', '-cr -w 30'])
    bk_name = cf.generate_string(cf.string1, 8)
    bk_op = '-n %s ' % bk_name + op_oss + op
    if not host.create_backupconfig(bk_op):
        logger.error("create backup config %s fail!\n" % bk_name)
        return 0
    updatedb_op = "-in %s -bin %s -hbp %s" % (dbname, bk_name, bkpassword)
    if not host.update_database(updatedb_op):
        logger.error("update db %s with backup config %s fail!\n" % (dbname, bk_name))
        return 0

    host.disable_auto_backup()
    op1 = create_bk_op()
    if not host.create_backup(op1):
        logger.error("create backup fail %s\n" % op1)
        return 0
    time.sleep(120)
    if not irestore_db(host,oss_name=oss_name):
        sys.exit(0)


def irestore_nfs(host):
    # create nfs
    racuser = host.racuser()
    cmd1 = "/bin/su - %s -c 'mkdir -p /tmp/backup'" % racuser
    cmd2 = "mount 10.214.80.5:/scratch/nfs /tmp/backup"
    cmd3 = " echo '/bin/mount 10.214.80.5:/scratch/nfs /tmp/backup &' >> /etc/rc.d/rc.local"
    host.ssh2node(cmd1)
    host.ssh2node(cmd2)
    host.ssh2node(cmd3)
    if host.is_ha_not():
        host2name = cf.node2_name(host.hostname)
        host2 = oda_lib.Oda_ha(host2name, host.username, host.password)
        host2.ssh2node(cmd1)
        host2.ssh2node(cmd2)
        host2.ssh2node(cmd3)
    # create backupconfig
    op = random.choice(['-cr -w 1', '-no-cr -w 7', '-cr -w 14'])
    bk_name = cf.generate_string(cf.string1, 8)
    bk_op = '-d NFS -c /tmp/backup ' + '-n %s ' % bk_name + op
    if not host.create_backupconfig(bk_op):
        logger.error("create backup config %s fail!\n" % bk_name)
        return 0
    updatedb_op = "-in %s -bin %s" % (dbname, bk_name)
    if not host.update_database(updatedb_op):
        logger.error("update db %s with backup config %s fail!\n" % (dbname, bk_name))
        return 0

    host.disable_auto_backup()
    time.sleep(120)
    op1 = create_bk_op()
    if not host.create_backup(op1):
        logger.error("create backup fail %s\n" % op1)
        return 0
    if not irestore_db(host):
        sys.exit(0)


def irestore_others(host):
    d = "/chqin/new_test/venv/src/%s" % backupreport
    remote_file = os.path.join(remote_dir, os.path.basename(backupreport))
    host.scp2node(d, remote_file)
    oss_name = cf.generate_string(cf.string2, 8)
    logger.info(oss_name)
    oss_result = host.create_objectstoreswift(oss_name)
    if not oss_result:
        return 0
    if not irestore_db(host,oss_name=oss_name, br=remote_file):
        sys.exit(0)


def irestore_db(host,oss_name='',br=''):
    if not br:
        br = generate_backupreport(host)
        #br = os.path.join(remote_dir, os.path.basename(backupreport))

    op2 = create_database_options(host)
    for i in op2:
        new_dbname = cf.generate_string(cf.string1, 8)
        uniqname = cf.generate_string(cf.string2, 20)
        resetDBID = random.choice(['-rDBID', ' '])
        # if de == "SE":
        #     noOfRmanChannels = 1
        # else:
        #     noOfRmanChannels = random.randint(1,200)
        if not oss_name:
            #options = i + " -n %s -u %s -r %s -hm %s -hbp %s -bl %s %s " % (new_dbname,uniqname,br, "WElcome12_-", bkpassword, "/tmp/backup",resetDBID)
            options = i + " -n %s -u %s -r %s -hm %s -hbp %s %s " % (new_dbname,uniqname,br, "WElcome12_-", bkpassword,resetDBID)

        else:
            options = i + " -n %s -u %s -r %s -on %s -hm %s -hbp %s %s " % (new_dbname,uniqname,br, oss_name, "WElcome12_-", bkpassword,resetDBID)

        if not host.irestore_database(options):
            logger.error("irestore database fail %s\n" % new_dbname)
            return 0
        check_dbstatus(host,new_dbname)

        logger.info("Will delete the db %s " % new_dbname)
        result = host.describe_database("-in %s" % new_dbname)
        if not result:
            logger.error("Describe-database return none.")
            return 0
        sourceDbHomeId = result["dbHomeId"]
        option = "-in %s" % new_dbname
        if host.delete_database(option):
            logger.info("The db %s is deleted successfully!" % new_dbname)
        else:
            logger.error("The db %s deletion fail!" % new_dbname)
        logger.info("Will delete the dbhome %s " % sourceDbHomeId)
        if host.delete_dbhome("-i %s" % sourceDbHomeId):
            logger.info("The dbhome %s is deleted successfully!" % sourceDbHomeId)
        else:
            logger.error("The dbhome %s deletion fail!" % sourceDbHomeId)
    return 1


def update_hosts(host):
    ###Check if dns is configured
    ## if not, add "10.241.247.6  storage.oraclecorp.com" to /etc/hosts
    cmd1 = "cat /etc/resolv.conf"
    output = host.ssh2node(cmd1)
    if not re.search("nameserver", output):
        # cmd2 = """echo "10.241.247.6  storage.oraclecorp.com" >>/etc/hosts"""
        cmd3 = """echo "148.87.19.20  www-proxy.us.oracle.com" >>/etc/hosts"""
        cmd2 = """echo "129.146.13.151 swiftobjectstorage.us-phoenix-1.oraclecloud.com" >>/etc/hosts"""
        host.ssh2node(cmd2)
        host.ssh2node(cmd3)
    else:
        pass


def randomget_dbname(host):
    cmd = "/opt/oracle/dcs/bin/odacli list-databases|grep -v testxx|grep Configured|awk '{print $2}'"
    result, error = host.ssh2node_job(cmd)
    if result:
        dbname = random.choice(result.split())
        return dbname
    else:
        dbname = create_new_db(host)
        return dbname


def create_new_db(host):
    if not c_m_d.is_clone_exists_or_not (host, host.db_versions[-1]):
        c_m_d.scp_unpack_clone_file (host, host.db_versions[-1])
    if host.create_database("-hm WElcome12__ -n testire -v %s " % host.db_versions[-1]):
        return "testire"
    else:
        return 0


def create_bk_op():
    a = ""
    i = random.choice(range(4))
    if i == 0:
        a = "-bt Regular-L0 -in %s " % dbname
    elif i == 1:
        a = "-bt Regular-L1 -c Database -in %s" % dbname
    elif i == 2:
        tag = cf.generate_string(cf.string2,8)
        a = "-bt Longterm -in %s -k 1 -t %s" % (dbname, tag)
    elif i == 3:
        tag = cf.generate_string(cf.string2,8)
        a = "-bt Regular-L1 -in %s -t %s" % (dbname, tag)
    return a


def check_dbstatus(host,new_dbname):
    oracle_home = host.dbnametodbhome(new_dbname)
    uniqname = host.describe_database("-in %s" % new_dbname)["databaseUniqueName"]
    fp = open(dbstatus, 'w')
    fp.write("#!/bin/bash\n")
    fp.write("export ORACLE_HOME=%s\n" % oracle_home)
    fp.write("%s/bin/srvctl status database -d %s;\n" % (oracle_home, uniqname))
    fp.close()
    remote_file = os.path.join(remote_dir, os.path.basename(dbstatus))
    host.scp2node(dbstatus, remote_file)
    racuser = host.racuser()
    racgroup = host.racgroup()
    cmd1 = "/bin/chown %s:%s %s" % (racuser, racgroup, remote_file)
    cmd2 = "/bin/chmod +x %s" % remote_file
    cmd3 = "/bin/su - %s -c %s" % (racuser, remote_file)
    host.ssh2node(cmd1)
    host.ssh2node(cmd2)
    result = host.ssh2node(cmd3) + '\n'
    logger.info(result)


def generate_backupreport(host):
    cmd1 = "/opt/oracle/dcs/bin/odacli list-backupreports|egrep -i 'Regular-|Long'|tail -n 1|awk '{print $1}'"
    bkreport_id = host.ssh2node(cmd1)
    #bkreport = host.describe_backupreport("-i %s" %bkreport_id)
    br = "/tmp/backupreport_%s" % bkreport_id
    cmd = "%s describe-backupreport -i %s > %s" %(host.ODACLI, bkreport_id, br)
    host.ssh2node(cmd)
    return br
    # fp = open(backupreport, 'w')
    # fp.write(bkreport)
    # fp.close()
    # remote_file = os.path.join(remote_dir, os.path.basename(backupreport))
    # host.scp2node(backupreport, remote_file)


def create_database_options(host):
    de = host.describe_database("-in %s" % dbname)["dbEdition"]
    db_versions = host.describe_database("-in %s" % dbname)["dbVersion"]

    options = []
    if host.is_ha_not():
        dbtype = ['racone', 'rac', 'SI']
    else:
        dbtype = ["SI"]

    if de == "SE":
        dbclass = ['OLTP']
    elif db_versions[0:4] == "11.2":
        dbclass = ['OLTP', 'DSS']
    else:
        dbclass = ['IMDB','OLTP','DSS']

    if db_versions[0:4] == "11.2":
        dbstorage = ["ACFS"]
    elif db_versions[0:4] == "12.1" and is_flex(host):
        dbstorage = ["ACFS"]
    else:
        dbstorage = ['ACFS', 'ASM']
    dbshape = random.choice(['odb1','odb2','odb4','odb6'])
    for y in dbtype:
        for cl in dbclass:
            for dr in dbstorage:
                if host.is_flash():
                    str = " -cl %s -s %s -dr %s -y %s -f " % (cl, dbshape, dr, y)
                else:
                    str = " -cl %s -s %s -dr %s -y %s -no-f " % (cl, dbshape, dr, y)
                options.append(str)

    return options


def is_flex(host):
    cmd = "%s list-dgstorages -r all|grep -i FLEX"% (host.ODACLI)
    result = host.ssh2node(cmd)
    if result:
        return 1
    else:
        return 0


def log_management(hostname):
    global logfile
    logname = "irestore_db_%s_%s.log" %(hostname, datetime.datetime.now().strftime('%Y-%m-%d'))
    logfile = os.path.join(cf.log_dir, logname)
    log = initlogging.initLogging("irestore_db", logfile, logging.WARN, logging.DEBUG)
    initlog(log)


def initlog(plog):
    oda_lib.initlog(plog)
    c_m_d.initlog(plog)
    global logger
    logger = plog

def main(host):
    log_management(host.hostname)
    global dbname
    dbname = randomget_dbname(host)
    global oracle_home
    oracle_home = host.dbnametodbhome (dbname)
    if dbname:
        irestore_oss (host)
        irestore_nfs (host)
        irestore_others (host)
    else:
        log.error("Fail to get the dbname!")
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
    global dbname
    if arg['-d']:
        dbname = arg['-d']
    else:
        dbname = randomget_dbname(host)
    logger.info(dbname)
    if not dbname:
        logger.error("No dbname!")
        sys.exit(0)
    irestore_oss(host)
    irestore_nfs(host)
    irestore_others(host)
    print("Finished irestore-database test, please check log %s for details." % logfile)
