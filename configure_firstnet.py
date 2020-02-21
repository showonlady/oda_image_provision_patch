#!/usr/bin/env python
#coding utf-8
#
# Copyright (c) 2018, Oracle and/or its affiliates. All rights reserved.
#
#    NAME
#      configure_firstnet.py
#
#    DESCRIPTION
#      Configure firstnet on all environments
#
#    NOTES
#
#
#    MODIFIED   (MM/DD/YY)
#    chqin    04/07/18 - Creation
#


"""
Usage:
    configure_firstnet.py -h
    configure_firstnet.py  -s <servername> -v <version> [--vm]
    configure_firstnet.py  -s <servername> -v <version> [--vm] [--network <vlan>]


Options:
    -h,--help       Show this help message
    -s <servername>   hostname of machine
    -v <version>   the version you re-image to
    --vm   image to vm stack
    --network <vlan>  network type, vlan, bonding, nonbonding

"""


from docopt import docopt

import oda_lib
import simplejson
import sys
import common_fun as cf
import datetime
import time
import re,os
import image
import datetime
import random
import socket
import logging
import initlogging
import simplejson

log_dir = cf.log_dir
script_dir = image.script_dir
#X7_machine = ["scaoda704c1n1", "scaoda7s005"]
netconfig = ['bonding', 'nonbonding', 'vlan']
netconfig_x6 = [ "bonding", 'vlan']
ilomTimeout = image.ilomTimeout
ilomAdmUsr = image.ilomAdmUsr
ilomAdmPwd = image.ilomAdmPwd
ilomTimeout = image.ilomTimeout;
sshport = image.sshport
nfsip = image.nfsip
ilomUsrPwd = image.ilomUsrPwd
domain_name = "us.oracle.com"
dnsserver = "10.209.76.197"
dnsserver_cn = "10.188.235.198"

# with open("/chqin/new_test/venv/allmachine.json", "r") as f:
#     host_d = simplejson.load(f)
host_d = cf.host_all

def is_x7_or_not(hostname):
    if re.match("scaoda7", hostname):
        return 1
    else:
        return 0

def is_x6_or_not(hostname):
    if re.match("rwsoda6", hostname):
        return 1
    else:
        return 0

def is_x5_or_not(hostname):
    if re.search("oda4", hostname):
        return 1
    else:
        return 0

def is_x8_or_not(hostname):
    if re.match("scaoda8", hostname):
        return 1
    else:
        return 0

def is_x6_lite_or_not(hostname):
    if re.match("rwsoda6", hostname):
        nodename = host_d[hostname]["nodename"]
        if len(nodename) == 1:
            return 1
        else:
            return 0
    else:
        return 0

def x6_network(lite_flag, version):
    version = cf.trim_version(version)
    versions = ['12.1.2.8','12.1.2.8.1','12.1.2.9','12.1.2.10','12.1.2.11', '12.1.2.12', '12.2.1.1','12.2.1.2']
    versions2 = ["12.2.1.3", "12.2.1.4"]
    if lite_flag:
        if version in versions:
            network = ['bonding']
        else:
            network = netconfig_x6
    else:
        if version in versions + versions2:
            network = ['bonding']
        else:
            network = netconfig_x6
    return network


def x5_network(version):
    version = cf.trim_version(version)
    versions = ['12.1.2.8','12.1.2.8.1','12.1.2.9','12.1.2.10','12.1.2.11', '12.1.2.12', '12.2.1.1','12.2.1.2']
    versions2 = ["12.2.1.3", "12.2.1.4", "18.2.1"]
    if version in versions + versions2:
        network = ['bonding']
    else:
        network = netconfig_x6
    return network



def x7_network(version):
    if re.match("12.2.1.1|18.1", version):
        network = ['bonding']
    elif re.match('12.2.1.2', version):
        network = ['bonding', 'vlan']
    else:
        network = netconfig
    return network

####Need to modify in 18.3
def is_dcs(hostname, version, vmflag = False):
    version = cf.trim_version(version)
    dcs = 1
    if vmflag:
        dcs = 0
        return dcs
    ilom = host_d[hostname]["ilom"]
    versions = ["12.1.2.8", "12.1.2.8.1", "12.1.2.9", "12.1.2.10", "12.1.2.11", "12.1.2.12", "12.2.1.1", "12.2.1.2", "12.2.1.3", "12.2.1.4"]
    is_x7 = is_x7_or_not(hostname)
    if len(ilom) == 2 and (not is_x7) and (version in versions):
        dcs = 0
    return dcs

def configure_firstnet_bond(hostname, imagelog, dcsflag):
    ilom = host_d[hostname]["ilom"]
    nodename = host_d[hostname]["nodename"]
    netmask = host_d[hostname]["netmask"]
    for i in range(len(ilom)):
        hostIp = socket.gethostbyname(nodename[i])
        cmd = script_dir + "setPublicIP.sh %s %s %s %s %s %s %s %s %s" %(ilomAdmUsr, ilom[i], ilomAdmPwd, ilomUsrPwd, hostIp, netmask, dcsflag, imagelog, ilomTimeout)
        log.info(cmd)
        out, err = cf.exc_cmd_new(cmd)
        if err:
            log.info(out)
            log.error("Set up the bonding public ip on ilom %s failed" % ilom[i])
            sys.exit(0)
    return nodename


def configure_firstnet_nonbonding(hostname, imagelog):
    ilom = host_d[hostname]["ilom"]
    nodename = host_d[hostname]["nodename"]
    netmask = host_d[hostname]["netmask"]
    for i in range(len(ilom)):
        hostIp = socket.gethostbyname(nodename[i])
        cmd = script_dir + "set_nonbonding_ip.sh %s %s %s %s %s %s %s %s" %(ilomAdmUsr, ilom[i], ilomAdmPwd, ilomUsrPwd, hostIp, netmask, imagelog, ilomTimeout)
        log.info(cmd)
        out, err = cf.exc_cmd_new(cmd)
        if err:
            log.info(out)
            log.error("Set up the bonding public ip on ilom %s failed" % ilom[i])
            sys.exit(0)
    return nodename


def configure_firstnet_vm(hostname, imagelog):
    ilom = host_d[hostname]["ilom"]
    if len(ilom) != 2:
        sys.exit(0)
        
    if re.search('com', hostname):
        oak1_dom0, oak2_dom0 = cf.dom0_name(hostname)
        hostip1 = socket.gethostbyname(oak1_dom0)
        hostip2 = socket.gethostbyname(oak2_dom0)
        node1_dom0 = oak1_dom0.split('.')[0]
        node2_dom0 = oak2_dom0.split('.')[0]
        domain_name1 = '.'.join(hostname.split(".")[1:])
        dnsserver1 = dnsserver_cn
    else:
        # node1_dom0 = hostname[:-4] + "1"
        # node2_dom0 = hostname[:-4] + "2"
        node1_dom0, node2_dom0 = cf.dom0_name(hostname)
        oak1_dom0,oak2_dom0 = node1_dom0, node2_dom0
        hostip1 = socket.gethostbyname(node1_dom0)
        hostip2 = socket.gethostbyname(node2_dom0)
        domain_name1 = domain_name
        dnsserver1 = dnsserver
    netmask = host_d[hostname]["netmask"]
    cmd = script_dir + "setdom0IP.sh %s %s %s %s %s %s %s %s %s %s %s %s" %(ilomAdmUsr, ilom[0], ilomAdmPwd, ilomUsrPwd,
                        domain_name1, dnsserver1,node1_dom0, node2_dom0, hostip1, hostip2, netmask, imagelog)
    out, err = cf.exc_cmd_new(cmd)
    if err:
        log.info(out)
        log.error("Set up the bonding public ip on ilom %s failed" % ilom[0])
        sys.exit(0)
    else:
        return [oak1_dom0, oak2_dom0]

def configure_firstnet_vlan(hostname, imagelog):
    if "vlan" not in host_d[hostname].keys():
        log.warn("No vlan infomation for host %s" % hostname)
        sys.exit(0)
    ilom = host_d[hostname]["ilom"]
    vlanid = host_d[hostname]["vlan"]["vlanid"]
    vlanIp = host_d[hostname]["vlan"]["vlanip"]
    vlannetmask = host_d[hostname]["vlan"]["vlannetmask"]
    if len(vlanIp) != len(ilom):
        log.warn("The number of vlanip is not consistent with ilom ip!")
        sys.exit(0)
    for i in range(len(ilom)):
        cmd = script_dir + "set_vlan_ip.sh %s %s %s %s %s %s %s %s %s" % (ilomAdmUsr,
                                                                          ilom[i], ilomAdmPwd, ilomUsrPwd, vlanid, vlanIp[i], vlannetmask, imagelog, ilomTimeout)
        out, err = cf.exc_cmd_new(cmd)
        if err:
            log.info(out)
            log.error("Set up the VLAN public ip on ilom %s failed" % ilom[i])
            sys.exit(0)
    return vlanIp


def network_list(hostname, version):
    x7_flag = is_x7_or_not(hostname)
    x6_flag = is_x6_or_not(hostname)
    x6_lite_flag = is_x6_lite_or_not(hostname)
    x5_flag = is_x5_or_not(hostname)
    x8_flag = is_x8_or_not(hostname)

    if x7_flag:
        network = x7_network(version)
        #dcsflag = 1
    elif x6_flag:
        network = x6_network(x6_lite_flag, version)
        #dcsflag = is_dcs(hostname, version)
    elif x5_flag:
        network = x5_network(version)
    elif x8_flag:
        network = netconfig_x6

    else:
        network = [netconfig[0]]
        #dcsflag = is_dcs(hostname, version)
    return network


def configure_firstnet(hostname, version, vmflag, *net_d):
    log_stamp = datetime.datetime.today().strftime("%Y%m%d")
    imagelog = os.path.join(log_dir,"configure-firstnet_%s_%s.log" % (hostname, log_stamp))

    if vmflag:
        ips = configure_firstnet_vm(hostname, imagelog)

    else:
        net_list = network_list(hostname, version)
        log.info(net_list)
        log.info(net_d)
        if len(net_d) and net_d[0] in net_list:
            network = net_d[0]
            log.info("The defined network is %s" % network)
        else:
            network= random.choice(net_list)

        # if host_d[hostname]["jbod"] == 2 and cf.trim_version (version) in image.ver_19:
        #     image.set_node_number_new (host_d[hostname]["ilom"], imagelog)

        if network == netconfig[2]:
            ips = configure_firstnet_vlan(hostname, imagelog)
        elif network == netconfig[1]:
            ips = configure_firstnet_nonbonding(hostname, imagelog)
        else:
            dcsflag = is_dcs(hostname, version)
            ips = configure_firstnet_bond(hostname, imagelog, dcsflag)

    time.sleep(120)
    cf.covertlog(imagelog)
    image.check_all_host_reachable(ips)
    print "Finish configure firstnet!"
    ping_prinet(ips)
    return ips


def ping_prinet(ips):
    if len(ips) == 1:
        return 1
    hostname = ips[0]
    host = oda_lib.Oda_ha(hostname, "root", "welcome1")
    flag = 1
    cmd = "ping -c 3 192.168.16.25 | grep '3 received' | wc -l"
    result, error = host.ssh2node_job (cmd)
    if error:
        flag = 0
    else:
        if not int (result):
            flag = 0
    if not flag:
        log.warn("Since the privite network is not pingable, will reboot both nodes as w/a!")
        host2 = oda_lib.Oda_ha(ips[1], host.username, host.password)
        host.ssh2node ("reboot")
        host2.ssh2node("reboot")
        cf.wait_until_ping(hostname)
        cf.wait_until_ping(ips[1])
    else:
        log.info("Privite network is pingable!")

def initnetworklogger(hostname):
    logname = "configure_network_%s.log" % hostname
    logfile = os.path.join(log_dir, logname)
    log = initlogging.initLogging("configure_firstnet", logfile, logging.INFO, logging.DEBUG)
    return log


def initlog(plog):
    oda_lib.initlog(plog)
    image.initlog(plog)
    global log
    log = plog



def log_management(hostname):
    log = initnetworklogger(hostname)
    initlog(log)
    


if __name__ == "__main__":
    arg = docopt(__doc__)
    print arg
    hostname = arg['-s']
    version = arg['-v']
    vm = arg["--vm"]
    #image.is_node_support(hostname)
    log_management(hostname)
    if arg["--network"] and arg["--network"] in netconfig:
        net_def = arg["--network"]
        ips = configure_firstnet(hostname, version, vm, net_def)
    else:
        ips = configure_firstnet(hostname, version, vm)
    print "Please use the following ips:"
    print ips
    print "Please use the new ip %s for new host!" % ips[0]
    dcs = is_dcs(hostname, version, vm)
    if dcs:
        print "This is DCS stack!"
    else:
        print "This is OAK stack!"