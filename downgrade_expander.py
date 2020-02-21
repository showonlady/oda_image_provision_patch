#!/usr/bin/env python
# -*- coding:UTF-8 -*-
#
# Copyright (c) 2018, Oracle and/or its affiliates. All rights reserved.
#
#    NAME
#      downgrade_expander.py
#
#    DESCRIPTION
#      downgrade the version of expander
#
#    NOTES
#
#
#    MODIFIED   (MM/DD/YY)
#    weiwei    11/13/18 - Creation
#
"""
Usage:
 downgrade_expander.py -s <hostname> [-u <username>] [-p <password>] 

Options:
  -h, --help  Show this screen
  -s <hostname>  hostname,if vlan,use ip instead
  -u <username>  username [default: root]
  -p <password>  password [default: welcome1]
"""

from docopt import docopt
import datetime
import os,logging
import common_fun as cf
import initlogging
import oda_lib

expander_dir = "/home/chqin/qcl/BIOS-ILOM-CPLD-FW/Expander/18.3"
remote_dir = "/tmp"


def downgrade_expander(host):

    if host.is_ha_not():
        if host.is_x7():
            expander = "DE3_FW_0304_FPGA_25.bin"
        elif host.is_x6():
            expander = "TW2200S_MCT_EXP_0291_FPGA_25_CPLD_10_IMG.bin"
        else:
            expander = " "
            logger.error("There is no version.")
    else:
        logger.error("Not support.")

    remote_file = scp_fw(host, expander)
    if not expander == " ":
        cmd1 = "/usr/sbin/fwupdate list expander|grep ^c[0-9]x[0-9]|awk '{print $1}'"
        result1 = run_cmd(cmd1)
        if result1:
            expander_name = result1.split()
            for i in expander_name:
                cmd2 = "/usr/sbin/fwupdate list expander|grep %s|awk '{print $7}'" % i
                fw_version = str(run_cmd(cmd2))
                if fw_version in expander:
                    print i + " is the old firmware, no need to downgrade!"
                else:
                    cmd3 = "/usr/sbin/fwupdate update expander-firmware -n %s -f %s --silent-no-reboot --force -q -o " \
                           "/tmp/%s.xml" % (i, remote_file, i)
                    run_cmd(cmd3)
                    fw_version = str(run_cmd(cmd2))
                    if fw_version in expander:
                        print i + " downgrade successful!"
                    else:
                        print i + " downgrade fail!"


def scp_fw(host, expander):
    result = cf.exc_cmd("ls %s" % expander_dir)
    for i in result.split():
        if expander in i:
            file = i
            print file
            break
    if not file:
        return 0

    fw_file = os.path.join(expander_dir, file)
    remote_file = os.path.join(remote_dir, file)
    host.scp2node(fw_file, remote_file)
    return remote_file


def run_cmd(cmd):
    logger.info(cmd)
    result, error = host.ssh2node_job(cmd)
    if error:
       logger.error(error)
       return 0
    else:
       logger.info('\n'+result)
       return result


def log_management(hostname):
    global logfile
    logname = "downgrade_expander_%s_%s.log" %(hostname, datetime.datetime.now().strftime('%Y-%m-%d'))
    logfile = os.path.join(cf.log_dir, logname)
    log = initlogging.initLogging("downgrade_expander", logfile, logging.WARN, logging.DEBUG)
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
    downgrade_expander(host)

