
#!/usr/bin/env python
#coding utf-8
#
# Copyright (c) 2018, Oracle and/or its affiliates. All rights reserved.
#
#    NAME
#      check_odacli_other.py
#
#    DESCRIPTION
#      Sanity check for other odacli commands
#
#    NOTES
#
#
#    MODIFIED   (MM/DD/YY)
#    chqin    12/15/18 - Creation
#

"""
Usage:
    check_odacli_other.py -h
    check_odacli_other.py -s <servername> [-u <username>] [-p <password>]

Options:
    -h,--help       Show this help message
    -s <servername>  hostname of machine, if vlan,use ip instead
    -u <username>  username [default: root]
    -p <password>  password [default: welcome1]
"""
from docopt import docopt
import oda_lib
import common_fun
import os
import logging
import initlogging
import common_fun as cf
import oda_patch as o_p

def odacli_cmd_check(host):
    flag = 1
    options = ['ping-agent -j', 'list-featuretracking -j', 'describe-latestpatch -j', "list-agentconfig-parameters"
               , 'list-availablepatches -j', 'list-backupreports', 'list-nodes', 'list-pendingjobs',
              'list-scheduled-executions']
    for i in options:
        cmd = host.ODACLI + i
        if not host.simple_run(cmd):
            flag = 0
    return flag


def describe_component(host):
    flag = 1
    cmd1 = host.ODACLI + 'describe-component'
    cmd2 = host.ODACLI + 'describe-component -d'
    cmd3 = host.ODACLI + 'describe-component -l'
    cmd4 = host.ODACLI + 'describe-component -n 0'
    cmd5 = host.ODACLI + 'describe-component -n 1'
    cmd6 = host.ODACLI + 'describe-component -s'
    cmd7 = host.ODACLI + 'describe-component -v'
    if host.is_ha_not():
        cmd = [cmd1, cmd2, cmd3, cmd4, cmd5, cmd6, cmd7]
    else:
        cmd = [cmd1, cmd2, cmd3, cmd4, cmd6, cmd7]
    for i in cmd:
        if not host.simple_run(i):
            flag = 0
    return flag

def check_dgstorage(host):
    flag = 1
    cmd1 = host.ODACLI + 'describe-dgstorage'
    cmd2 = host.ODACLI + 'describe-dgstorage -d data'
    cmd3 = host.ODACLI + 'describe-dgstorage -d reco'
    cmd4 = host.ODACLI + 'describe-dgstorage -d flash'
    cmd5 = host.ODACLI + 'describe-dgstorage -d redo'
    cmd6 = host.ODACLI + 'list-dgstorages'
    if host.is_flash():
        cmd = [cmd1, cmd2, cmd3, cmd4, cmd5, cmd6]
    else:
        cmd = [cmd1, cmd2, cmd3, cmd5, cmd6]
    for i in cmd:
        if not host.simple_run (i):
            flag = 0
    return flag

def list_logspaceusage(host):
    flag = 1
    options = ['-c gi', '-c database', '-c dcs', '']
    for i in range(len(options)):
        options[i] = host.ODACLI + "list-logspaceusage " + options[i]
    for i in options:
        if not host.simple_run(i):
            flag = 0
    return flag

def logcleanjob(host):
    flag = 1
    options1 = ["-c gi ", "-c dcs ", "-c database ", ' ', "-c dcs,gi ", "-c database,gi "]
    options2 = ["", "-o 3", "-o 300 -u Minute", "-o 24 -u Hour","-u Hour"]
    for i in options1:
        for j in options2:
            option = i + j
            if not host.create_logcleanjob (option):
                flag = 0
                log.error("Create logcleanjob fail with option %s" % option)
    cmd = host.ODACLI + "list-logcleanjobs"
    if not host.simple_run(cmd):
        flag = 0
    else:
        cmd = host.ODACLI + "list-logcleanjobs|awk 'NR>3 {print $1}'|uniq"
        result = host.ssh2node(cmd).split()
        for i in result:
            cmd = host.ODACLI + "describe-logcleanjob -i %s" % i
            if not host.simple_run(cmd):
                flag = 0
    return flag

def network(host):
    flag = 1
    if host.is_ha_not():
        node_number = 2
    else:
        node_number = 1
    for j in range(node_number):
        cmd = host.ODACLI + "list-networks -u %s" % j
        if not host.simple_run(cmd):
            flag = 0
        else:
            cmd = host.ODACLI + "list-networks -u %s|awk 'NR>3 {print $1}'" % j
            result = host.ssh2node(cmd).split()
            for i in result:
                cmd = host.ODACLI + "describe-network -i %s -u %s" % (i,j)
                if not host.simple_run(cmd):
                    flag = 0
    return flag

def networkinterface(host):
    flag = 1
    if host.is_ha_not ():
        node_number = 2
    else:
        node_number = 1
    for j in range(node_number):
        cmd = host.ODACLI + "list-networkinterfaces -u %s" % j
        if not host.simple_run(cmd):
            flag = 0
        else:
            cmd = host.ODACLI + "list-networkinterfaces -u %s|awk 'NR>3 {print $1}'" % j
            result = host.ssh2node(cmd).split()
            for i in result:
                cmd = host.ODACLI + "describe-networkinterface -i %s -u %s" % (i,j)
                if not host.simple_run(cmd):
                    flag = 0
    return flag

def osconfigurations(host):
    flag = 1
    cmd = host.ODACLI + "list-osconfigurations"
    if not host.simple_run(cmd):
        flag = 0
    else:
        if host.update_osconfigurations():
            cmd =  host.ODACLI + "list-osconfigurations|awk 'NR >3&&$3!=$4 {print $3}'"
            result = host.ssh2node(cmd).split()
            #print result
            if len(result) != 0:
                log.error("The update osconfigurations fail!")

        else:
            log.error("Update the osconfiguratios fail!")


def schedule(host):
    flag = 1
    cmd = host.ODACLI + "list-schedules"
    if not host.simple_run(cmd):
        flag = 0
    else:
        cmd = host.ODACLI + "list-schedules|awk 'NR>3 {print $1}'"
        result = host.ssh2node(cmd).split()
        for i in result:
            cmd = host.ODACLI + "describe-schedule -i %s" % i
            if not host.simple_run(cmd):
                flag = 0
    return flag

def precheckreport(host):
    cmd = "ls -l /opt/oracle/oak/pkgrepos/|wc -l"
    if int(host.ssh2node(cmd)) == 7:
        o_p.unpack_server_zip(host)
    cr_options1 = ['-s','-st', '-s -l', '-s -n 1', '-st -l', '-st -n 1']
    cr_options2 = ['-s', '-st', '-s -l', '-s -n 0', '-st -l', '-st -n 0']
    cmd = host.ODACLI + "list-dbhomes"
    if not host.simple_run(cmd):
        dbhome_option1 = []
        dbhome_option2 = []
        dbhome_option3 = []
    else:
        cmd = host.ODACLI + "list-dbhomes |awk 'NR>3 {print $1}'"
        dbhomeid = host.ssh2node(cmd).split()
        dbhome_option1 = ["-d -i %s " % i for i in dbhomeid]
        dbhome_option2 = ["-d -i %s -l " % i for i in dbhomeid]
        dbhome_option3 = ["-d -i %s -n 1" % i for i in dbhomeid]
    if host.is_ha_not():
        opt = cr_options1 + dbhome_option1 + dbhome_option2 + dbhome_option3
    else:
        opt = cr_options2 + dbhome_option1 + dbhome_option2
    for i in opt:
        if not host.create_prepatchreport(i):
            log.error("Create prepatch report with option %s fail!" % i)
        else:
            describe_prepatchreport(host)


def describe_prepatchreport(host):
    flag = 1
    cmd = host.ODACLI + "list-prepatchreports|tail -n 2|head -n 1|awk '{print $1}'"
    jobid = host.ssh2node(cmd)
    cmd = host.ODACLI + "describe-prepatchreport -i %s" % jobid
    result, error = host.ssh2node_job (cmd)
    if error:
        log.warn (cmd + "\n" + error)
        flag = 0
    else:
        log.info (cmd + "\n" + result)
        if cf.check_error(result):
            flag = 0
            log.error("There is error message in the prepatchreport!")
        else:
            if not host.delete_prepatchreport("-i %s" % jobid):
                flag = 0
    return flag


def describe_system_test(host):
    d = host.describe_system()
    hw_platform = d['SysModel']['hardwarePlatformDisplay']
    cpu_core = d['SysModel']['licensedCoreCount']
    time_zone = d['SysInstance']['timeZone']
    dg_list = d['SysInstance']['grid']['diskGroup']
    check_hw(host, hw_platform)
    check_cpucore(host, cpu_core)
    check_timezone(host, time_zone)
    check_dg(host, dg_list)


def check_dg(host, dg_list):
    if host.is_flash():
        if len(dg_list) != 4:
            log.error("For the system with flash, it should show 4 dg!")
    gi_home = host.gi_home()
    cmd_data = "%s/bin/asmcmd lsdg data|awk 'END{print $8}'" %gi_home
    cmd_reco = "%s/bin/asmcmd lsdg reco|awk 'END{print $8}'" %gi_home
    data_size = host.ssh2node(cmd_data)
    reco_size = host.ssh2node(cmd_reco)
    data_ratio = int(data_size)*100.0/(int(data_size) + int(reco_size))
    reco_ratio = int(reco_size)*100.0/(int(data_size) + int(reco_size))
    log.info(data_ratio)
    log.info(reco_ratio)
    data_ratio = int(round(data_ratio))
    reco_ratio = int(round(reco_ratio))
    #print data_ratio, reco_ratio
    for i in range(len(dg_list)):
        if dg_list[i]["diskGroupName"].upper() in ("FLASH", "REDO"):
            if dg_list[i]["diskPercentage"]!=100:
                log.error("The diskgroup pertentage for %s is %s!" % (dg_list[i]["diskGroupName"], dg_list[i]["diskPercentage"]))
        elif dg_list[i]["diskGroupName"].upper() == 'DATA':
                if dg_list[i]["diskPercentage"]!= data_ratio:
                    log.error("The data pertentage is %s, but show %s!" % (data_ratio, dg_list[i]["diskPercentage"]))
        elif dg_list[i]["diskGroupName"].upper() == 'RECO':
                if dg_list[i]["diskPercentage"]!= reco_ratio:
                    log.error("The reco pertentage is %s, but show %s!" % (reco_ratio, dg_list[i]["diskPercentage"]))

        cmd_red = "%s/bin/asmcmd lsdg %s|awk 'END{print $2}'" %(gi_home,dg_list[i]["diskGroupName"])
        red = host.ssh2node(cmd_red)
        if red.lower() != dg_list[i]["redundancy"].lower():
            log.error("The redundancy of %s is %s, but show %s" % (dg_list[i]["diskGroupName"], red, dg_list[i]["redundancy"]))

def check_timezone(host, time_zone):
    cmd = "grep ZONE /etc/sysconfig/clock|awk -F '\"' '{print $2}'"
    result = host.ssh2node(cmd)
    if result not in time_zone:
        log.error("The timezone displays is %s, but in the system it is %s" %(time_zone, result))


def check_cpucore(host, cpu_core):
    cmd1 = "lscpu|grep Core|awk '{print $4}'"
    cmd2 = "lscpu|grep Socket|awk '{print $2}'"
    core = host.ssh2node(cmd1)
    socket = host.ssh2node(cmd2)
    num2 = int(core) * int(socket)
    if num2 != int(cpu_core):
        log.error("Cpu core displayed is %s, but lscpu shows %s" % (cpu_core, num2))


def check_hw(host, hw_platform):
    if host.is_ha_not():
        if host.is_x3():
            hw = "X3-2-HA"
        elif host.is_x4():
            hw = "X4-2-HA"
        elif host.is_x5():
            hw = "X5-2-HA"
        elif host.is_x6():
            hw = "X6-2-HA"
        elif host.is_x7():
            hw = "X7-2-HA"
        elif host.is_x8():
            hw = "X8-2-HA"
        if hw.lower() != hw_platform.lower():
            log.error("The hw platform should be %s, but it shows %s" % (hw_platform, hw))
    # else:
    #     cmd = "cat /proc/cmdline|grep -i %s" % hw_platform
    #     result = host.ssh2node(cmd)
    #     if not result:
    #         log.error("The hw platform %s is not correct!" % hw_platform)


def initlog(plog):
    oda_lib.initlog(plog)
    global log
    log = plog


def log_management(hostname):
    logname = "Check_odacli_other_%s.log" % hostname
    global logfile
    logfile = os.path.join(cf.log_dir, logname)
    log = initlogging.initLogging("check_odacli_other", logfile, logging.WARN, logging.DEBUG)
    initlog(log)


def sanity_check(host):
    odacli_cmd_check(host)
    describe_component(host)
    check_dgstorage(host)
    list_logspaceusage(host)
    logcleanjob(host)
    schedule(host)
    network(host)
    networkinterface(host)
    osconfigurations(host)
    #precheckreport(host)
    describe_system_test(host)


def main(host):
    log_management(host.hostname)
    sanity_check(host)
    if host.is_ha_not():
        node2 = cf.node2_name(host.hostname)
        host2 = oda_lib.Oda_ha(node2, host.username, host.password)
        sanity_check(host2)


if __name__ == '__main__':
    arg = docopt(__doc__)
    print arg
    hostname = arg['-s']
    username = arg['-u']
    password = arg['-p']
    host = oda_lib.Oda_ha(hostname, username, password)

    main(host)
    print ("Please check the logfile %s for details!" % logfile)
    #osconfigurations(host)