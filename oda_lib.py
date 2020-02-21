#!/usr/bin/env python
#coding utf-8

import re
import os
import paramiko
import traceback
import time
import simplejson
import common_fun as cf
import sys
import logging
import initlogging
import re
import pexpect
import datetime

def initlog(plog):
    global logger
    logger = plog

def simplejson_load(result):
    try:
        d = simplejson.loads (result)
    except Exception as e:
        logger.error(result)
        d = None
    return d

class Oda_ha(object):
    Current_version = "18.8.0.0"
    db_versions = ["11.2.0.4.191015","12.2.0.1.191015", "12.1.0.2.191015","18.8.0.0.191015"]
    ODACLI = "/opt/oracle/dcs/bin/odacli "
    old_version = ['12.1.2.8','12.1.2.8.1','12.1.2.9','12.1.2.10','12.1.2.11', '12.1.2.12', '12.2.1.1','12.2.1.2',
           '12.2.1.3', '12.2.1.4','18.1', '18.2.1', '18.3', '18.4','18.5']
    def __init__(self, hostname, username, password):
        self.hostname = hostname
        self.username = username
        self.password = password
        self.newpassword = "WElcome12_-"
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            self.ssh.connect(hostname=self.hostname, port=22, username=self.username, password=self.password)
        except Exception as e:
            self.ssh.connect(hostname=self.hostname, port=22, username=self.username, password=self.newpassword)
        try:
            self.transport = paramiko.Transport((self.hostname, 22))
            self.transport.connect(username=self.username, password=self.password)
        except Exception as e:
            self.transport = paramiko.Transport((self.hostname, 22))
            self.transport.connect(username=self.username, password=self.newpassword)

    def is_dcs_or_oak(self):
        cmd = "rpm -qa|grep dcs"
        result = self.ssh2node(cmd)
        if result:
            return 1
        else:
            return 0

    def is_vm_or_not(self):
        cmd = "rpm -qa|grep ovm-template"
        result = self.ssh2node(cmd)
        if result:
            return 1
        else:
            return 0

    def is_deployed_or_not(self):
        cmd = "ps -ef|grep 'init.ohasd' |grep -v grep"
        result = self.ssh2node(cmd)
        if result:
            return 1
        else:
            return 0

    def is_patch_or_not(self):
        cmd = Oda_ha.ODACLI +  " list-jobs|grep -i server"
        result = self.ssh2node(cmd)
        if result:
            return 1
        else:
            return 0


    def is_x6(self):
        flag = 0
        cmd = "cat /proc/cmdline|grep X6"
        result = self.ssh2node(cmd)
        if result:
            flag = 1
        else:
            cmd2 = "ls -l  /etc/oda/environment"
            result2, err = self.ssh2node_job (cmd2)
            if not err:
                cmd3 = "cat /etc/oda/environment |grep X6"
                result3 = self.ssh2node (cmd3)
                if result3:
                    flag = 1
        return flag


    def is_x8(self):
        flag = 0
        cmd = "cat /proc/cmdline|grep X8"
        result = self.ssh2node(cmd)
        if result:
            flag = 1
        else:
            cmd2 = "ls -l  /etc/oda/environment"
            result2, err = self.ssh2node_job(cmd2)
            if not err:
                cmd3 = "cat /etc/oda/environment |grep X8"
                result3 = self.ssh2node(cmd3)
                if result3:
                    flag = 1
        return flag


    def is_x7(self):
        flag = 0
        cmd = "cat /proc/cmdline|grep X7"
        result = self.ssh2node(cmd)
        if result:
            flag = 1
        else:
            cmd2 = "ls -l  /etc/oda/environment"
            result2, err = self.ssh2node_job (cmd2)
            if not err:
                cmd3 = "cat /etc/oda/environment |grep X7"
                result3 = self.ssh2node (cmd3)
                if result3:
                    flag = 1
        return flag

    def is_x4(self):
        flag = 0
        cmd = "cat /proc/cmdline|grep V3"
        result = self.ssh2node (cmd)
        if result:
            flag = 1
        else:
            cmd2 = "ls -l  /etc/oda/environment"
            result2, err = self.ssh2node_job (cmd2)
            if not err:
                cmd3 = "cat /etc/oda/environment |grep X4"
                result3 = self.ssh2node (cmd3)
                if result3:
                    flag = 1
        return flag

    def is_x3(self):
        cmd = "cat /proc/cmdline |grep V2"
        result = self.ssh2node(cmd)
        if result:
            return 1
        else:
            return 0

    def is_x5(self):
        flag = 0
        cmd = "cat /proc/cmdline|grep X5"
        result = self.ssh2node(cmd)
        if result:
            flag = 1
        else:
            cmd2 = "ls -l  /etc/oda/environment"
            result2, err = self.ssh2node_job (cmd2)
            if not err:
                cmd3 = "cat /etc/oda/environment |grep X5"
                result3 = self.ssh2node (cmd3)
                if result3:
                    flag = 1
        return flag

    def is_hdd_or_ssd(self):
        cmd = "/usr/sbin/fwupdate list disk|grep HDD"
        result = self.ssh2node(cmd)
        if result:
            return 1
        else:
            return 0
            
    def is_latest_or_not(self):
        s_v = self.system_version()
        a = cf.trim_version(s_v)
        b = cf.trim_version(Oda_ha.Current_version)
        if a == b:
            return 1
        else:
            return 0


    def system_version(self):
        cmd = "cat /opt/oracle/oak/pkgrepos/System/VERSION"
        result = self.ssh2node(cmd)
        v = result.split("=")[1]
        return v

    
    
    def ssh2node(self, cmd):
        #print cmd
        stdin, stdout, stderr = self.ssh.exec_command(cmd)
        result = stdout.read().strip()
        errormsg = stderr.read().strip()
        # self.ssh.close()
        return result + errormsg

    def ssh2node_input(self, cmd, bkpassword='',input =''):
        #logger.info(cmd)
        sys.stdout.flush()
        stdin, stdout, stderr = self.ssh.exec_command(cmd)
        if not input:
            stdin.write("%s\n" % self.newpassword)
        else:
            stdin.write("%s\n" % input)

        if bkpassword:
            time.sleep(10)
            stdin.write("%s\n" % bkpassword)

        result = stdout.read().strip()
        errormsg = stderr.read().strip()
        p = re.compile(".*option is deprecated.*instead$")
        if p.search(errormsg):
            errormsg = None
        #print result
        return result, errormsg

    def ssh2node_job(self, cmd):
        stdin, stdout, stderr = self.ssh.exec_command(cmd)
        result = stdout.read().strip()
        error = stderr.read().strip()
        p = re.compile(".*option is deprecated.*instead$")
        if p.search(error):
            error = None
        return result, error


    def scp2node(self, scp_file, remote_file):
        sftp = paramiko.SFTPClient.from_transport(self.transport)
        sftp.put(scp_file, remote_file)

    def is_ha_not(self):
        flag = 1
        if  self.is_x4() or self.is_x3() or self.is_x5():
            return flag
        else:
            cmd = 'cat /proc/cmdline |grep -i nvme'
            result = self.ssh2node(cmd)
            if result:
                flag =0
        return flag


    def is_ib_not(self):
        cmd = "/sbin/lspci|grep -i Mellanox"
        result = self.ssh2node(cmd)
        if result:
            return 1
        else:
            return 0



    def is_flash(self):
        cmd = '/opt/oracle/oak/bin/odaadmcli show diskgroup|grep -i FLASH'
        result = self.ssh2node(cmd)
        if result:
            return 1
        else:
            return 0


###Only for x7
    def is_bonding_or_not(self):
        cmd = "ls /etc/sysconfig/network-scripts/ifcfg-btbond1"
        result = self.ssh2node(cmd)
        #print result
        if re.search("No such", result):
            return 0
        else:
            return 1


    def run_cmd(self, cmd, bkpassword='', input=''):
        logger.info(cmd)
        result,error = self.ssh2node_input(cmd, bkpassword=bkpassword, input=input)
        if error:
            logger.error(error)
            return 0
        else:
            logger.info(result)

        #d = simplejson.loads(result)
        #jobid = d['jobId']
        try:
            jobid = re.search('jobId.*"(\S+)"', result).group(1)
        except Exception as e:
            logger.error("Could not find the jobid!")
            #print "Could not find the jobid!"
            return 0

        if not jobid:
            return 0
        time.sleep(60)
        cmd1 = Oda_ha.ODACLI + "describe-job -j -i %s" % jobid
        while True:
            tasks, err = self.ssh2node_job(cmd1)
            if err:
                logger.error(err)
                sys.exit(0)
                            
            #job_status = re.findall('Status:\s*(\S+)', tasks)[0]
            a = simplejson_load(tasks)
            job_status = a['status']
            if job_status.lower() == 'success':
                return 1
            elif job_status.lower() in ('running', "waiting"):
                time.sleep(5)
            else:
                logger.error("job fail!\n")
                return 0

    def create_database(self, options):
        options = cf.change_hm(options)
        cmd = Oda_ha.ODACLI + 'create-database -j ' + options
        result = self.run_cmd(cmd)
        return result


    def delete_database(self, options):
        cmd = Oda_ha.ODACLI + 'delete-database -j ' + options
        result = self.run_cmd(cmd)
        return result

    def delete_dbhome(self, options):
        cmd = Oda_ha.ODACLI + 'delete-dbhome -j ' + options
        result = self.run_cmd(cmd)
        return result

    def describe_database(self,options):
        cmd = Oda_ha.ODACLI + 'describe-database -j ' + options
        result = self.ssh2node(cmd)
        d = simplejson_load(result)
        return d

    def describe_appliance(self):
        cmd = Oda_ha.ODACLI + 'describe-appliance -j '
        result = self.ssh2node(cmd)
        d = simplejson_load(result)
        return d

    def describe_system(self):
        cmd = Oda_ha.ODACLI + 'describe-system -j '
        result = self.ssh2node (cmd)
        d = simplejson_load (result)
        return d


    def describe_dbhome(self,options):
        cmd = Oda_ha.ODACLI + 'describe-dbhome -j ' + options
        result = self.ssh2node(cmd)
        d = simplejson_load(result)
        return d

    def update_database(self, options):
        options = cf.change_hbp(options)
        cmd = Oda_ha.ODACLI + 'update-database -j ' + options
        result = self.run_cmd(cmd)
        return result

    def create_backup(self, options):
        cmd = Oda_ha.ODACLI + 'create-backup -j ' + options
        result = self.run_cmd(cmd)
        return result


    def disable_auto_backup(self):
        cmd = Oda_ha.ODACLI + "list-schedules |grep backup| awk '{print $1}'"
        result = self.ssh2node(cmd)
        if not result:
            logger.info("no auto backup schedules!")
            return 0
        result1 = result.split()
        for i in result1:
            d_cmd = Oda_ha.ODACLI + "update-schedule -i %s -d" % i
            self.ssh2node(d_cmd)
        else:
            return 1

    def delete_backupconfig(self, options):
        cmd = Oda_ha.ODACLI + 'delete-backupconfig -j ' + options
        result = self.run_cmd(cmd)
        return result

    def create_backupconfig(self, options):
        cmd = Oda_ha.ODACLI + 'create-backupconfig -j ' + options
        result = self.run_cmd(cmd)
        return result

    def describe_backupconfig(self, options):
        cmd = Oda_ha.ODACLI + 'describe-backupconfig -j ' + options
        result = self.ssh2node(cmd)
        d = simplejson_load(result)
        return d

    def create_objectstoreswift(self, options):

        url_oss = "https://swiftobjectstorage.us-phoenix-1.oraclecloud.com/v1"
        tenant_name_oss = "dbaasimage"
        user_name_oss = 'chunling.qin@oracle.com'
        password_oss = 'wgT.ZM&>U6Tmm#F]O&9n'


        # url_oss = "https://storage.oraclecorp.com/v1"
        # tenant_name_oss = "Storage-vidsunda"
        # user_name_oss = 'vidsunda.Storageadmin'
        # password_oss = 'Objwelcome1'

        op = "-n %s -e %s -p -t %s -u %s" % (options, url_oss,tenant_name_oss, user_name_oss)
        cmd = Oda_ha.ODACLI + 'create-objectstoreswift -j ' + op
        result = self.run_cmd(cmd, input="%s" % password_oss )
        return result

    def delete_objectstoreswift(self, options):
        cmd = Oda_ha.ODACLI + 'delete-objectstoreswift -j ' + options
        result = self.run_cmd(cmd)
        return result

    def describe_objectstoreswift(self, options):
        cmd = Oda_ha.ODACLI + 'describe-objectstoreswift -j ' + options
        result = self.ssh2node(cmd)
        d = simplejson_load(result)
        return d

    def describe_backupreport(self, options):
        cmd = Oda_ha.ODACLI + 'describe-backupreport -j ' + options
        result = self.ssh2node(cmd)
        return result

    def dbnametodbhome(self, dbname):
        d = self.describe_database("-in %s" %dbname)
        dbhomeid = d['dbHomeId']
        dbhome = self.describe_dbhome("-i %s" %dbhomeid)
        return dbhome['dbHomeLocation']

    def racuser(self):
        #cmd = "ls -ld /u01/app/*/product/*/dbhome_*|awk '{print $3}'|uniq"
        cmd = "ls -l /home |grep ^d|awk '{print $9}'"
        result = self.ssh2node(cmd).split()
        giuser = self.griduser()
        if len(result) == 1 and result[0] == giuser:
            return giuser
        elif len(result) == 3:
            result.remove(giuser)
            result.remove("oracle")
            return result[0]
        elif len(result) == 2:
            result.remove(giuser)
            return result[0]
        else:
            logger.error("Could not find rac user!")
            sys.exit(0)


    # def griduser(self):
    #     cmd = "ls /u01/app/1*/|tail -n 1"
    #     result = self.ssh2node(cmd)
    #     return result

    def griduser(self):
        crs_home = self.gi_home()
        cmd2 = "ls -l %s/bin/oracle | awk '{print $3}'" % crs_home
        grid = self.ssh2node(cmd2)
        return grid

    def gi_home(self):
        cmd = "cat /etc/init.d/init.ohasd|grep ORA_CRS_HOME=|awk -F= '{print $2}'"
        crs_home = self.ssh2node (cmd)
        return crs_home


    def gridgroup(self):
        griduser = self.griduser()
        cmd = "ls -ld /home/%s|awk '{print $4}'" % griduser
        result = self.ssh2node(cmd)
        return result


    def racgroup(self):
        racuser = self.racuser()
        cmd = "ls -ld /home/%s|awk '{print $4}'" % racuser
        result = self.ssh2node(cmd)
        return result


    def dbnametoinstance(self, dbname):
        cmd = """ps -ef|egrep "ora_pmon_%s[12_]*$" |grep -v grep|awk '{print $8}'""" % dbname
        result = self.ssh2node(cmd)
        return result[9:]

    def asminstance(self):
        cmd = "ps -ef | grep -v grep | egrep asm_pmon | awk '{print $8;}' | cut -d'_' -f3"
        result = self.ssh2node(cmd)
        return result

    def recover_database(self, options):
        options = cf.change_hp (options)
        cmd = Oda_ha.ODACLI + 'recover-database -j ' + options
        result = self.run_cmd(cmd)
        return result


    def describe_component(self):
        cmd = Oda_ha.ODACLI + 'describe-component'
        logger.info(cmd)
        result = self.ssh2node(cmd)
        return result

    def update_repository(self, options):
        cmd = Oda_ha.ODACLI + 'update-repository -j ' + options
        result = self.run_cmd(cmd)
        return result


    def update_dcsagent(self, options):
        cmd = Oda_ha.ODACLI + 'update-dcsagent -j ' + options
        logger.info(cmd)
        result, error = self.ssh2node_job(cmd)
        if error:
            logger.error(error)
            return 0
        else:
            logger.info(result)
        time.sleep(600)
        try:
            jobid = re.search('jobId.*"(\S+)"', result).group(1)
        except Exception as e:
            logger.error("Could not find the jobid!")
            return 0

        if not jobid:
            return 0
        cmd1 = Oda_ha.ODACLI + "describe-job -j -i %s" % jobid
        while True:
            tasks, err = self.ssh2node_job(cmd1)
            if err:
                logger.error(err)
                return 0
            a = simplejson_load(tasks)
            job_status = a['status']
            if job_status.lower() == 'success':
                return 1
            elif job_status.lower() == 'running':
                time.sleep(10)
            else:
                logger.error("job failed!")
                return 0


    def update_dcsadmin(self, options):
        cmd = Oda_ha.ODACLI + "update-dcsadmin -j " + options
        result = self.run_cmd(cmd)
        return result


    def update_dcscomponents (self, options):
        cmd = Oda_ha.ODACLI + "update-dcscomponents  -j " + options
        result = self.run_cmd(cmd)
        return result

    def update_server(self, options):
        cmd = Oda_ha.ODACLI + 'update-server -j ' + options
        result = self.run_cmd(cmd)
        return result

    def update_storage(self, options):
        cmd = Oda_ha.ODACLI + 'update-storage -j ' + options
        result = self.run_cmd(cmd)
        return result

    def create_appliance(self, options):
        s_v = self.system_version()
        a = cf.trim_version(s_v)
        if a not in self.old_version:
            result = self.create_appliance_new(options)
        else:
            cmd = Oda_ha.ODACLI + 'create-appliance -j ' + options
            result = self.run_cmd(cmd)
        return result

    def create_appliance_new(self,options):
        log_stamp = datetime.datetime.today ().strftime ("%Y%m%d")
        logname = "create_appliance_%s_%s.log" % (self.hostname,log_stamp)
        logfile = os.path.join (cf.log_dir, logname)
        fout = open (logfile, 'wb')
        cmd = "ssh -o UserKnownHostsFile=/dev/null %s" % (self.hostname)
        child = pexpect.spawn (cmd,logfile = fout)
        child = cf.login (child, self)
        cmd1 = Oda_ha.ODACLI + 'create-appliance -j ' + options
        child.sendline (cmd1)
        i = child.expect (["Enter an initial password for Web Console account", pexpect.TIMEOUT], timeout= 300)
        if i == 0:
            child.sendline ("%s" % self.newpassword)
            child.expect ("Confirm the password for Web Console account")
            child.sendline ("%s" % self.newpassword)
        time.sleep(120)
        child.close ()
        fout.close()
        jobid_cmd = Oda_ha.ODACLI + "list-jobs|grep 'Provisioning service creation'|awk '{print $1}'"
        jobid, err = self.ssh2node_input(jobid_cmd)
        if not jobid:
            return 0
        time.sleep (60)
        cmd1 = Oda_ha.ODACLI + "describe-job -j -i %s" % jobid
        while True:
            tasks, err = self.ssh2node_job (cmd1)
            if err:
                logger.error (err)
                sys.exit (0)

            # job_status = re.findall('Status:\s*(\S+)', tasks)[0]
            a = simplejson_load (tasks)
            job_status = a['status']
            if job_status.lower () == 'success':
                return 1
            elif job_status.lower () in ('running', "waiting"):
                time.sleep (5)
            else:
                logger.error ("job fail!\n")
                return 0



    def update_dbhome(self, options):
        cmd = Oda_ha.ODACLI + 'update-dbhome -j ' + options
        result = self.run_cmd(cmd)
        return result

    def extend_u01(self):
        cmd1 = "df -h /u01|awk 'NR>2 {print $1}'"
        result = self.ssh2node(cmd1)
        if not result:
            cmd2 = "df -h /u01|awk 'NR>1 {print $2}'"
            result = self.ssh2node(cmd2)
        result1 = re.search('(\d+)', result).group()
        if int(result1) < 100:
            cmd2 = "lvextend -L +100G /dev/VolGroupSys/LogVolU01;resize2fs /dev/VolGroupSys/LogVolU01"
            self.ssh2node(cmd2)

    def extend_opt(self):
        cmd1 = "df -h /opt|awk 'NR>2 {print $1}'"
        result = self.ssh2node(cmd1)
        if not result:
            cmd2 = "df -h /opt|awk 'NR>1 {print $2}'"
            result = self.ssh2node(cmd2)
        result1 = re.search('(\d+)', result).group()
        if int(result1) < 60:
            cmd2 = "lvextend -L +60G /dev/VolGroupSys/LogVolOpt;resize2fs /dev/VolGroupSys/LogVolOpt"
            self.ssh2node(cmd2)


    def crs_status(self):
        self.scp2node('/chqin/new_test/venv/stats.sh','/tmp/stats.sh')
        cmd = 'sh /tmp/stats.sh'
        result = self.ssh2node(cmd)
        return result

    def create_dbhome(self, options):
        cmd = Oda_ha.ODACLI + 'create-dbhome -j ' + options
        result = self.run_cmd(cmd)
        return result

    def delete_dbhome(self, options):
        cmd = Oda_ha.ODACLI + 'delete-dbhome -j ' + options
        result = self.run_cmd(cmd)
        return result

    def create_dbstorage(self, options):
        cmd = Oda_ha.ODACLI + 'create-dbstorage -j ' + options
        result = self.run_cmd(cmd)
        return result

    def delete_dbstorage(self, options):
        cmd = Oda_ha.ODACLI + 'delete-dbstorage -j ' + options
        result = self.run_cmd(cmd)
        return result

    def describe_dbstorage(self, options):
        cmd = Oda_ha.ODACLI + 'describe-dbstorage -j ' + options
        result = self.ssh2node(cmd)
        d = simplejson_load(result)
        return d

    def decribe_cpucore(self):
        cmd = Oda_ha.ODACLI + 'describe-cpucore -j '
        result = self.ssh2node(cmd)
        d = simplejson_load(result)
        return d

    def update_cpucore(self, options):
        cmd = Oda_ha.ODACLI + 'update-cpucore -j ' + options
        result = self.run_cmd(cmd)
        return result

    def update_agentproxy(self):
        cmd = Oda_ha.ODACLI + 'update-agentconfig-parameters -n HttpProxyHost -v 148.87.19.20  -n HttpProxyPort -v 80 -u -j'
        result = self.run_cmd(cmd)
        return result

    def clone_database(self, options):
        options = cf.change_hm(options)
        cmd = Oda_ha.ODACLI + 'clone-database -j ' + options
        result = self.run_cmd(cmd)
        return result

    def create_logcleanjob(self, options):
        cmd = Oda_ha.ODACLI + 'create-logcleanjob -j ' + options
        result = self.run_cmd(cmd)
        return result

    def update_osconfigurations(self):
        cmd = Oda_ha.ODACLI + 'update-osconfigurations -j '
        result = self.run_cmd(cmd)
        return result

    def create_prepatchreport(self, options):
        cmd = Oda_ha.ODACLI + 'create-prepatchreport -v %s -j ' % Oda_ha.Current_version + options
        result = self.run_cmd (cmd)
        return result

    def delete_prepatchreport(self, options):
        cmd = Oda_ha.ODACLI + 'delete-prepatchreport -j '+ options
        result = self.simple_run (cmd)
        return result

    def modify_database(self, options):
        cmd = Oda_ha.ODACLI + 'modify-database -j ' + options
        result = self.run_cmd (cmd)
        return result


    def simple_run(self, cmd):
        result, error = self.ssh2node_job (cmd)
        p = re.compile ("^DCS-1.*not found.$", re.IGNORECASE)
        if error:
            if p.match(error):
                logger.info(cmd + "\n" + error)
            else:
                logger.error (cmd + "\n" + error)
            flag = 0
        else:
            logger.info (cmd + "\n" + result)
            flag = 1
        return flag

    def configure_asr(self, options):
        cmd = Oda_ha.ODACLI + 'configure-asr -j ' + options
        result = self.run_cmd(cmd)
        return result

    def delete_asr(self):
        cmd = Oda_ha.ODACLI + 'delete-asr -j '
        result = self.run_cmd(cmd)
        return result

    def describe_asr(self):
        cmd = Oda_ha.ODACLI + 'describe-asr -j '
        result = self.ssh2node(cmd)
        d = simplejson_load(result)
        return d

    def test_asr(self):
        cmd = Oda_ha.ODACLI + 'test-asr -j '
        result = self.run_cmd(cmd)
        return result

    def update_asr(self, options):
        cmd = Oda_ha.ODACLI + 'update-asr -j ' + options
        result = self.run_cmd(cmd)
        return result

    def upgrade_database(self, options):
        cmd = Oda_ha.ODACLI + 'upgrade-database -j ' + options
        result = self.run_cmd(cmd)
        return result

    def irestore_database(self, options):
        options = cf.change_hm(options)
        options = cf.change_hbp(options)
        cmd = Oda_ha.ODACLI + 'irestore-database -j ' + options
        result = self.run_cmd(cmd,bkpassword=self.newpassword)
        return result

    def stop_tfa(self):
        cmd = "/etc/init.d/init.tfa stop"
        logger.info(cmd)
        result1 = self.ssh2node(cmd)
        logger.info(result1)
        if self.is_ha_not():
            node2 = cf.node2_name (self.hostname)
            host2 = Oda_ha(node2, "root", "welcome1")
            result2 = host2.ssh2node(cmd)
            logger.info(result2)





