#!/usr/bin/env python
#conding utf-8


"""
Usage:
    disk_testing.py -h
    disk_testing.py  -s <servername> [-u <username>] [-p <password>]

Options:
    -h,--help       Show this help message
    -s <servername>   hostname of machine
    -u <username>   username [default: root]
    -p <password>   password [default: welcome1]
"""


from docopt import docopt
import oda_lib
import simplejson
import os
import common_fun as cf
import datetime
import time
import logging
import logger
from multiprocessing import Process

remote_dir = "/u01"
change_asm_power_file = "change_asm_power.sh"
check_asmdisk_file = "check_asm_disk.sh"
log_dir = cf.log_dir
asm_file = os.path.join(remote_dir, check_asmdisk_file)
power_file = os.path.join(remote_dir, change_asm_power_file)



def change_power(host):
    giuser = host.griduser()
    gigroup = host.gridgroup()
    gi_home = grid_home(host, giuser)
    gi_sid = grid_sid(host)
    change_power_scripts(host, gi_home, gi_sid)
    scp_modify_file(host, change_asm_power_file, giuser, gigroup)
    cmd = "/bin/su - %s -c %s" % (giuser, power_file)
    host.ssh2node(cmd)


def generate_asm_disk_script(host):
    giuser = host.griduser()
    gigroup = host.gridgroup()
    gi_home = grid_home(host, giuser)
    gi_sid = grid_sid(host)
    check_asmdisk_scripts(host, gi_home, gi_sid)
    scp_modify_file(host, check_asmdisk_file, giuser, gigroup)


def scp_modify_file(host, file, giuser, gigroup):
    remote_file = os.path.join(remote_dir, os.path.basename(file))
    host.scp2node(file, remote_file)
    cmd1 = "/bin/chown %s:%s %s" % (giuser, gigroup, remote_file)
    cmd2 = "/bin/chmod +x %s" % remote_file
    host.ssh2node(cmd1)
    host.ssh2node(cmd2)



def change_power_scripts(host, gi_home, gi_sid):
    sql = "alter system set asm_power_limit=32 scope=both"
    fp = open(change_asm_power_file, 'w')
    fp.write("#!/bin/bash\n")
    fp.write("export ORACLE_SID=%s\n" % gi_sid)
    fp.write("export ORACLE_HOME=%s\n" % gi_home)
    fp.write("%s/bin/sqlplus -S -L / as sysasm <<EOF\n" % gi_home)
    fp.write("%s;\n" % sql)
    fp.write("EOF\n")
    fp.close()


def check_asmdisk_scripts(host, gi_home, gi_sid):

    sql = "set linesize 200 colsep '|' pagesize 2000;\n" \
          "col name format a23;\n" \
          "col disk_number format 999; \n" \
          "col path format a35;\n" \
          "col header_status format a9; \n" \
          "col library format a6; \n" \
          "col failgroup format a22; \n" \
          "col state format a10;\n " \
          "select group_number,disk_number,state,mount_status,HEADER_STATUs,MODE_STatus ,name,path from v\$asm_disk order by group_number,disk_number,name;\n " \
          "select * from v\$asm_operation;\n "

    fp = open(check_asmdisk_file, 'w')
    fp.write("#!/bin/bash\n")
    fp.write("export ORACLE_SID=%s\n" % gi_sid)
    fp.write("export ORACLE_HOME=%s\n" % gi_home)
    fp.write("%s/bin/sqlplus -S -L / as sysasm <<EOF\n" % gi_home)
    fp.write("%s\n" % sql)
    fp.write("EOF\n")





def grid_home(host, giuser):
    cmd = "ls -d /u01/app/18*/%s" % giuser
    result = host.ssh2node(cmd)
    return result

def grid_sid(host):
    cmd = "ps -ef|grep asm_pmon|grep -v grep|awk '{print $8}'|awk -F_ '{print $3}'"
    result = host.ssh2node(cmd)
    return result


def scp_stat(host):
    stat = "stats.sh"
    remote_file = os.path.join(remote_dir, os.path.basename(stat))
    host.scp2node(stat,remote_file)



def host_monitor(host):
    giuser = host.griduser()
    generate_asm_disk_script(host)
    scp_stat(host)
    hostname = host.hostname
    dcs_flag = host.is_dcs_or_oak()
    if dcs_flag:
        cli = "/opt/oracle/oak/bin/odaadmcli"
    else:
        cli = "/opt/oracle/oak/bin/odacli"
    cmd1 = cli + " show disk"
    cmd2 = cli + " show storage -errors"
    cmd3 = "sh /u01/stats.sh"
    cmd4 = "/bin/su - %s -c %s" % (giuser, asm_file)

    #fp = open(log, 'a')
    while True:
        result1 = host.ssh2node(cmd1)
        result2 = host.ssh2node(cmd2)
        result3 = host.ssh2node(cmd3)
        result4 = host.ssh2node(cmd4)
        log.info( "*" * 80)
        log.info("*" * 80 )
        log.info(cmd1)
        log.info(result1)
        log.info(cmd2)
        log.info(result2)
        log.info(cmd3)
        log.info(result3)
        log.info(result4)
        # fp.write("\n\n" + "*" * 80)
        # fp.write("*" * 80 + "\n\n")
        # fp.flush()
        # fp.write(timestamp + "\n")
        # fp.write("\n" + cmd1 + "\n")
        # fp.write(result1 + "\n")
        # fp.flush()
        # fp.write("\n" + cmd2 + "\n")
        # fp.write(result2 + "\n")
        # fp.flush()
        # fp.write("\n" + cmd3 + "\n")
        # fp.write(result3 + "\n")
        # fp.flush()
        # fp.write("\n" + result4 + "\n")
        # fp.flush()
        # timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        # fp.write(timestamp + "\n")
        # fp.flush()
        time.sleep(10)



def initlogger(hostname):
    global logfile
    logname = "disk_status_%s.log" % hostname
    logfile = os.path.join(cf.log_dir, logname)
    log = initlogging.initLogging("dsk_dst", logfile, logging.WARN, logging.DEBUG)
    return log


def initlog(plog):
    oda_lib.initlog(plog)
    global log
    log = plog


def log_management(hostname):
    log = initlogger(hostname)
    initlog(log)



if __name__ == '__main__':
    arg = docopt(__doc__)
    print arg
    hostname = arg['-s']
    username = arg['-u']
    password = arg['-p']
    log_management(hostname)
    host = oda_lib.Oda_ha(hostname, username, password)
    change_power(host)
    host_monitor(host)
