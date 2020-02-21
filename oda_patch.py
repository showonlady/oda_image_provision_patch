#!/usr/bin/env python
#conding utf-8
"""
Usage:
    oda_patch.py -h
    oda_patch.py -s <servername> [-u <username>] [-p <password>] [-v <version>]

Options:
    -h,--help       Show this help message
    -s <servername>  hostname of machine, if vlan,use ip instead
    -u <username>  username [default: root]
    -p <password>  password [default: welcome1]
    -v <version>   The version number you want to patch
"""


from docopt import docopt
import oda_lib
import sys
import common_fun as cf
import os
import re
import random
import time
import logging
import initlogging
log_dir = cf.log_dir
#The version need gi out of place patch
patch_version = ['12.1.2.8','12.1.2.8.1','12.1.2.9','12.1.2.10','12.1.2.11', '12.1.2.12','12.2.1.1','12.2.1.2','12.2.1.3','12.2.1.4',"18.3", "18.5" ]

def scpfile(host, remote_dir, server_loc):
    for i in os.listdir(server_loc):
        if not i:
            sys.exit(1)
        else:
            remote_file = os.path.join(remote_dir, i)
            local_file = os.path.join(server_loc, i)
            host.scp2node(local_file, remote_file)

def unpack_all_files(host, remote_dir, server_loc):
    for i in os.listdir(server_loc):
        file = os.path.join(remote_dir, i)
        if host.update_repository("-f %s" % file):
            cmd = "rm -rf %s" % file
            host.ssh2node(cmd)
        else:
            log.error("Unpack the repository %s failed!" % file)
            sys.exit(0)



def update_dcsagent(host, version):
    if host.update_dcsagent("-v %s" % version):
        return 1
    else:
        return 0

def is_12211_or_not(host):
    cmd = "rpm -qa|grep dcs-agent"
    output = host.ssh2node(cmd)
    if re.search('12.2.1.1', output):
        return 1
    else:
        return 0

def close_firewall(host):
    cmd1 = "service iptables stop"
    cmd2 = "chkconfig iptables off"
    host.ssh2node(cmd1)
    host.ssh2node(cmd2)
    if host.is_ha_not():
        host2name = cf.node2_name(host.hostname)
        host2 = oda_lib.Oda_ha(host2name, host.username, host.password)
        host2.ssh2node(cmd1)
        host2.ssh2node(cmd2)



def update_server_precheck(host, version):
    """prechecks"""
    flag = 1
    s_v = host.system_version()
    s_v = cf.trim_version(s_v)
    if s_v not in patch_version and host.is_ha_not():
        op_pre = ['-v %s -p' % version, '-v %s -p -l' % version, '-v %s -p -n 0' % version, '-v %s -p -n 1' % version]
    else:
        op_pre = ['-v %s -p' % version]


    for i in op_pre:
        if not host.update_server(i):
            flag = 0
            log.error("update server precheck fail! %s" % i)

    # if host.is_ha_not():
    #     if s_v not in patch_version:
    #         op_pre_ha = '-v %s -p -n 1' % version
    #         if not host.update_server(op_pre_ha):
    #             flag = 0
    #             log.error("update server precheck fail! %s" % op_pre_ha)

    return flag

def update_server(host, version):
    flag = 1
    s_v = host.system_version()
    s_v = cf.trim_version(s_v)
    if s_v in patch_version:
        op_lite = ['-v %s' % version]
    else:
        ###For odalite we don't support local patch#####
        op_lite = ['-v %s' % version]
        #op_lite = ['-v %s' % version,'-v % s -l'% version,'-v %s -n 0' % version]
    op1 = random.choice(op_lite)
    if not host.is_ha_not():
        if not host.update_server(op1):
            flag = 0
            log.error("update server fail! %s" % op1)
    else:
        ###For 12.x to 18.3, we don't support local path.for 18.3/18.5/, we also don't support local patch to 18.8
        if random.choice([True, False]) and s_v not in patch_version:
            if not host.update_server("-v %s -n 1" % version):
                flag = 0
                log.error("update server with '-v -n 1' fail!")
                sys.exit(0)
            time.sleep(600)
            hostname2 = cf.node2_name(host.hostname)
            cf.wait_until_ping(hostname2)
            if not host.update_server("-v %s -n 0" % version):
                flag = 0
                log.error("update server with '-v -n 0' fail!")
        else:
            if not host.update_server ("-v %s" % version):
                flag = 0
                log.error ("update server with '-v' fail!")
    return flag


def dbhome_patch(host, version = oda_lib.Oda_ha.Current_version):
    log.info("*" * 20 + "dbhome patch begin" + "*" * 20)
    log.info(host.describe_component())
    log.info(host.crs_status())
    if cf.trim_version (version) == "18.8":
        host.stop_tfa()
    cmd = "/opt/oracle/dcs/bin/odacli list-dbhomes"
    log.info(host.ssh2node(cmd))
    cmd = "/opt/oracle/dcs/bin/odacli list-dbhomes|grep -i Configured|awk '{print $1}'"
    result = host.ssh2node(cmd)
    if not result:
        log.error("not dbhome to patch!")
    else:
        dbhomeid = result.split()
        for i in dbhomeid:
            patch_one_dbhome(host,i, version)
    log.info(host.describe_component())
    log.info(host.crs_status())
    cmd = "/opt/oracle/dcs/bin/odacli list-dbhomes"
    log.info(host.ssh2node(cmd))
    log.info("*" * 20 + "dbhome patch finish" + "*" * 20)




def patch_one_dbhome(host, id, version):
    if host.is_ha_not():
       if random.choice([True, False]):
           if not host.update_dbhome("-v %s -i %s -p" % (version, id)):
               log.error("dbhome %s precheck failed!" % id)
           if not host.update_dbhome("-v %s -i %s" % (version, id)):
               log.error("dbhome %s patch failed!" % id)

       else:
           if not host.update_dbhome("-v %s -i %s -n 0 -p" % (version, id)):
               log.error("dbhome %s precheck failed!" % id)

           if not host.update_dbhome("-v %s -i %s -l" % (version, id)):
               log.error("dbhome %s patch failed!" % id)

           if not host.update_dbhome("-v %s -i %s -n 1 -p" % (version, id)):
               log.error("dbhome %s precheck failed!" % id)

           if not host.update_dbhome("-v %s -i %s -n 1" % (version, id)):
               log.error("dbhome %s patch failed!" % id)


    else:
        if not host.update_dbhome("-v %s -i %s -p" % (version, id)):
            log.error("dbhome %s precheck failed!" % id)

        if not host.update_dbhome("-v %s -i %s" % (version, id)):
            log.error("dbhome %s patch failed!" % id)

"""
def node2_name(a):
    b = a[:-1] + str(int(a[-1]) + 1)
    return b
"""

def storage_patch(host, version = oda_lib.Oda_ha.Current_version):
    log.info("*" * 20 + "storage patch begin" + "*" * 20)
    log.info(host.describe_component())
    log.info(host.crs_status())
    if host.is_ha_not():
        if not host.update_storage('-v %s -r' %version):
            log.error("update storage with rolling failed!")
            time.sleep(60)
            if not host.update_storage('-v %s' %version):
                log.error("update storage fail!")
                sys.exit(0)
    else:
        if not host.update_storage ('-v %s' % version):
            log.error ("update storage fail!")
            sys.exit (0)
    log.info("*" * 20 + "storage patch finish" + "*" * 20)

def unpack_server_zip(host, version = oda_lib.Oda_ha.Current_version):
    v_loc = "ODA" + cf.trim_version(version)
    #v_loc = "ODA" + '.'.join(version.split('.')[0:4])
    remote_dir = '/tmp/'
    server_loc = '/chqin/%s/patch/' % v_loc
    scpfile(host, remote_dir, server_loc)
    unpack_all_files(host, remote_dir, server_loc)
    hostname = host.hostname
    username = host.username
    password = host.password
    if host.is_ha_not() and is_12211_or_not(host):
        node2 = cf.node2_name(hostname)
        host2 = oda_lib.Oda_ha(node2, username, password)
        scpfile(host2, remote_dir, server_loc)
        unpack_all_files(host2,remote_dir, server_loc)
    #####Add stop tfa in 18.8
    if cf.trim_version(version) == "18.8":
        host.stop_tfa()
    # if cf.trim_version(version) == '18.7':
    #     log.info("Will replace dcsagent files!")
    #     replace_dcsagent_file(host)

def replace_dcsagent_file(host):
    files_loc = "/chqin/ODA18.7/dcsagent/"
    remote_dir = "/opt/oracle/oak/pkgrepos/dcsagent/18.7.0.0.0"
    scpfile(host,remote_dir,files_loc)
    if host.is_ha_not():
        node2 = cf.node2_name (host.hostname)
        host2 = oda_lib.Oda_ha (node2, host.username, host.password)
        scpfile (host2, remote_dir, files_loc)


def dcs_patch(host, version = oda_lib.Oda_ha.Current_version):
    unpack_server_zip (host, version)
    cf.extend_space_u01 (host)
    # close_firewall(host)
    log.info ("*" * 20 + "dcsagent patch begin" + "*" * 20)
    log.info (host.describe_component ())
    log.info (host.crs_status ())
    if not update_dcsagent (host, version):
        log.error ("update dcsagent failed on %s" % host.hostname)
        sys.exit (0)
    else:
        dcs_agent_version = host.ssh2node ("rpm -qa|grep dcs-agent")
        if cf.trim_version (re.search ('dcs-agent-(.*)_LI', dcs_agent_version).group (1)) == cf.trim_version (version):
            log.info ("The new installed dcs version: %s" % dcs_agent_version)
        else:
            log.error ("Fail to update dcsagent: %s" % dcs_agent_version)

    time.sleep (180)
    log.info (host.describe_component ())
    log.info (host.crs_status ())
    log.info ("*" * 20 + "dcsagent patch finish" + "*" * 20)

def replace_file(host):
    remote_file1 = "/opt/oracle/oak/pkgrepos/System/latest/patchmetadata.xml"
    remote_file2 = "/opt/oracle/oak/pkgrepos/System/18.7.0.0.0/patchmetadata.xml"
    remote_file3 = "/opt/oracle/oak/pkgrepos/System/18.7.0.0.0/metadata.xml"
    file1 = "/chqin/ODA18.7/alok_patchmetadata/latest/patchmetadata.xml"
    file2 = "/chqin/ODA18.7/alok_patchmetadata/18.7.0.0.0/patchmetadata.xml"
    file3 = "/chqin/ODA18.7/alok_patchmetadata/18.7.0.0.0/metadata.xml"
    host.scp2node (file1, remote_file1)
    host.scp2node (file2, remote_file2)
    host.scp2node (file3, remote_file3)
    if host.is_ha_not():
        node2 = cf.node2_name(host.hostname)
        host2 = oda_lib.Oda_ha(node2, host.username, host.password)
        host2.scp2node (file1, remote_file1)
        host2.scp2node (file2, remote_file2)
        host2.scp2node (file2, remote_file3)


def new_dcs_patch(host, version = oda_lib.Oda_ha.Current_version):
    unpack_server_zip(host, version)
    #w/a for replacing metadata files
    #replace_file(host)
    cf.extend_space_u01(host)
    #close_firewall(host)
    log.info("*" * 20 + "dcsagent patch begin" + "*" * 20)
    log.info(host.describe_component())
    log.info(host.crs_status())

    if not update_dcsagent(host, version):
        log.error("update dcsagent failed on %s" % host.hostname)
        sys.exit (0)
        # cmd = "sh /opt/oracle/dcs/bin/setupAgentAuth.sh"
        # if host.is_ha_not():
        #     cmd1 = "sed -i 's+cp -f $dcsagentbaseDir/conf/dcs-agent-auth.json $dcsagentbaseDir/conf/dcs-agent.json+#cp -f $dcsagentbaseDir/conf/dcs-agent-auth.json $dcsagentbaseDir/conf/dcs-agent.json+' /opt/oracle/dcs/bin/setupAgentAuth.sh"
        #     cmd2 = "sed -i 's+cp -f $dcsagentbaseDir/conf/dcs-agent.json $dcsagentbaseDir/conf/dcs-agent.json.bk+#cp -f $dcsagentbaseDir/conf/dcs-agent.json $dcsagentbaseDir/conf/dcs-agent.json.bk+' /opt/oracle/dcs/bin/setupAgentAuth.sh"
        #     host.ssh2node(cmd2)
        #     host.ssh2node(cmd1)
        #     host.ssh2node(cmd)
        #     node2 = cf.node2_name(host.hostname)
        #     host2 = oda_lib.Oda_ha(node2, host.username,host.password)
        #     host2.ssh2node(cmd1)
        #     host2.ssh2node(cmd2)
        #     host2.ssh2node(cmd)
        # else:
        #     host.ssh2node(cmd)
    else:
        dcs_agent_version = host.ssh2node("rpm -qa|grep dcs-agent")
        if cf.trim_version(re.search('dcs-agent-(.*)_LI', dcs_agent_version).group(1)) == cf.trim_version(version):
            log.info("The new installed dcs version: %s"% dcs_agent_version)
        else:
            log.error("Fail to update dcsagent: %s" % dcs_agent_version)
    time.sleep(180)
    log.info(host.describe_component())
    log.info(host.crs_status())
    if not host.update_dcsadmin("-v %s" % version):
        log.error("Update dcsadmin failed!")
        sys.exit(0)
    # if not host.update_dcscomponents("-v %s" % version):
    #     log.error("Update dcscomponents failed!")
    #     sys.exit(0)
    component_cmd = "%s update-dcscomponents -v %s" % (host.ODACLI, version)
    log.info(component_cmd)
    result = host.ssh2node(component_cmd)
    log.info(result)
    log.info("*" * 20 + "dcsagent patch finish" + "*" * 20)




def server_patch(host, version = oda_lib.Oda_ha.Current_version):
    log.info("*" * 20 + "server patch begin" + "*" * 20)
    log.info(host.describe_component())
    log.info(host.crs_status())
    if cf.trim_version (version) == "18.8":
        host.stop_tfa()
    log.info(host.hostname + '\n' + host.ssh2node("df -h"))
    if host.is_ha_not():
        node2 = cf.node2_name(host.hostname)
        host2 = oda_lib.Oda_ha(node2, host.username, host.password)
        log.info(node2 + '\n' + host2.ssh2node("df -h"))
    if not update_server_precheck(host, version):
        log.error("update server precheck failed on %s" % host.hostname)
        sys.exit(0)
    if not update_server(host, version):
        log.error("update server failed")
        sys.exit(0)
    log.info("*" * 20 + "server patch finish" + "*" * 20)

def simple_update_server(host,version):
    log.info("*" * 20 + "server patch begin" + "*" * 20)
    log.info(host.describe_component())
    log.info(host.crs_status())
    if cf.trim_version (version) == "18.8":
        host.stop_tfa()
    if not host.update_server("-v %s" % version):
        log.error("update server with '-v' fail!")
        sys.exit(0)
    log.info("*" * 20 + "server patch finish" + "*" * 20)

def simple_update_dbhome(host,version):
    log.info("*" * 20 + "dbhome patch begin" + "*" * 20)
    log.info(host.describe_component())
    log.info(host.crs_status())
    if cf.trim_version (version) == "18.8":
        host.stop_tfa()
    cmd = "/opt/oracle/dcs/bin/odacli list-dbhomes"
    log.info(host.ssh2node(cmd))
    cmd = "/opt/oracle/dcs/bin/odacli list-dbhomes|grep -i Configured|awk '{print $1}'"
    result = host.ssh2node(cmd)
    if not result:
        log.info("not dbhome to patch!")
    else:
        dbhomeid = result.split()
        for i in dbhomeid:
            if not host.update_dbhome("-v %s -i %s" % (version, i)):
                log.info("dbhome %s patch failed!" % i)
    log.info(host.describe_component())
    log.info(host.crs_status())
    cmd = "/opt/oracle/dcs/bin/odacli list-dbhomes"
    log.info(host.ssh2node(cmd))
    log.info("*" * 20 + "dbhome patch finish" + "*" * 20)




def main(hostname,username,password, version):
    # logfile_name = 'check_oda_patch_%s.log' % hostname
    # fp, out, err,log = cf.logfile_name_gen_open(logfile_name)
    log_management(hostname)
    host = oda_lib.Oda_ha(hostname, username, password)
    ver = cf.trim_version(version)
    if ver in ["18.3", "18.5"]:
        dcs_patch(host, version)
    else:
        new_dcs_patch(host, version)
    host = oda_lib.Oda_ha(hostname, username, password)
    server_patch(host, version)
    time.sleep(600)
    cf.wait_until_ping(host.hostname)
    host2 = oda_lib.Oda_ha(hostname, username, password)
    dbhome_patch(host2, version)
    time.sleep(600)
    storage_patch(host2, version)
    time.sleep(600)
    cf.wait_until_ping(host2.hostname)
    print "Done, please check the log %s for details!" % logfile


def initlogger(hostname):
    global logfile
    logname = "odacli_patch_%s.log" % hostname
    logfile = os.path.join(log_dir, logname)
    log = initlogging.initLogging("patch", logfile, logging.WARN, logging.DEBUG)
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
    if arg['-v']:
        version = arg['-v']
    else:
        version = oda_lib.Oda_ha.Current_version

    main(hostname, username, password, version)



