#! /usr/bin/env python
# coding utf-8

"""
Usage:
    downgrade_disk.py -h
    downgrade_disk.py  -s <servername> [-u <username>] [-p <password>] [-d <diskversion>] [-n <devicenum>]


Options:
    -h,--help       Show this help message

    -s <servername>  hostname of machine, if vlan,use ip instead
    -u <username>  username [default: root]
    -p <password>  password [default: welcome1]
    -d <diskversion>   The diskversion
    -n <devicenum>  The device number
"""

from docopt import docopt
import oda_lib
import common_fun as cf
import initlogging
import logging
import time
import os, sys



disk_version = {
    "H109090SESUN900G": ["A7E0", "A720"],
    "H7240AS60SUN4.0T": ["A3A0", "A2D2"],
    "HBCAC2DH2SUN3.2T": ["A122", "A087"],
    "HBCAC2DH4SUN800G": ["A122", "A087"],
    "H7210A520SUN010T": ["A38K","A374"]
    }

nvme_version = {
    "ICDPC2DD2ORA6.4T":["RE14", "RE0F"],
    "MS1PC2DD3ORA3.2T":["IR3Q", "GR3Q"]
}


fw_dir = "/home/chqin/qcl/BIOS-ILOM-CPLD-FW/Disks/18.3"
remote_dir = "/tmp"
fwupdate = "/usr/sbin/fwupdate"

def downgrade_disk(host):
    if host.is_ha_not():
        for i in disk_version.keys():
            log.info(disk_version[i][0])
            cmd = "%s list disk|egrep -i '^c1.*%s.*%s'|awk '{print $1}'"% (fwupdate, i, disk_version[i][0])
            log.info(cmd)
            disk = host.ssh2node(cmd).split()
            log.info(disk)
            if disk:
                log.info ("Will downgrade the disk to %s" % disk_version[i][1])
                remote_file = scp_fw(host, disk_version[i][1])
                for j in disk:
                    cmd = "%s update disk-firmware -n %s -f %s -q" % (fwupdate, j, remote_file)
                    log.info(cmd)
                    host.ssh2node(cmd)
                log.info("Finished the downgrade disk!")
                log.info("Will check the disk version.")
                for j in disk:
                    cmd = "%s list disk -n %s|tail -n 1|awk '{print $9}'" %(fwupdate, j)
                    if host.ssh2node(cmd) == disk_version[i][1]:
                        log.info("The device %s is correctly downgraded!" % j)
                    else:
                        log.warn("The device %s is not downgraded" % j)
    else:
        for i in nvme_version.keys():
            cmd = "%s list controller|egrep -i '%s.*%s'|awk '{print $1}'"% (fwupdate, i, nvme_version[i][0])
            log.info(cmd)
            disk = host.ssh2node(cmd).split()
            log.info(disk)
            if disk:
                log.info ("Will downgrade the disk to %s" % nvme_version[i][1])
                remote_file = scp_fw(host, nvme_version[i][1])
                for j in disk:
                    cmd = "%s update nvme-controller-firmware -n %s -f %s -q" % (fwupdate, j, remote_file)
                    log.info(cmd)
                    host.ssh2node(cmd)
                log.info("Finished the downgrade disk!")
                log.info("Will reboot the host to take effect the downgrade.")
                reboot (host)
                host = oda_lib.Oda_ha(host.hostname, host.username, host.password)
                log.info("Will check the disk version.")
                for j in disk:
                    cmd = "%s list controller -n %s|tail -n 1|awk '{print $6}'" %(fwupdate, j)
                    if host.ssh2node(cmd) == nvme_version[i][1]:
                        log.info("The device %s is correctly downgraded!" % j)
                    else:
                        log.warn("The device %s is not downgraded" % j)



def downgrade_disk_cmd(host,fw):
    remote_file = scp_fw(host, fw)
    if host.is_ha_not():
        cmd = "for i in {%s};do /usr/sbin/fwupdate update disk-firmware -n c1d${i} -f %s -q;done" % (device_num, remote_file)
    else:
        cmd = "for i in {%s};do /usr/sbin/fwupdate update nvme-controller-firmware -n c${i} -f %s -q;done" % (device_num, remote_file)
    host.ssh2node(cmd)


def determin_fw(host):
    if host.is_ha_not():
        if host.is_x7():
            if host.is_hdd_or_ssd():
                fw = "A374"
            else:
                fw = "A087"
        elif host.is_x5():
            fw = "A2D2"
        elif host.is_x4() or host.is_x3():
            fw = "A720"
        else:
            print "Could not find the firmware for the host!"
            sys.exit(0)
    else:
        if host.is_x6():
            fw = "GR3Q"
        elif host.is_x7():
            fw = "RE0F"
    return fw

def check_fw(host, fw):
    flag = 1
    if host.is_ha_not():
        cmd = "for i in {%s};do %s list disk -n c1d${i}|tail -n 1|awk '{print $9}';done" % (device_num, fwupate)
        result = host.ssh2node(cmd).split()
        for i in result:
            if fw.lower() not in i.lower():
                log.warning("The installed version is %s, not %s" % (i, fw))
                flag = 0
    else:
        cmd = "for i in {%s};do %s list controller -n c${i}|tail -n 1|awk '{print $6}'" % (device_num, fwupate)
        result = host.ssh2node(cmd)
        for i in result:
            if fw.lower () not in i.lower ():
                flag = 0
                log.warning ("The installed version is %s, not %s!" %(i, fw))
    return flag

def reboot(host):
    cmd = "reboot"
    host.ssh2node(cmd)
    time.sleep(300)
    cf.wait_until_ping(host.hostname, 60)

def scp_fw(host, fw):
    result = cf.exc_cmd("ls %s" % fw_dir)
    for i in result.split():
        if fw.lower() in i.lower():
            file = i
            print file
            break
    fw_file = os.path.join(fw_dir, file)
    remote_file = os.path.join(remote_dir, file)
    host.scp2node(fw_file, remote_file)
    return remote_file


def initlog(plog):
    oda_lib.initlog(plog)
    global log
    log = plog


def log_management(hostname):
    global logfile
    logname = "downgrade_disk_%s.log" % hostname
    logfile = os.path.join (cf.log_dir, logname)
    log = initlogging.initLogging ("downgrade_disk", logfile, logging.WARN, logging.DEBUG)
    initlog(log)


def main(host, fw):
    downgrade_disk_cmd(host, fw)
    #reboot(host)
    #host = oda_lib.Oda_ha(host.hostname, host.username, host.password)
    check_fw(host, fw)

def fun_in_image(host):
    fw = determin_fw (host)
    main(host,fw)

if __name__ == '__main__':
    arg = docopt(__doc__)
    print arg
    hostname = arg['-s']
    username = arg['-u']
    password = arg['-p']
    global device_num
    if arg["-n"]:
        device_num = arg["-n"]
    else:
        device_num = "0..5"
    log_management (hostname)
    host = oda_lib.Oda_ha (hostname, username, password)
    # if arg['-d']:
    #     fw = arg['-d']
    # else:
    #     fw = determin_fw(host)

    #main(host,fw)
    downgrade_disk(host)