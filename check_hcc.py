#!/usr/bin/env python


"""
Usage:
    unified_auditing.py -h
    unified_auditing.py -s <servername> [-u <username>] [-p <password>] [-d <dbname>]


Options:
    -h,--help       Show this help message
    -s <servername>  hostname of machine, if vlan,use ip instead
    -u <username>  username [default: root]
    -p <password>  password [default: welcome1]
    -d <dbname> the db name
"""
from docopt import docopt
import re,os,sys
import oda_lib
import common_fun as cf
import initlogging
import logging
import random
hcc_scripts = cf.script_dir + "/hcc_check.sql"


def valide_db(host, dbname):
    d = host.describe_database ("-in %s" % dbname)
    edition = d['dbEdition']
    storage = d['dbStorage']
    log.info ("The db %s edition is %s!" % (dbname, edition))
    log.info ("The db %s storage is %s!" % (dbname, storage))
    #if edition.lower() == "se" or storage.lower() == "acfs":
    if edition.lower () == "se" :

        return 0
    else:
        return 1


def check_hcc(host,dbname):
    if not valide_db(host, dbname):
        log.info("The db %s was not supported!" % dbname)
        return 0
    racuser = host.racuser()
    racgroup = host.racgroup()
    oracle_home = host.dbnametodbhome(dbname)
    oracle_sid = host.dbnametoinstance(dbname)
    remote_dir = "/home/%s" % racuser
    remote_file = os.path.join(remote_dir, os.path.basename(hcc_scripts))
    result_file = os.path.join(remote_dir, "hcc_result.txt")
    host.scp2node(hcc_scripts, remote_file)
    cmd1 = "/bin/chown %s:%s %s" % (racuser, racgroup, remote_file)
    cmd2 = "/bin/chmod +x %s" % remote_file
    cmd3 = 'sudo su - %s -c "export ORACLE_HOME=%s; ' \
          'export ORACLE_SID=%s; %s/bin/sqlplus -S -L / as sysdba  @%s"' % (racuser, oracle_home,oracle_sid, oracle_home, remote_file)
    host.ssh2node(cmd1)
    host.ssh2node(cmd2)
    host.ssh2node(cmd3)
    #log.info(result3 + "\n")
    log.info("=" *30)
    log.info("HCC on db %s"  % dbname)
    log.info("=" *30)
    log.info(host.ssh2node("cat %s" % result_file))

def main(host):
    cf.extend_space_u01(host)
    for i in host.db_versions:
        if not re.match("11.2", i):
            dbname = cf.generate_string(cf.string1, 8)
            options = "-hm WElcome12_- -n %s -de EE -v %s" %(dbname, i)
            if host.create_database(options):
                check_hcc(host, dbname)
                dbhome = host.describe_database("-in %s" %dbname)
                dbhomeid = dbhome['dbHomeId']
                dbname1 = cf.generate_string(cf.string1,8)
                options1 = "-hm WElcome12_- -n %s -dh %s -r ACFS" %( dbname1, dbhomeid)
                if host.create_database(options1):
                    check_hcc (host, dbname1)
        else:
            dbname = cf.generate_string (cf.string1, 8)
            options = "-hm WElcome12_- -n %s -de EE -v %s -r ACFS" % (dbname, i)
            if host.create_database (options):
                check_hcc (host, dbname)



def initlog(plog):
    oda_lib.initlog(plog)
    global log
    log = plog

def log_management(hostname):
    global logfile
    logname = "check_hcc_%s.log" % hostname
    logfile = os.path.join (cf.log_dir, logname)
    log = initlogging.initLogging ("hcc", logfile, logging.WARN, logging.DEBUG)
    initlog(log)

if __name__ == '__main__':
    arg = docopt(__doc__)
    print arg
    hostname = arg['-s']
    username = arg['-u']
    password = arg['-p']
    log_management(hostname)
    host = oda_lib.Oda_ha(hostname, username, password)
    if arg['-d']:
        dbname = arg['-d']
        check_hcc(host, dbname)
    else:
        main(host)

    print "Done, please check the log %s for details!" % logfile