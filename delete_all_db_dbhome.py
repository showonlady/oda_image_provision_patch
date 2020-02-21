#!/usr/bin/env python
#encoding utf-8
"""
Usage:
    delete_all_db_dbhome.py -h
    delete_all_db_dbhome.py -s <servername> [-u <username>] [-p <password>]

Options:
    -h,--help       Show this help message
    -s <servername>  hostname of machine, if vlan,use ip instead
    -u <username>  username [default: root]
    -p <password>  password [default: welcome1]
"""

from docopt import docopt
import oda_lib
import common_fun as cf
import os
import logging
import initlogging


def delete_all_dbhomes(host):
    cmd = "/opt/oracle/dcs/bin/odacli list-dbhomes|awk 'NR>3 {print $1}'"
    home_id = host.ssh2node(cmd)
    for i in home_id.split():
        if not host.delete_dbhome("-i %s" % i):
            print "delete dbhome %s failed!\n" % i


def delete_all_databases(host):
    cmd = "/opt/oracle/dcs/bin/odacli list-databases|awk 'NR>3 {print $2}'"
    db_id = host.ssh2node(cmd)
    for i in db_id.split():
        if not host.delete_database("-in %s -fd" % i):
            print "delete database %s failed!\n" % i

def initlogger(hostname):
    global logfile
    logname = "delete_all_dbhome_%s.log" % hostname
    logfile = os.path.join(cf.log_dir, logname)
    log = initlogging.initLogging("delete_dbhome", logfile, logging.WARN, logging.DEBUG)
    oda_lib.initlog(log)





def main(hostname, username, password):
    initlogger(hostname)
    host = oda_lib.Oda_ha(hostname,username,password)
    delete_all_databases(host)
    delete_all_dbhomes(host)


if __name__ == '__main__':
    arg = docopt (__doc__)
    print arg
    hostname = arg['-s']
    username = arg['-u']
    password = arg['-p']
    main (hostname, username, password)

