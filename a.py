#!/usr/bin/env python


"""
Usage:
    a.py -h
    a.py -s <servername> [-u <username>] [-p <password>] [-o <filename>] [--network <vlan>]


Options:
    -h,--help       Show this help message
    -v,--version     Show version
    -s <servername>  hostname of machine, if vlan,use ip instead
    -u <username>  username [default: root]
    -p <password>  password [default: welcome1]
    -o <jsonfile>  json file path [default: jsonfile]
    --network <vlan> network type, vlan, bonding, nonbonding
"""

#
from docopt import docopt
import time
import os
import datetime
import common_fun as cf
import sys
from multiprocessing import Process
import initlogging
import logging
import oda_lib
import pexpect


# LOG_FORMAT = '%(asctime)s - %(name)s - %(funcName)s - %(levelname)s: %(message)s'
# logging.basicConfig(level=logging.INFO,
#                     format=LOG_FORMAT)
# logger = logging.getLogger(__name__)


# def fun():
#
#     #logger = logging.getLogger(__name__ )
#     #
#     # handler = logging.FileHandler('error.log')
#     # # format = logging.Formatter(LOG_FORMAT)
#     # # handler.setFormatter(format)
#     #
#     # logger.addHandler(handler)
#
#     log = initlogging.initLogging("test","as.log", logging.INFO, logging.DEBUG)
#     i = 0
#     while True:
#         log.info("%s:" % i )
#
#         i += 1
#
# def bs():
#     log.error("THIS IS B")
#
#
# def login(child, password):
#     i = child.expect(["continue connecting", 'password: ', pexpect.TIMEOUT])
#     if i == 0:
#         child.sendline("yes")
#         child.expect("password")
#         child.sendline("%s" % password)
#     elif i == 1:
#         child.sendline("%s" % password)
#     else:
#         print "timeout!"
#         sys.exit(0)
#     return child

def fun(a, b):
    c = []
    i = 0
    j = 0
    if a == None or b == None:
        c = a + b
        return c


    while i < len(a) and j < len(b):
        if a [i]<b[j]:
            c.append(a[i])
            i = i + 1
        else:
            c.append(b[j])
            j = j + 1
    if i == len(a):
        c = c + b[j:]
    else:
        c = c + a[i:]
    return c

def fun2(a):
    flag = 1
    for i in range(1,len(a)):
        if a[i-1] == a[i]:
            flag = 0
            break
    if flag == 0:
        return [flag, i]
    else:
        return [flag]

def fun3(a, index):
    b = a[:index+1]
    b = int(b) + 1
    out = str(b)
    i = index + 1
    while i < len(a):
        out += '0'
        i += 1
    return out


def main(a):
    a = a + 1
    # a = str(a)
    # out = fun2(a)
    # print out
    # out2 = fun3(a, out[1])
    # print out2
    while True:
        a = str(a)
        out1 = fun2(a)
        if len(out1) == 1:
            print a
            return out1
        else:
            out2 = fun3(a, out1[1])
            a = int(out2)
            print a




def create_dbhome(host):
    logfile = "test.log"
    cmd = ["/opt/oracle/oak/bin/oakcli create dbhome -v 12.2.0.1.180417", ["'root'  password","welcome1"],
           ["password", "welcome1"], ["password","welcome1"],["password","welcome1"],["Edition", "2"]]
    child = cf.run_expect(host, cmd, logfile, 60)
    try:
        child.expect("Successfully", timeout = 600)
        print "Success create dbhome!"
    except Exception as e:
        print "Fail to create dbhome!"
    time.sleep(60)
    child.close()
    child.logfile.close()

def create_dbhome(host):
    logfile = "test.log"
    cmd = ["/opt/oracle/oak/bin/oakcli create dbhome -v 12.2.0.1.180417", ["'root'  password","welcome1"],
           ["password", "welcome1"], ["password","welcome1"],["password","welcome1"],["edition", "1"]]
    cf.run_expect(host, cmd, logfile, 60, 600)


def delete_dbhome(host):
    logfile = "test2.log"
    cmd = ["/opt/oracle/oak/bin/oakcli delete dbhome -oh OraDb12201_home4", ["'root'  password","welcome1"],
           ["password", "welcome1"], ["password","welcome1"],["password","welcome1"],["continue", "Y"]]
    child = cf.run_expect(host, cmd, logfile, 60)
    try:
        child.expect("Successfully", timeout = 600)
        print "Success create dbhome!"
    except Exception as e:
        print "Fail to create dbhome!"
    time.sleep(60)
    child.close()
    child.logfile.close()


def sql_result(host, sql):
    oracle_sid = host.dbnametoinstance(dbname)
    if not oracle_sid:
        host = oda_lib.Oda_ha(cf.node2_name(host.hostname), host.username, host.password)
        oracle_sid = host.dbnametoinstance(dbname)
        if not oracle_sid:
            log.error("Could not get the db instance name for %s!" % dbname)
            sys.exit(0)
    racuser1 = host.racuser()
    cmd = 'su - %s -c "echo -e \\"set lines 300; \\n set trimspool on; \\n %s ; \\n exit;\\n\\">/home/oracle/data.sql; export ORACLE_HOME=%s; export ORACLE_SID=%s; %s/bin/sqlplus -S -L / as sysdba  @/home/oracle/data.sql"' %(racuser1, sql, oracle_home,oracle_sid, oracle_home)
    result = host.ssh2node (cmd) + '\n'
    #return result
    print cmd
    print result

def srvctl_result(host):
    oracleuser = host.racuser()
    cmd = 'su - %s -c "echo -e \\"export ORACLE_HOME=%s;\\n%s/bin/srvctl status database -d %s;\\n\\">/home/%s/check.sh;sh /home/%s/check.sh"' % (oracleuser, oracle_home,oracle_home, dbname,oracleuser,oracleuser)
    result = host.ssh2node(cmd)+ '\n'
    print cmd
    print result

def srvctl_start(host):
    oracleuser = host.racuser()
    cmd = 'su - %s -c "echo -e \\"export ORACLE_HOME=%s;\\n%s/bin/srvctl start database -d %s;\\n\\">/home/%s/check.sh;sh /home/%s/check.sh"' % (oracleuser, oracle_home,oracle_home, dbname,oracleuser,oracleuser)
    result = host.ssh2node(cmd)+ '\n'
    print cmd
    print result

def initlog(plog):
    oda_lib.initlog(plog)
    global log
    log = plog


def log_management(hostname):
    logname = "test_%s.log" % hostname
    logfile = os.path.join(cf.log_dir, logname)
    log = initlogging.initLogging("test", logfile, logging.WARN, logging.DEBUG)
    initlog(log)


class chqin(object):
    def __init__(self, name):
        self.name = name
    def fun(self):
        print self.name
        name2 = self.name + "111"
        name2 = chqin(name2)
        print name2.name

if __name__ == '__main__':
    host = oda_lib.Oda_ha("rwsoda601c1n1", "root", "welcome1")

    #
    log_management("rwsoda601c1n1")
    host.stop_tfa()
    # logfile = "cleanup_%s.log" % host.hostname
    # cmd = "perl /opt/oracle/oak/onecmd/cleanup.pl -griduser %s -dbuser %s" % (host.griduser (), host.racuser ())
    # #cf.cleanup_deployment(host,cmd)
    # create_dbhome(host)
    # delete_dbhome(host)
    # sql = "select to_char(sysdate, 'mm/dd/yyyy hh24:mi:ss')PITR from dual"
    # global dbname
    # global oracle_home
    # dbname = "odacn"
    # oracle_home = host.dbnametodbhome (dbname)
    # srvctl_result(host)
    # sql_file = "/home/oracle/data.sql"
    # sql_result(host, sql)
    #
    # result,error = host.ssh2node_input("%s delete-database  -in NtCp1" % host.ODACLI)
    # print result,error

    # options= "-cl OLTP -s odb1 -dr ACFS -y SI -no-f  -n Pdx -u dzhw3x -r /tmp/backupreport.br -on Ja -m  -bp"
    # host.irestore_database(options)


