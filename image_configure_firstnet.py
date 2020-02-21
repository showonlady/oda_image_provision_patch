
#!/usr/bin/env python
#coding utf-8
#
# Copyright (c) 2018, Oracle and/or its affiliates. All rights reserved.
#
#    NAME
#      image_configure_firstnet.py
#
#    DESCRIPTION
#      Image, configure firstnet, provision, create multiple databases...etc
#
#    NOTES
#
#
#    MODIFIED   (MM/DD/YY)
#    chqin    04/07/18 - Creation
#


"""
Usage:
    image_configure_firsnet.py  -s <servername> -v <version> [-u <username>] [-p <password>] [--vm] [--network <vlan>]
    image_configure_firsnet.py [nocleanup] [nodeploy] -s <servername> -v <version> [-u <username>] [-p <password>] [--vm] [--network <vlan>]
    image_configure_firsnet.py [nocleanup] [nopatch] -s <servername> -v <version> [-u <username>] [-p <password>] [--network <vlan>][--vm]

Options:
    -h,--help       Show this help message
    -s <servername>   hostname of machine,if ha only give the 1st nodename
    -v <version>   the version you want to re-image to
    -u <username>   username [default: root]
    -p <password>   password [default: welcome1]
    --vm   image to vm stack
    nodeploy   Don't do the deploy
    nopatch    Don't do the patch, only prepare the environment
    nocleanup  Don't run cleanup script before reimage
    --network <vlan>   network type, vlan, bonding, nonbonding

"""

import image
import configure_firstnet
from docopt import docopt
import oda_lib
import deploy_patch_patch as d_p_p
import common_fun as cf
import sys
import time
import logging
import initlogging
import os
import oak_deploy
import vm_deploy
import oak_create_db
import oak_patch as o_p
import oak_deploy_patch_patch as o_d_p_p

def initlogger(hostname):
    global logfile
    logname = 'Image_firstnet_provision_patch_%s.log' % hostname
    logfile = os.path.join(cf.log_dir, logname)
    logger = initlogging.initLogging("image_provision_patch", logfile, logging.WARN, logging.DEBUG)
    return logger

def initlog(plog):
    oda_lib.initlog(plog)
    image.initlog(plog)
    configure_firstnet.initlog(plog)
    d_p_p.initlog(plog)
    # oak_deploy.initlog(plog)
    # vm_deploy.initlog(plog)
    # oak_create_db.initlog(plog)
    # o_p.initlog(plog)
    o_d_p_p.initlog(plog)
    global log
    log = plog
    
def log_management(hostname):
    log = initlogger(hostname)
    initlog(log)

def main(arg):
    hostname = arg['-s']
    version = arg['-v']
    password = arg['-p']
    username = arg['-u']
    vm = arg["--vm"]
    nodeploy = arg['nodeploy']
    nocleanup = arg['nocleanup']
    net_d = arg["--network"]
    nopatchflag = arg['nopatch']
    image.is_node_support(hostname)
    log_management(hostname)
    if not nocleanup:
        image.cleanup(hostname, username, password)
        time.sleep(300)
    else:
        log.info("Will not run cleanup scripts on host %s" % hostname)
    log.info("Will image the host %s" % hostname)
    image.image(hostname, version, vm)
    if net_d and net_d in configure_firstnet.netconfig:
        ips = configure_firstnet.configure_firstnet(hostname, version, vm, net_d)
    else:
        ips = configure_firstnet.configure_firstnet(hostname, version, vm)
    log.info("Finish configure firstnet, you can use the following ip to configure:")
    log.info(ips)
    print ips
    host = oda_lib.Oda_ha(ips[0], "root", "welcome1")
    if nodeploy:
        log.info("Will not do the provision, please deploy %s via oda_deploy.py or deploy_patch_patch.py!" % ips[0])

    elif vm:
        log.info("This host is OAK VM stack, will continue to deploy on %s" % ips[0])
        # if vm_deploy.vm_deploy(host, version):
        #     host = oda_lib.Oda_ha (hostname, "root", "welcome1")
        #     oak_create_db.main(host)
        #     o_p.main(host, nopatchflag)
        o_d_p_p.deploy_patch(host, nopatchflag)
    elif not configure_firstnet.is_dcs(hostname, version):
        log.info("This host is OAK stack, will continue to deploy %s to %s!" % (ips[0], version))
        # if oak_deploy.oak_deploy(host):
        #     oak_create_db.main(host)
        #     o_p.main(host, nopatchflag)
        o_d_p_p.deploy_patch(host, nopatchflag)

    else:
        log.info("Will do the provision and patch to latest version!")
        time.sleep(300)
        d_p_p.provision_patch(host, nopatchflag)
#    cf.closefile(fp, out, err)
    print "Finish, please check the log %s for details!, the host ips are:" % logfile
    print ips


if __name__ == '__main__':
    arg = docopt(__doc__)
    print arg
    main(arg)