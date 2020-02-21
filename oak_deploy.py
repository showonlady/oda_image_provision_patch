#!/usr/env/bin python
# -*- conding:utf-8 -*-

"""
Usage:
    oak_deploy.py -h
    oak_deploy.py  -s <servername> [-u <username>] [-p <password>] [-o <onecommand.params>]

Options:
    -h,--help       Show this help message
    -s <servername>  hostname of machine, if vlan,use ip instead
    -u <username>  username [default: root]
    -p <password>  password [default: welcome1]
    -o <onecommand.params>   The onecommand file name with path
"""


from docopt import docopt
import oda_lib
import logging
import os, sys
import common_fun as cf
import initlogging
import random
import re
import datetime

def oak_deploy(*a):
    host = a[0]
    if host.is_vm_or_not():
        vmflag = True
    else:
        vmflag = False
    s_v = host.system_version()
    version = cf.trim_version(s_v)
    scp_unpack_file(host, version)
    if len(a) == 2:
        jsonfile = a[1]
    elif len(a) == 1:
        if vmflag:
            jsonfile = onecommand_file(host.hostname, version, 1)
        else:
            jsonfile = onecommand_file (host.hostname, version)
    else:
        pass

    remote_file = os.path.join("/tmp", os.path.basename(jsonfile))
    host.scp2node(jsonfile,remote_file)
    cmd = "/opt/oracle/oak/bin/oakcli copy -conf %s" % remote_file
    log.info(cmd)
    result = host.ssh2node(cmd)
    log.info(result)
    if vmflag:
        cmd = "/opt/oracle/oak/onecmd/GridInst.pl -o -r 0-23"
    else:
        cmd = "/opt/oracle/oak/onecmd/GridInst.pl -r 0-23"

    log.info(cmd)
    result = host.ssh2node(cmd)
    log_stamp = datetime.datetime.today ().strftime ("%Y%m%d")
    logfile = os.path.join (cf.log_dir, "bm_odabase_girac_deploy_%s_%s.log" % (host.hostname, log_stamp))
    fp = open (logfile, 'w')
    fp.write (result)
    fp.close()
    cf.covertlog(logfile)
    fp = open(logfile, 'r')
    result = fp.read()
    fp.close()

   # log.info(result)
    if check_deploy(result):
        print "Successlly finished gi/rac deployment!"
        return 1
    else:
        log.error("Fail to deploy gi/rac!")
        return 0

def check_deploy(result):
    str = "INFO.*Time spent in step .* SetupASR is"
    if re.search(str, result):
        return 1
    else:
        return 0


def onecommand_file(*a):
    hostname = a[0]
    version = a[1]
    dir1 = "/chqin/json/%s*%s*bm*" % (hostname[0:9], version)
    dir2 = "/home/chqin/qcl/onecmd.params/%s_%s_bm*" % (hostname[0:9], version)
    if len(a) == 3:
        dir1 = "/chqin/json/%s*%s*vm*" % (hostname[0:9], version)
        dir2 = "/home/chqin/qcl/onecmd.params/%s*%s*vm*" %(hostname[0:9], version)

    log.info(dir2)
    out,err = cf.exc_cmd_new("ls %s" % dir1)
    if err != 0:
        out, err = cf.exc_cmd_new("ls %s" % dir2)
        if err != 0:
            log.error("onecommad parameter file could not be found under %s!" % dir2)
            sys.exit(0)
        else:
            result = out
    else:
        result = out

    file = random.choice(result.split())
    file = file.strip()
    return file



def scp_unpack_file(host, version):
    remote_dir = "/tmp"
    clone_loc = "/chqin/ODA%s/OAKEndUserBundle*" % version
    out, err = cf.exc_cmd_new("ls %s" % clone_loc)
    if err:
        log.error("Fail to find the OAKEndUserBundle under the dir %s" % clone_loc)
        sys.exit(0)
    for i in out.split():
        remote_file = os.path.join(remote_dir, os.path.basename(i))
        host.scp2node(i, remote_file)
        cmd = "/opt/oracle/oak/bin/oakcli unpack -package %s" % remote_file
        result, error = host.ssh2node_job(cmd)
        if error:
            log.error("Unpack the file %s failed on host %s" % (remote_file, host.hostname))
            sys.exit(0)


def log_management(hostname):
    global logfile_bm
    logname = "oakcli_deploy_%s.log" % hostname
    logfile_bm = os.path.join(cf.log_dir, logname)
    log = initlogging.initLogging("oakcli_deploy", logfile_bm, logging.WARN, logging.DEBUG)
    initlog(log)


def initlog(plog):
    oda_lib.initlog(plog)
    global log
    log = plog





if __name__ == '__main__':
    arg = docopt(__doc__)
    print arg
    hostname = arg['-s']
    username = arg['-u']
    password = arg['-p']
    log_management(hostname)
    host = oda_lib.Oda_ha(hostname, username, password)
    if arg['-o']:
        jsonfile = arg['-o']
        oak_deploy(host,jsonfile)
    else:
        oak_deploy(host)
    print("Finished gi/rac deployment, please check log %s for details" % logfile_bm)