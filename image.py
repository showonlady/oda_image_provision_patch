#!/usr/bin/env python
#coding utf-8
#
# Copyright (c) 2018, Oracle and/or its affiliates. All rights reserved.
#
#    NAME
#      image.py
#
#    DESCRIPTION
#      image all the oda machines
#
#    NOTES
#
#
#    MODIFIED   (MM/DD/YY)
#    chqin    04/07/18 - Creation
#

"""
Usage:
    image.py -h
    image.py  -s <servername> -v <version> [-u <username>] [-p <password>] [--vm]

Options:
    -h,--help       Show this help message
    -s <servername>   hostname of machine
    -v <version>   the version you want to re-image to
    -u <username>   username [default: root]
    -p <password>   password [default: welcome1]
    --vm   image to vm stack
"""


from docopt import docopt
import initlogging
import oda_lib
import simplejson
import sys,os
import common_fun as cf
import datetime
import time
import re
import logging
import pexpect

ver_his = ['12.1.2.8','12.1.2.8.1','12.1.2.9','12.1.2.10','12.1.2.11', '12.1.2.12', '12.2.1.1','12.2.1.2',
           '12.2.1.3', '12.2.1.4','18.1', '18.2.1']
vm_ver_node_num = ["18.3", "18.4","18.5","18.7","18.8"]
ver_19 = ["19.4", "19.5"]
log_dir = cf.log_dir
script_dir = cf.scr_dir + "/"
#script_dir = "/chqin/oda_test/venv/src/"
oakpassword = "welcome1"
# f = open("/chqin/new_test/venv/machine.json", "r")
# host_d = simplejson.load(f)
host_d = cf.host_notv2v3
#ilomAdmUsr = "root"
ilomAdmUsr = "imageuser"
ilomAdmPwd = "welcome1"
ilomTimeout = 10;
factoryIlomPwd = "changeme"
sshport = '22'
nfsip = "10.214.80.5"
ilomUsrPwd = "welcome1"
copper = ["rwsoda601c1n1", "rwsoda602c1n1"]




def rwsoda315_iso(iso):
    a = re.sub('chqin', 'scratch/chqinnew', iso, 1)
    return a

def cleanup(hostname, username, password):
    if host_reachable(hostname):
        log.info("The host %s is reachable, will perform the cleanup!" % hostname)
    elif "vlan" in host_d[hostname].keys():
        log.info("Found vlan infomation for host %s" % hostname)
        hostname = host_d[hostname]["vlan"]["vlanip"][0]
        if host_reachable(hostname):
            log.info("The host %s is reachable, will perform the cleanup!" % hostname)
        else:
            log.warn("The host %s is not reachable, could not run the cleanup!" % hostname)
            return 0
    else:
        log.warn("The host %s is not reachable, could not run the cleanup!" % hostname)
        return 0

    host = oda_lib.Oda_ha(hostname, username, password)
    if not host.is_dcs_or_oak():
        cmd = "perl /opt/oracle/oak/onecmd/cleanupDeploy.pl"
        logfile = cf.cleanup_deployment(host,cmd)
        log.info ("Cleanup is done, please check the logfile %s for details!" % logfile)

        #result = oak_cleanup(host, cmd)
        #return result
    else:
        if host.is_deployed_or_not():
            cmd = "perl /opt/oracle/oak/onecmd/cleanup.pl -griduser %s -dbuser %s" % (host.griduser(), host.racuser())
        else:
            cmd = "perl /opt/oracle/oak/onecmd/cleanup.pl"

        if host.is_ha_not():
            node2name = cf.node2_name(hostname)
            host2 = oda_lib.Oda_ha(node2name, username, password)
            # result = oak_cleanup(host, cmd)
            # log.info(result)
            logfile = cf.cleanup_deployment (host, cmd)
            log.info ("Cleanup on the 1st node is done, please check the logfile %s for details!" % logfile)
            log.info("Wait two minutes, and it will run cleanup on the 2nd node!")
            time.sleep(120)
            logfile = cf.cleanup_deployment (host2, cmd)
            log.info ("Cleanup on the 2nd node is done, please check the logfile %s for details!" % logfile)
        else:
            logfile = cf.cleanup_deployment (host, cmd)
            log.info ("Cleanup is done, please check the logfile %s for details!" % logfile)

            # result2 = oak_cleanup(host2, cmd)
            # log.info(result2)


def reset_sp(ilom, imagelog):
    time.sleep(60)
    cmd2 = script_dir + "resetSP.sh %s %s %s %s %s" % (ilomAdmUsr, ilom, ilomAdmPwd, imagelog, ilomTimeout)
    log.info(cmd2)
    out, error = cf.exc_cmd_new(cmd2)
    if error:
        log.error("ILOM %s reset failed, can't proceed reimage process" % ilom)
        sys.exit(0)


def reset_sp_scaoda8032(ilom, imagelog):
    time.sleep(60)
    cmd2 = script_dir + "resetSP_scaoda8032.sh %s %s %s %s %s" % (ilomAdmUsr, ilom, ilomAdmPwd, imagelog, ilomTimeout)
    log.info(cmd2)
    out, error = cf.exc_cmd_new(cmd2)
    if error:
        log.error("ILOM %s reset failed, can't proceed reimage process" % ilom)
        sys.exit(0)


def reset_ilom_password(ilom, imagelog):
    cmd = script_dir + "changeFactoryPwd.sh %s %s %s %s %s %s" % (
    ilomAdmUsr, ilom, factoryIlomPwd, ilomAdmPwd, imagelog, ilomTimeout)
    log.info(cmd)
    out, error = cf.exc_cmd_new(cmd)
    if error:
        log.error("Ilom %s reset of factory password failed, can't proceed reimage process!" % ilom)
        sys.exit(0)
    time.sleep(60)
    cmd2 = script_dir + "resetSP.sh %s %s %s %s %s" % (ilomAdmUsr, ilom, ilomAdmPwd, imagelog, ilomTimeout)
    log.info(cmd2)
    out, error = cf.exc_cmd_new(cmd2)
    if error:
        log.error("ILOM %s reset failed, can't proceed reimage process" % ilom)
        sys.exit(0)

def setiso(ilom, iso, imagelog):
    cmd = script_dir + "setISO.sh %s %s %s %s %s %s %s" % (ilomAdmUsr, ilom, ilomAdmPwd, iso, nfsip, imagelog, ilomTimeout)
    out, err = cf.exc_cmd_new(cmd)
    if err:
        log.info(out)
        log.error("ILOM %s setting up iso failed, can't proceed reimage process" % ilom)
        sys.exit(0)

def vm_reset_ilom(ilom, imagelog):
    cmd = script_dir + "vm_reset_ilom.sh %s %s %s %s %s" % (ilomAdmUsr, ilom, ilomAdmPwd, imagelog, ilomTimeout)
    out, err = cf.exc_cmd_new(cmd)
    if err:
        log.info(out)
        log.error("Vm ILOM %s reset speed failed!" % ilom)
        sys.exit(0)


def bootup(ilom, version, imagelog):
    cmd = script_dir + "checkOakFirstBoot.sh %s %s %s %s %s %s %s" %(ilomAdmUsr, ilom, ilomAdmPwd, ilomUsrPwd, version, imagelog, ilomTimeout)
    status = False
    log.info(cmd)
    for i in range(10):
        out, err = cf.exc_cmd_new(cmd)
        if err == 3:
            log.info("Firstboot file found on host %s!" % ilom)
            status = True
            return status
        else:
            time.sleep(300)
    return status

def set_node_number(ilom, imagelog):
    for i in range(2):
        nodenum = i
        cmd = script_dir + "setNodeNumAndIPTwoJbodSystem.sh %s %s %s %s %s %s %s" %(ilomAdmUsr, ilom[i], ilomAdmPwd, ilomUsrPwd, nodenum, imagelog, ilomTimeout)
        out, err = cf.exc_cmd_new(cmd)
        if err:
            log.info(out)
            log.error("Set the node number on ilom %s failed" % ilom[i])
            sys.exit(0)

def set_node_number_new(ilom, imagelog):
    for i in range(len(ilom)):
        nodenum = i
        cmd = script_dir + "setNodeNumAndIPTwoJbodSystem_new.sh %s %s %s %s %s %s %s" %(ilomAdmUsr, ilom[i], ilomAdmPwd, ilomUsrPwd, nodenum, imagelog, ilomTimeout)
        out, err = cf.exc_cmd_new(cmd)
        if err:
            log.info(out)
            log.error("Set the node number on ilom %s failed" % ilom[i])
            sys.exit(0)

def configure_network_copper(ilom, imagelog, dcsflag):
    for i in ilom:
        cmd = script_dir + "configure_network_copper.sh %s %s %s %s %s %s %s" %(ilomAdmUsr, i, ilomAdmPwd, ilomUsrPwd, imagelog, ilomTimeout, dcsflag)
        out, err = cf.exc_cmd_new(cmd)
        if err:
            log.info(out)
            log.error("oakcli configure network -publicNet copper failed on %s" % i)
            sys.exit(0)
        else:
            time.sleep(120)

def check_all_host_reachable(ilom):
    for i in ilom:
        if not host_reachable(i):
            log.error("The host %s was not reachable, fail!" % i)
            sys.exit(0)
        else:
            log.info("The host %s was reachable." % i)

def check_all_host_port_reachable(ilom):
    for i in ilom:
        if not host_reachable(i):
            log.error("The ilom %s was not reachable after reset sp,can't proceed reimage process, fail!" % i)
            sys.exit(0)
        if not port_reachable(i):
            log.warn("The ssh port on node %s not reachable" % i)


def copper_dcsflag(version, vmflag):
    if vmflag:
        return 0
    version = cf.trim_version(version)
    versions = ['12.1.2.8','12.1.2.8.1','12.1.2.9','12.1.2.10','12.1.2.11', '12.1.2.12', '12.2.1.1','12.2.1.2']
    versions2 = ["12.2.1.3", "12.2.1.4"]
    if version in versions + versions2:
        dcsflag = 0
    else:
        dcsflag = 1
    return dcsflag



def image(hostname, version, vmflag):
    log_stamp = datetime.datetime.today().strftime("%Y%m%d")
    imagelog = log_dir + "/image_%s_%s.log" % (hostname, log_stamp)
    ilom = host_d[hostname]["ilom"]
    log.info("Check all the ilom are reachable")
    check_all_host_reachable(ilom)

    ###reset ilom password and reset host ilom
    for i in ilom:
        ######Could not use root to do image, so no need to change root password.
        #reset_ilom_password(i, imagelog)
        if i != "scaoda8032-c":
            reset_sp(i, imagelog)
        else:
            reset_sp_scaoda8032(i, imagelog)

    ###check for ilom reachability post reset sp
    check_all_host_port_reachable(ilom)

    ####set iso
    time.sleep(360)
    iso = generate_iso(hostname, version, vmflag)
    log.info("The iso to be installed is %s" % iso)
    for i in ilom:
        setiso(i, iso, imagelog)

    ######Wait for about half an hour
    time.sleep(1800)
    ####If the host is vm, we need to reset the pending speed to 9600
    if vmflag:
        for i in ilom:
            vm_reset_ilom(i, imagelog)

    ###Check if the host is boot up
    for i in ilom:
        status = bootup(i, version,imagelog)
        if not status:
            log.error("Could not find the first boot file on host %s" % i)
            sys.exit(0)

    ######If the system is two jbod system, we need to set the node num
    ####This is for the w/a of 18.3 vm, all need to input the node number

    if host_d[hostname]["jbod"] == 2 and cf.trim_version(version) not in ver_19:
        set_node_number(ilom, imagelog)
        ##Wait the host to boot up
        time.sleep(360)
    elif host_d[hostname]["jbod"] == 2 and cf.trim_version(version) in ver_19:
        set_node_number_new(ilom,imagelog)
        time.sleep(120)
    elif vmflag and cf.trim_version(version)in vm_ver_node_num:
        set_node_number (ilom, imagelog)
        time.sleep (360)
    else:
        pass

    ####For rwsoda601c1n1, we need to run "oakcli configure network -publicNet copper"
    if hostname in copper :
        dcsflag = copper_dcsflag(version, vmflag)
        configure_network_copper(ilom, imagelog, dcsflag)
        ##Wait the host to boot up
        time.sleep(300)
    print "Finish image process!"
    cf.covertlog(imagelog)




def generate_iso(hostname, version, vmflag):
    iso1 = getiso(hostname, version, vmflag)
    if not iso1:
        sys.exit(0)
    iso = rwsoda315_iso(iso1)
    return iso


def getiso(hostname, version, vmflag):
    flag = 0
    ver = cf.trim_version(version)
    loc = "/chqin/ODA%s/" % ver
    if ver in ver_his:
        oliteIso1 = "singlenode_*iso"
        oliteIso2 = "oda*-os-image*iso"
        odaIso1 = "multinode_*iso"
        odaIso2 = "OAKFactoryImage*iso"
    else:
        oliteIso1 = " oda_bm_*iso"
        oliteIso2 = "oda_bm_*iso"
        odaIso1 = "oda_bm_*iso"
        odaIso2 = "oda_bm_*iso"

    vmiso = "OakOvm_*.iso"

    if vmflag:
        cmd = 'ls %s' %(loc + vmiso)
        out, err = cf.exc_cmd_new(cmd)
        if err:
            log.error("Could not find the iso: %s" % (loc + vmiso))
            return flag
        else:
            log.info(out)
            return out.strip()

    if len(host_d[hostname]["ilom"]) == 2:
        cmd = 'ls %s' %(loc + odaIso1)
        out, err = cf.exc_cmd_new(cmd)
        if err:
            cmd1 = 'ls %s' %(loc + odaIso2)
            out, err = cf.exc_cmd_new(cmd1)
            if err:
                log.error("Could not find the iso: %s" % (loc + odaIso2))
                return flag
            else:
                log.info(out)
                return out.strip()
        else:
            log.info(out)
            return out.strip()

    if len(host_d[hostname]["ilom"]) == 1:
        cmd = 'ls %s' %(loc + oliteIso1)
        out, err = cf.exc_cmd_new(cmd)
        if err:
            cmd1 = 'ls %s' %(loc + oliteIso2)
            out, err = cf.exc_cmd_new(cmd1)
            if err:
                log.error("Could not find the iso: %s" % (loc + oliteIso2))
                return flag
            else:
                log.info(out)
                return out.strip()
        else:
            log.info(out)
            return out.strip()



def port_reachable(hostname, sshport = sshport):
    result = 0
    cmd = "nc -vz %s %s" %(hostname, sshport)
    for i in range(5):
        out, err = cf.exc_cmd_new(cmd)
        if not err:
            result = 1
            log.info("Ilom %s port %s reachable" %(hostname, sshport))
            return result
        else:
            time.sleep(60)
    return result

def host_reachable(hostname):
    result = 0
    cmd = "ping -c 3 %s | grep '3 received' | wc -l" % hostname
    for i in range(5):
        out,err = cf.exc_cmd_new(cmd)
        if err:
            log.error(err)
            return result
        else:
            if int(out):
                result = 1
                return result
            else:
                time.sleep(60)
    return result












def oak_cleanup(host, cmd):
    log.info(cmd)
    stdin, stdout, stderr = host.ssh.exec_command(cmd)
    if not host.is_dcs_or_oak():
        log.info("This is oak stack, need to input password!")
        stdin.write("%s\n" % oakpassword)
        stdin.write("%s\n" % oakpassword)
    stdin.write("%s\n" % 'yes')
    stdin.write("%s\n" % 'yes')
    result = stdout.read().strip()
    errormsg = stderr.read().strip()
    return result + errormsg

def oak_cleanup_bk(host, cmd):
    log.info(cmd)



def is_node_support(hostname):
    if hostname in host_d.keys():
        return 1
    else:
        print "This node is not supported, exit!"
        sys.exit(0)
    

def initlogger(hostname):
    logname = "image_%s.log" % hostname
    logfile = os.path.join(cf.log_dir, logname)
    log = initlogging.initLogging("image", logfile, logging.WARN, logging.DEBUG)
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
    version = arg['-v']
    password = arg['-p']
    username = arg['-u']
    vm = arg["--vm"]
    is_node_support(hostname)
    log_management(hostname)
    cleanup(hostname, username, password)
    time.sleep(300)
    image(hostname, version, vm)
