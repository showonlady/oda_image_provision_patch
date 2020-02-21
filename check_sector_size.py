#!/usr/bin/env python
# conding : utf-8

import oda_lib
import os
import logging
import initlogging
import common_fun as cf
import datetime

script_dir = cf.script_dir
sql_file = script_dir + '/' + "check_sector_size_parameter.sh"
remote_dir = "/tmp"
sql = "show parameter _disk_sector_size_override"
machine_info = script_dir + "/" + 'a.txt'
with open (machine_info, 'r') as f:
    machine_list = f.readlines()
machine_list = [line.strip() for line in machine_list]



def check_parameter(host):
    scripts(host, sql)
    remote_file = os.path.join (remote_dir, os.path.basename (sql_file))
    host.scp2node (sql_file, remote_file)
    giuser = host.griduser ()
    gigroup = host.gridgroup ()
    cmd1 = "/bin/chown %s:%s %s" % (giuser, gigroup, remote_file)
    cmd2 = "/bin/chmod +x %s" % remote_file
    cmd3 = "/bin/su - %s -c %s" % (giuser, remote_file)
    host.ssh2node (cmd1)
    host.ssh2node (cmd2)
    log.info ("Will check the parameter _disk_sector_size_override on host %s!" % host.hostname)
    result = host.ssh2node (cmd3) + '\n'
    log.info(result)
    result = result.strip()
    try:
        x = result.split()[-1].split()[-1]
    #print x
        if x.lower() != 'true':
            log.error ("The parameter _disk_sector_size_override is not correct on host %s" % host.hostname)
    except Exception as e:
        log.error("The parameter _disk_sector_size_override is not correct on host %s" % host.hostname)



def scripts(host, sql):
    asm_sid = host.asminstance()
    crs_home = host.gi_home()
    if not asm_sid:
        log.error ("Could not get the asm instance name for %s!" % host.hostname)
        sys.exit (0)
    fp = open (sql_file, 'w')
    fp.write ("#!/bin/bash\n")
    fp.write ("export ORACLE_SID=%s\n" % asm_sid)
    fp.write ("export ORACLE_HOME=%s\n" % crs_home)
    fp.write ("%s/bin/sqlplus -S -L / as sysasm <<EOF\n" % crs_home)
    fp.write ("%s;\n" % sql)
    fp.write ("EOF\n")
    fp.close ()


def main():
    username = "root"
    password = "welcome1"
    flag = 1
    for i in machine_list:
        items = i.split()
        if len(items) == 1:
            host = oda_lib.Oda_ha(items[0], username, password)
        elif len(items) == 2:
            host = oda_lib.Oda_ha(items[0], username, items[1])
        else:
            flag = 0
            log.error("The machine information is not correct! %s" % i)
        if flag:
            check_parameter(host)
            if host.is_ha_not():
                node2 = cf.node2_name(host.hostname)
                host2 = oda_lib.Oda_ha(node2, host.username, host.password)
                check_parameter(host2)






def initlog(plog):
    oda_lib.initlog(plog)
    global log
    log = plog


def log_management():
    log_stamp = datetime.datetime.today ().strftime ("%Y%m%d")
    logname = "Check_sector_size_parameter_%s.log" % log_stamp
    logfile = os.path.join(cf.log_dir, logname)
    log = initlogging.initLogging("check_sector_size", logfile, logging.INFO, logging.DEBUG)
    initlog(log)





if __name__ == '__main__':

    log_management()
    main()
