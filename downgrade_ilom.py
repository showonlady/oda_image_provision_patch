#!/usr/bin/env python
# -*- coding:UTF-8 -*-
#
# Copyright (c) 2018, Oracle and/or its affiliates. All rights reserved.
#
#    NAME
#      downgrade_ilom.py
#
#    DESCRIPTION
#      downgrade the version of ilom
#
#    NOTES
#
#
#    MODIFIED   (MM/DD/YY)
#    weiwei    10/23/18 - Creation
#
"""
Usage:
 downgrade_ilom.py -s <hostname> [-u <username>] [-p <password>] 

Options:
  -h, --help  Show this screen
  -s <hostname>  hostname,if vlan,please use vlan ip
  -u <username>  username [default: root]
  -p <password>  password [default: welcome1]
"""

from docopt import docopt
import datetime
import os,logging
import common_fun as cf
import initlogging
import oda_lib
import time
import subprocess
import json

ilom_dir = "/home/chqin/qcl/BIOS-ILOM-CPLD-FW/ILOM/weiwei"


def downgrade_ilom(host):
    # with open("allmachine.json", 'r') as load_f:
    #     load_dict = json.load(load_f)
    load_dict = cf.host_all

    try:
        if host.hostname in load_dict.keys():
            ilom_hostname = load_dict[host.hostname]['ilom']
        else:
            for key in load_dict:
                try:
                    if host.hostname == load_dict[key]['vlan']['vlanip'][0]:
                        ilom_hostname = load_dict[key]['ilom']
                        break
                except KeyError:
                    pass
    except:
        logger.error("The machine is not exist.")

    if host.is_x7():
        ilom = "ILOM-4_0_0_22_r120818-ORACLE_SERVER_X7-2-rom.pkg"
    elif host.is_x6():
        ilom = "ILOM-3_2_7_26_a_r112632-Oracle_Server_X6-2.pkg"
    elif host.is_x5():
        ilom = "ILOM-3_2_4_52_r101649-Oracle_Server_X5-2.pkg"
    elif host.is_x4():
        ilom = "ILOM-3_1_2_30_c_r88185-Sun_Server_X4-2.pkg"
    elif host.is_x3():
        ilom = "ILOM-3_1_2_42_r88414-Sun_Fire_4170_M3.pkg"
    elif host.is_x8 ():
        ilom = "ILOM-4_0_4_38_r130206-ORACLE_SERVER_X8-2L.pkg"
    else:
        ilom = " "
        logger.error("There is no version.")

    os.chdir(ilom_dir)
    if not ilom == " ":
        for item in ilom_hostname:
            print item
            cmd1 = "/usr/sbin/ipmitool -I lanplus -U imageuser -P welcome1 -H %s chassis power off" % item
            cmd2 = "/usr/sbin/ipmiflash -I lanplus -U imageuser -P welcome1 -H %s write %s" %(item, ilom)
            cmd3 = "/usr/sbin/ipmitool -I lanplus -U imageuser -P welcome1 -H %s chassis power on" % item
            print cmd1
            subprocess.call(cmd1, shell=True)
            print cmd2
            subprocess.call(cmd2, shell=True)
            time.sleep(300)
            print cmd3
            subprocess.call(cmd3, shell=True)


def get_key(dict, value):
    return [k for k, v in dict.items() if v == value]


def log_management(hostname):
    global logfile
    logname = "downgrade_ilom_%s_%s.log" %(hostname, datetime.datetime.now().strftime('%Y-%m-%d'))
    logfile = os.path.join(cf.log_dir, logname)
    log = initlogging.initLogging("downgrade_ilom", logfile, logging.WARN, logging.DEBUG)
    initlog(log)


def initlog(plog):
    oda_lib.initlog(plog)
    global logger
    logger = plog

if __name__ == '__main__':
    arg = docopt(__doc__)
    print arg
    hostname = arg['-s']
    username = arg['-u']
    password = arg['-p']
    log_management(hostname)
    host = oda_lib.Oda_ha(hostname, username, password)
    downgrade_ilom(host)


