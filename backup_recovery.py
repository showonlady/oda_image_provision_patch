#!/usr/bin/env python
#encoding utf-8
#
# Copyright (c) 2018, Oracle and/or its affiliates. All rights reserved.
#
#    NAME
#      backup_recovery.py
#
#    DESCRIPTION
#      Sanity check for the backup and recovery commands
#
#    NOTES
#
#
#    MODIFIED   (MM/DD/YY)
#    chqin    4/15/18 - Creation
#

"""
Usage:
    backup_recovery.py -h
    backup_recovery.py  -s <servername> [-u <username>] [-p <password>] [-d <dbname>]
    backup_recovery.py [case1] -s <servername> [-u <username>] [-p <password>] [-d <dbname>]


Options:
    -h,--help       Show this help message
    -s <servername>  hostname of machine, if vlan,use ip instead
    -u <username>  username [default: root]
    -p <password>  password [default: welcome1]
    -d <dbname>   The db name
    case1  Do the case for Long term backup on CDB databases post a Level 0 backup
"""


from docopt import docopt
import oda_lib
import random
import common_fun as cf
import create_multiple_db as c_m_d
import os
import re
from sys import argv
import sys
import time
import logging
import initlogging

sql_file = 'sql_check.sh'
delete_file_name = 'delete_file.sh'
backupreport = 'backupreport.br'
dbstatus = 'dbstatus_check.sh'
scn_sql = "select current_scn SCN from v\\\\\$database"
pitr_sql = "select to_char(sysdate, 'mm/dd/yyyy hh24:mi:ss')PITR from dual"
spfile_sql = "select value from v\\\\\$parameter where name ='spfile'"
control_sql = "select name from v\\\\\$controlfile"
datafile_sql = "select name from v\\\\\$datafile"
remote_dir = '/tmp'
bkpassword = "WElcome12_-"
#dbname = argv[1]

tag = cf.generate_string(cf.string2,8)


def randomget_dbname(host):
    cmd = "/opt/oracle/dcs/bin/odacli list-databases|grep Configured|awk '{print $2}'"
    result, error = host.ssh2node_job(cmd)
    if result and not error:
        dbname = random.choice(result.split())
        return dbname
    else:
        dbname = create_new_db(host)
        return dbname



def create_new_db(host):
    dbversion = random.choice(host.db_versions)
    if not c_m_d.is_clone_exists_or_not (host, dbversion):
        c_m_d.scp_unpack_clone_file (host, dbversion)
    if host.create_database("-hm WElcome12_- -n testxx -v %s " % dbversion):
        return "testxx"
    else:
        return 0

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


def case1(host):
    ###Check if dns is configured
    ## if not, add "10.241.247.6  storage.oraclecorp.com" to /etc/hosts
    update_hosts(host)
    ###set the agent proxy###
    if not host.update_agentproxy():
        log.error("Fail to set the agent proxy!")
        sys.exit(0)
    ###Create an object store
    oss_name = cf.generate_string(cf.string2, 8)
    oss_result = host.create_objectstoreswift(oss_name)
    if not oss_result :
        return 0
    ##Create backup config
    op_oss = "-d ObjectStore -c chqin -on %s " % oss_name
    #op_oss = "-d ObjectStore -c 'oda-oss' -on %s " % oss_name
    op = ['-cr -w 1','-no-cr -w 15','-cr -w 30']
    bk_name = cf.generate_string(cf.string1, 8)
    bk_op = '-n %s ' % bk_name + op_oss + random.choice(op)
    if not host.create_backupconfig(bk_op):
        log.error("create backup config %s fail!\n" % bk_name)
        return 0
    ##Update the database with the new create backup config
    updatedb_op = "-in %s -bin %s -hbp %s" %(dbname, bk_name,bkpassword)
    if not host.update_database(updatedb_op):
        log.error("update db %s with backup config %s fail!\n" % (dbname, bk_name))
        return 0
    time.sleep(120)
    host.disable_auto_backup()
    ####Create a level 0 backup
    op_level0 = "-bt Regular-L0 -in %s " % dbname
    if not host.create_backup(op_level0):
        log.error("create Regular-L0 backup fail %s\n" % op)
        return 0
    ###Create a longter backup
    tag = cf.generate_string(cf.string2, 8)
    op_longterm = "-bt Longterm -in %s -k 1 -t %s" % (dbname, tag)
    if not host.create_backup(op_longterm):
        log.error("create Longterm backup fail %s\n" % op)
        return 0
    host.disable_auto_backup()


def backup_disk(host):
    op = ['-cr -w 1','-no-cr -w 7','-cr -w 14']
    name = cf.generate_string(cf.string1, 8)
    for i in range(0,len(op)):
        bk_name = name + str(i)
        bk_op = '-d Disk '+ '-n %s ' % bk_name + op[i]
        if not host.create_backupconfig(bk_op):
            log.error("create backup config %s fail!\n" % bk_name)
            return 0
        updatedb_op = "-in %s -bin %s" %(dbname, bk_name)
        if not host.update_database(updatedb_op):
            log.error("update db %s with backup config %s fail!\n" % (dbname, bk_name))
            return 0

        if i == 0:
            tag1 = cf.generate_string(cf.string2, 8)
            create_bk_op_n = ["-bt Longterm -in %s -k 1 -t test" % dbname, "-c TdeWallet -in %s" % dbname,
                          "-bt Regular-L0 -in %s -k 1" % dbname, "-bt ArchiveLog -in %s -t %s" % (dbname, tag1)]
            for j in range(0, len(create_bk_op_n)):
                if host.create_backup(create_bk_op_n[j]) and j != 3:
                    log.error("Negtive case for backup fail! %s \n" % create_bk_op_n[j])
        host.disable_auto_backup()
        if not recover_test(host):
            sys.exit(0)

def backup_oss(host):
    ###Check if dns is configured
    ## if not, add "10.241.247.6  storage.oraclecorp.com" to /etc/hosts
    update_hosts(host)
    if host.is_ha_not():
        host2name = cf.node2_name(host.hostname)
        host2 = oda_lib.Oda_ha(host2name, host.username, host.password)
        update_hosts(host2)
    ###set the agent proxy###
    if not host.update_agentproxy():
        log.error("Fail to set the agent proxy!")
        sys.exit(0)
    oss_name = cf.generate_string(cf.string2, 8)
    log.info(oss_name)
    oss_result = host.create_objectstoreswift(oss_name)
    if not oss_result :
        return 0
    op_oss = "-d ObjectStore -c chqin -on %s " % oss_name
    #op_oss = "-d ObjectStore -c 'oda-oss' -on %s " % oss_name
    op = ['-cr -w 1','-no-cr -w 15','-cr -w 30']
    name = cf.generate_string(cf.string1, 8)
    for i in range(len(op)):
        bk_name = name + str(i)
        bk_op = '-n %s ' % bk_name + op_oss + op[i]
        if not host.create_backupconfig(bk_op):
            log.error("create backup config %s fail!\n" % bk_name)
            return 0
        updatedb_op = "-in %s -bin %s -hbp %s" %(dbname, bk_name,bkpassword)
        if not host.update_database(updatedb_op):
            log.error("update db %s with backup config %s fail!\n" % (dbname, bk_name))
            return 0

        if i == 0:
            tag1 = cf.generate_string(cf.string2, 8)
            create_bk_op_n = ["-bt Longterm -in %s -k 1" % dbname, "-c TdeWallet -in %s" % dbname,
                          "-bt Regular-L0 -in %s -k 1" % dbname, "-bt ArchiveLog -in %s -t %s" % (dbname, tag1)]
            for j in range(0, len(create_bk_op_n)):
                if host.create_backup(create_bk_op_n[j]) and j != 3:
                    log.error("Negtive case for backup fail! %s \n" % create_bk_op_n[j])
        host.disable_auto_backup()
        time.sleep(120)
        if not recover_test_oss(host):
            sys.exit(0)


def create_bk_op_oss():
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


def recover_test_oss(host):
    op = create_bk_op_oss()
    if not host.create_backup(op):
        log.error("create backup fail %s\n" % op)
        return 0
    allfile_loss(host)
    if not host.recover_database("-in %s -t Latest -hp %s" % (dbname, bkpassword)):
        log.error("recover database with latest fail %s\n" % dbname)
        return 0
    check_dbstatus(host)

    op = create_bk_op_oss()
    #op = "-bt Regular-L1 -c Database -in %s" % dbname
    if not host.create_backup(op):
        log.error("create backup fail %s\n" % op)
        return 0
    s = current_scn(host)
    sp_control_loss(host)
    if not host.recover_database("-in %s -t SCN -s %s -hp %s" % (dbname, s, bkpassword)):
        log.error("recover database with SCN fail! %s\n" % dbname)
        return 0
    check_dbstatus(host)

    op = create_bk_op_oss()
    if not host.create_backup(op):
        log.error("create backup fail! %s\n" % op)
        return 0
    p = current_pitr(host)
    control_datafile_loss(host)
    if not host.recover_database("-in %s -t PITR -r %s -hp %s" % (dbname, p,bkpassword)):
        log.error("recover database with PIRT fail! %s\n" % dbname)
        return 0
    check_dbstatus(host)
    op = create_bk_op_oss()
    if not host.create_backup(op):
        log.error("create backup fail %s\n" % op)
        return 0
    generate_backupreport(host)
    sp_datafile_loss(host)
    br = os.path.join(remote_dir, os.path.basename(backupreport))
    if not host.recover_database("-in %s -br %s -hp %s" % (dbname,br,bkpassword)):
        log.error("recover database with backupreport fail! %s\n" % dbname)
        return 0
    check_dbstatus(host)
    return 1


def recover_test(host):
    create_bk_op_disk = ["-bt Regular-L0 -in %s " % dbname, "-bt Regular-L1 -c Database -in %s" % dbname,
                         "-bt Regular-L0 -in %s -t %s" % (dbname, tag), "-bt Regular-L1 -in %s -t %s" % (dbname, tag)]
    op = random.choice(create_bk_op_disk)
    if not host.create_backup(op):
        log.error("create backup fail %s\n" % op)
        return 0
    allfile_loss(host)
    if not host.recover_database("-in %s -t Latest" % dbname):
        log.error("recover database with latest fail %s\n" % dbname)
        return 0
    check_dbstatus(host)

    op = random.choice(create_bk_op_disk)
    if not host.create_backup(op):
        log.error("create backup fail %s\n" % op)
        return 0
    s = current_scn(host)
    sp_control_loss(host)
    if not host.recover_database("-in %s -t SCN -s %s" % (dbname, s)):
        log.error("recover database with SCN fail! %s\n" % dbname)
        return 0
    check_dbstatus(host)

    op = random.choice(create_bk_op_disk)
    if not host.create_backup(op):
        log.error("create backup fail! %s\n" % op)
        return 0
    p = current_pitr(host)
    control_datafile_loss(host)
    if not host.recover_database("-in %s -t PITR -r %s" % (dbname, p)):
        log.error("recover database with PIRT fail! %s\n" % dbname)
        return 0
    check_dbstatus(host)
    op = random.choice(create_bk_op_disk)
    if not host.create_backup(op):
        log.error("create backup fail %s\n" % op)
        return 0
    generate_backupreport(host)
    sp_datafile_loss(host)
    br = os.path.join(remote_dir, os.path.basename(backupreport))
    if not host.recover_database("-in %s -br %s" % (dbname,br)):
        log.error("recover database with backupreport fail! %s\n" % dbname)
        return 0
    check_dbstatus(host)
    return 1


def generate_backupreport(host):
    cmd1 = "/opt/oracle/dcs/bin/odacli list-backupreports|egrep -i 'Regular-|Long'|tail -n 1|awk '{print $1}'"
    bkreport_id = host.ssh2node(cmd1)
    bkreport = host.describe_backupreport("-i %s" %bkreport_id)
    fp = open(backupreport, 'w')
    fp.write(bkreport)
    fp.close()
    remote_file = os.path.join(remote_dir, os.path.basename(backupreport))
    host.scp2node(backupreport, remote_file)

"""
def check_dbstatus(host):
    #oracle_home = host.dbnametodbhome(dbname)
    fp = open(dbstatus, 'w')
    fp.write("#!/bin/bash\n")
    fp.write("export ORACLE_HOME=%s\n" % oracle_home)
    fp.write("%s/bin/srvctl status database -d %s;\n" % (oracle_home, dbname))
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
    log.info(result)
"""
def check_dbstatus(host):
    oracleuser = host.racuser()
    cmd = 'su - %s -c "echo -e \\"export ORACLE_HOME=%s;\\n%s/bin/srvctl status database -d %s;\\n\\">/home/%s/check.sh;sh /home/%s/check.sh"' % (oracleuser, oracle_home,oracle_home, dbname,oracleuser,oracleuser)
    result = host.ssh2node(cmd)+ '\n'
    log.info(cmd)
    log.info(result)

def start_db_by_srvctl(host):
    oracleuser = host.racuser()
    cmd = 'su - %s -c "echo -e \\"export ORACLE_HOME=%s;\\n%s/bin/srvctl start database -d %s;\\n\\">/home/%s/check.sh;sh /home/%s/check.sh"' % (oracleuser, oracle_home,oracle_home, dbname,oracleuser,oracleuser)
    result = host.ssh2node(cmd)+ '\n'
    log.info(cmd)
    log.info(result)

"""
def start_db_by_srvctl(host):
    #oracle_home = host.dbnametodbhome(dbname)
    fp = open(dbstatus, 'w')
    fp.write("#!/bin/bash\n")
    fp.write("export ORACLE_HOME=%s\n" % oracle_home)
    fp.write("%s/bin/srvctl start database -d %s;\n" % (oracle_home, dbname))
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
    log.info(result)
"""
def current_scn(host):
    result = sql_result(host,scn_sql)
    result = result.strip()
    x = result.split('\n')
    y = x[-1].strip()
    return y


def current_pitr(host):
    result = sql_result(host,pitr_sql)
    result = result.strip()
    x = result.split('\n')
    y = x[-1].strip()
    return y


def datafile_loss(host):
    file = sql_result(host, datafile_sql)
    delete_file(host,file)

def controlfile_loss(host):
    file = sql_result(host, control_sql)
    delete_file(host,file)

def spfile_loss(host):
    file = sql_result(host, spfile_sql)
    delete_file(host,file)

def allfile_loss(host):
    datafile = sql_result(host, datafile_sql)
    controlfile = sql_result(host, control_sql)
    spfile = sql_result(host, spfile_sql)
    file = datafile + controlfile + spfile
    log.info(file)
    delete_file(host,file)

def sp_control_loss(host):
    controlfile = sql_result(host, control_sql)
    spfile = sql_result(host, spfile_sql)
    file = controlfile + spfile
    log.info(file)
    delete_file(host, file)

def sp_datafile_loss(host):
    datafile = sql_result(host, datafile_sql)
    spfile = sql_result(host, spfile_sql)
    file = datafile + spfile
    log.info(file)
    delete_file(host, file)

def control_datafile_loss(host):
    datafile = sql_result(host, datafile_sql)
    controlfile = sql_result(host, control_sql)
    file = datafile + controlfile
    delete_file(host,file)

def delete_file(host, x):
    if db_on_asm_acfs(host):
        delete_asm_file(host,x)
    else:
        delete_acfs_file(host,x)


def sql_result(host, sql):
    oracle_sid = host.dbnametoinstance(dbname)
    if not oracle_sid:
        if host.is_ha_not():
            host = oda_lib.Oda_ha(cf.node2_name(host.hostname), host.username, host.password)
            oracle_sid = host.dbnametoinstance(dbname)
            if not oracle_sid:
                log.error("Could not get the db instance name for %s!" % dbname)
                sys.exit(0)
        else:
            log.error ("Could not get the db instance name for %s!" % dbname)
            sys.exit (0)

    racuser = host.racuser()
    cmd = 'su - %s -c "echo -e \\"set lines 300; \\n set trimspool on; \\n %s; \\n exit;\\n\\">/home/%s/%s; export ORACLE_HOME=%s; ' \
          'export ORACLE_SID=%s; %s/bin/sqlplus -S -L / as sysdba  @/home/%s/%s"' % (racuser,sql, racuser, sql_file, oracle_home,oracle_sid, oracle_home,racuser, sql_file)
    result = host.ssh2node (cmd) + '\n'
    return result


def sql_result_bk(host, sql):
    oracle_sid = host.dbnametoinstance(dbname)
    if not oracle_sid:
        log.error("Could not get the db instance name for %s!" % dbname)
        sys.exit(0)

    #oracle_home = host.dbnametodbhome(dbname)
    fp = open(sql_file, 'w')
    fp.write("#!/bin/bash\n")
    fp.write("export ORACLE_SID=%s\n" % oracle_sid)
    fp.write("export ORACLE_HOME=%s\n" % oracle_home)
    fp.write("%s/bin/sqlplus -S -L / as sysdba <<EOF\n" % oracle_home)
    fp.write("%s;\n" % sql)
    fp.write("EOF\n")
    fp.close()
    remote_file = os.path.join(remote_dir, os.path.basename(sql_file))
    host.scp2node(sql_file, remote_file)
    racuser = host.racuser()
    racgroup = host.racgroup()
    cmd1 = "/bin/chown %s:%s %s" % (racuser, racgroup, remote_file)
    cmd2 = "/bin/chmod +x %s" % remote_file
    cmd3 = "/bin/su - %s -c %s" % (racuser, remote_file)
    host.ssh2node(cmd1)
    host.ssh2node(cmd2)
    result = host.ssh2node(cmd3) + '\n'
    return result

def sql_script(host,sql):
    oracle_sid = host.dbnametoinstance(dbname)
    if not oracle_sid:
        log.error("Could not get the db instance name for %s!" % dbname)
        sys.exit(0)

    #oracle_home = host.dbnametodbhome(dbname)
    fp = open(sql_file, 'w')
    fp.write("#!/bin/bash\n")
    fp.write("export ORACLE_SID=%s\n" % oracle_sid)
    fp.write("export ORACLE_HOME=%s\n" % oracle_home)
    fp.write("%s/bin/sqlplus -S -L / as sysdba <<EOF\n" % oracle_home)
    fp.write("%s;\n" % sql)
    fp.write("EOF\n")
    fp.close()

#asm --1
#acfs --0
def db_on_asm_acfs(host):
    d = host.describe_database("-in %s" % dbname)
    if not d:
        log.error("Describe-database return none.")
        return 0
    if d["dbStorage"] == 'ASM':
        return 1
    else:
        return 0


def delete_asm_file(host,x):
    fp = open(delete_file_name, 'w')
    y = x.split()
    for i in y:
        if re.search("^\+", i):
            i.strip('\n')
            fp.write("asmcmd rm -rf %s\n" % i)
    fp.close()
    remote_file = os.path.join(remote_dir, os.path.basename(delete_file_name))
    host.scp2node(delete_file_name, remote_file)
    griduser = host.griduser()
    gridgroup = host.gridgroup()
    cmd1 = "/bin/chown %s:%s %s" % (griduser, gridgroup, remote_file)
    cmd2 = "/bin/chmod +x %s" % remote_file
    cmd3 = "/bin/su - %s -c %s" % (griduser, remote_file)
    host.ssh2node(cmd1)
    host.ssh2node(cmd2)
    sql_result(host,"shutdown immediate")
    host.ssh2node(cmd3)
    #sql_result(host, "startup")
    start_db_by_srvctl(host)

def delete_acfs_file(host, x):
    fp = open(delete_file_name, 'w')
    y = x.split()
    for i in y:
        if re.search("^/", i):
            i.strip('\n')
            fp.write("rm -rf %s\n" % i)
    fp.close()
    remote_file = os.path.join(remote_dir, os.path.basename(delete_file_name))
    host.scp2node(delete_file_name, remote_file)
    griduser = host.griduser()
    log.info(griduser)
    gridgroup = host.gridgroup()
    log.info(gridgroup)
    cmd1 = "/bin/chown %s:%s %s" % (griduser, gridgroup, remote_file)
    cmd2 = "/bin/chmod +x %s" % remote_file
    cmd3 = "/bin/su - %s -c %s" % (griduser, remote_file)
    host.ssh2node(cmd1)
    host.ssh2node(cmd2)
    host.ssh2node(cmd3)


def initlogger(hostname):
    global logfile
    logname = "backup_recovery_%s.log" % hostname
    logfile = os.path.join(cf.log_dir, logname)
    log = initlogging.initLogging("bk_recovery", logfile, logging.WARN, logging.DEBUG)
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
    #logfile_name = 'check_back_recovery_%s.log' % hostname
    #fp, out, err,log = cf.logfile_name_gen_open(logfile_name)
    log_management(hostname)
    host = oda_lib.Oda_ha(hostname, username, password)
    global dbname
    dbname = randomget_dbname(host)
    global oracle_home
    oracle_home = host.dbnametodbhome (dbname)
    if dbname:
        backup_disk(host)
        backup_oss(host)
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
    #logfile_name = 'check_back_recovery_%s.log' % hostname
    #fp, out, err,log = cf.logfile_name_gen_open(logfile_name)
    log_management(hostname)
    host = oda_lib.Oda_ha(hostname, username, password)
    global dbname
    if arg['-d']:
        dbname = arg['-d']
    else:
        dbname = randomget_dbname(host)
    log.info(dbname)
    if not dbname:
        log.error("No dbname!")
        sys.exit(0)
    global oracle_home
    oracle_home = host.dbnametodbhome (dbname)

    if arg['case1']:
        case1(host)
    else:
        backup_oss(host)
        backup_disk(host)
    print "Done, please check the log %s for details!" % logfile

