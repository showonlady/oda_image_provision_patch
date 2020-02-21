#!/usr/bin/env python


"""
Usage:
    unified_auditing.py -h
    unified_auditing.py -s <servername> [-u <username>] [-p <password>]


Options:
    -h,--help       Show this help message
    -s <servername>  hostname of machine, if vlan,use ip instead
    -u <username>  username [default: root]
    -p <password>  password [default: welcome1]
"""

from docopt import docopt
import re,os,sys
import oda_lib
import common_fun as cf
import initlogging
import logging
import random
import create_multiple_db as c_m_d
#from backup_recovery import create_bk_op_oss
import backup_recovery

def create_db(host):
    for i in host.db_versions:
        if not c_m_d.is_clone_exists_or_not(host, i):
            c_m_d.scp_unpack_clone_file(host, i)
        options = db_op(host,i)
        for j in options:
            dbname = cf.generate_string(cf.string1, 8)
            db_options = j + " -n %s" % dbname
            if not host.create_database (db_options):
                log.error ("database creation fail! %s" % db_options)
            else:
                if not check_uf_ad(host,dbname):
                    if re.match("11.", i):
                        log.info("The db %s with version %s is not unified auditing enable!" % (dbname,i))
                    else:
                        log.error("The db %s with version %s is not unified auditing enable!" % (dbname,i))
                else:
                    if re.match("11.", i):
                        log.error("The db %s with version %s is unified auditing enable!" % (dbname,i))
                    else:
                        log.info("The db %s with version %s is unified auditing enable!" % (dbname,i))
                backup_check(host, dbname)
                log.info("Will delete the db %s and dbhome" % dbname)
                delete_database_dbhome(host, dbname)

def create_bk_op_oss(dbname):
    i = random.choice(range(4))
    if i == 0:
        a = "-bt Regular-L0 -in %s " % dbname
    elif i == 1:
        a = "-bt Regular-L1 -c Database -in %s" % dbname
    elif i == 2:
        tag = cf.generate_string(cf.string2,8)
        a = "-bt Longterm -in %s -k 1 -t %s" % (dbname, tag)
    elif i == 3:
        tag = cf.generate_string(cf.string2,8)
        a = "-bt Regular-L1 -in %s -t %s" % (dbname, tag)
    return a


def backup_check(host, dbname, dbhomeid = ''):
    flag = 1
    backup_recovery.update_hosts (host)
    if host.is_ha_not ():
        host2name = cf.node2_name (host.hostname)
        host2 = oda_lib.Oda_ha (host2name, host.username, host.password)
        backup_recovery.update_hosts (host2)
    ###set the agent proxy###
    if not host.update_agentproxy ():
        log.error ("Fail to set the agent proxy!")
        sys.exit (0)
    oss_name = cf.generate_string (cf.string2, 8)
    log.info (oss_name)
    oss_result = host.create_objectstoreswift (oss_name)
    if not oss_result:
        return 0
    op_oss = "-d ObjectStore -c chqin -on %s " % oss_name
    op = '-cr -w 1'
    bk_name = cf.generate_string (cf.string1, 8)
    bk_op = '-n %s ' % bk_name + op_oss + op
    if not host.create_backupconfig (bk_op):
        log.error ("create backup config %s fail!\n" % bk_name)
        return 0
    updatedb_op = "-in %s -bin %s -hbp WElcome12_-" % (dbname, bk_name)
    if not host.update_database (updatedb_op):
        log.error ("update db %s with backup config %s fail!\n" % (dbname, bk_name))
        return 0
    create_bk_op = create_bk_op_oss(dbname)
    if not host.create_backup(create_bk_op):
        log.error("create backup fail %s\n" % op)
        flag = 0
    host.disable_auto_backup ()
    if flag:
        log.info("Backup check succesful!")
        br = generate_backupreport(host, dbname)
        if irestore_check(host, oss_name, br, dbhomeid):
            log.info("Irestore check successful!")



def generate_backupreport(host, dbname):
    cmd1 = "/opt/oracle/dcs/bin/odacli list-backupreports|egrep -i 'Regular-|Long'|grep %s|tail -n 1|awk '{print $1}'" % dbname
    bkreport_id = host.ssh2node(cmd1)
    bkreport = host.describe_backupreport("-i %s" %bkreport_id)
    backupreport = 'backupreport.br'
    fp = open(backupreport, 'w')
    fp.write(bkreport)
    fp.close()
    remote_file = os.path.join("/tmp", os.path.basename(backupreport))
    host.scp2node(backupreport, remote_file)
    return remote_file


def check_dbstatus(host,dbname, uniqname):
    oracleuser = host.racuser()
    oracle_home = host.dbnametodbhome (dbname)
    cmd = 'su - %s -c "echo -e \\"export ORACLE_HOME=%s;\\n%s/bin/srvctl status database -d %s;\\n\\">/home/%s/check.sh;sh /home/%s/check.sh"' % (oracleuser, oracle_home,oracle_home, uniqname,oracleuser,oracleuser)
    result = host.ssh2node(cmd)+ '\n'
    log.info(cmd)
    log.info(result)

def irestore_check(host,oss_name, br, dbhomeid = ''):
    flag = 1
    #op2 = create_database_options(host)
    new_dbname = cf.generate_string(cf.string1, 8)
    uniqname = cf.generate_string(cf.string2, 20)
    resetDBID = random.choice(['-rDBID'])
    options = " -n %s -u %s -r %s -on %s -hm WElcome12_- -hbp WElcome12_- %s " % (new_dbname,uniqname,br, oss_name,resetDBID)
    if dbhomeid:
        options += " -dh %s " % dbhomeid
    if not host.irestore_database(options):
        log.error("irestore database fail %s\n" % new_dbname)
        return 0
    check_dbstatus(host,new_dbname, uniqname)
    version = host.describe_database("-in %s" % new_dbname)["dbVersion"]

    if dbhomeid:
        if check_uf_ad(host, new_dbname):
            flag = 0
            log.error ("The db %s with version %s with exising dbhomeid %s is unified auditing enable!" % (new_dbname, version, dbhomeid))
        else:
            log.info ("The db %s with version %s is not unified auditing enable!" % (new_dbname, version))
        log.info("Will delete the database %s!" % new_dbname)
        option = "-in %s" % new_dbname
        if host.delete_database (option):
            log.info ("The db %s is deleted successfully!" % new_dbname)
        else:
            log.error ("The db %s deletion fail!" % new_dbname)
    else:
        if not check_uf_ad (host, new_dbname):
            if re.match ("11.", version):
                log.info ("The db %s with version %s is not unified auditing enable!" % (new_dbname, version))
            else:
                flag = 0
                log.error ("The db %s with version %s is not unified auditing enable!" % (new_dbname, version))
        else:
            if re.match ("11.", version):
                flag = 0
                log.error ("The db %s with version %s is unified auditing enable!" % (new_dbname, version))
            else:
                log.info ("The db %s with version %s is unified auditing enable!" % (new_dbname, version))
        log.info ("Will delete the db %s and dbhome" % new_dbname)
        delete_database_dbhome (host, new_dbname)
    return flag



def delete_database_dbhome(host, dbname):
    result = host.describe_database ("-in %s" % dbname)
    if not result:
        log.error ("Describe-database return none.")
        return 0
    dbhomeid = result["dbHomeId"]
    option = "-in %s" % dbname
    if host.delete_database (option):
        log.info ("The db %s is deleted successfully!" % dbname)
    else:
        log.error ("The db %s deletion fail!" % dbname)

    if not host.delete_dbhome ("-i %s" % dbhomeid):
        log.error ("Delete dbhome %s for db %s fail!\n" % (dbhomeid, dbname))
    else:
        log.info ("Successfull delete the dbhome for db %s!" % dbname)




def check_uf_ad(host,dbname):
    sql = "SELECT VALUE FROM V\\\\\$OPTION WHERE PARAMETER = 'Unified Auditing'"
    oracle_sid = host.dbnametoinstance(dbname)
    if not oracle_sid:
        if host.is_ha_not():
            host = oda_lib.Oda_ha(cf.node2_name(host.hostname), host.username, host.password)
            oracle_sid = host.dbnametoinstance(dbname)
            if not oracle_sid:
                log.error("Could not get the db instance name for %s!" % dbname)
                sys.exit(0)
        else:
            log.error ("Could not get the db instance name for %s!" % dbname)
            sys.exit (0)
    oracle_home = host.dbnametodbhome (dbname)
    racuser = host.racuser()
    sql_file = "check_unified_auditing.sh"
    cmd = 'su - %s -c "echo -e \\"set lines 300; \\n set trimspool on; \\n %s; \\n exit;\\n\\">/home/%s/%s; export ORACLE_HOME=%s; ' \
          'export ORACLE_SID=%s; %s/bin/sqlplus -S -L / as sysdba  @/home/%s/%s"' % (racuser,sql, racuser, sql_file, oracle_home,oracle_sid, oracle_home,racuser, sql_file)
    result = host.ssh2node (cmd) + '\n'
    log.info(result)
    if re.search("true", result, re.IGNORECASE):
        return 1
    else:
        return 0

def check_exsiting_db(host):
    cmd = host.ODACLI + "list-databases|awk 'NR>3 {print $2}'"
    dbnames = host.ssh2node(cmd).split("\n")
    if dbnames:
        for i in dbnames:
            print i
            dbhomeid = host.describe_database("-in %s" %i)["dbHomeId"]
            if check_uf_ad(host, i):
                log.info("The db %s is unified auditing enable!" % i)
            else:
                log.info("The db %s is unified auditing disable!" % i)
            backup_check(host, i, dbhomeid)
    check_existing_dbhome(host)

def check_existing_dbhome(host):
    cmd = host.ODACLI + "list-dbhomes|awk 'BEGIN {IGNORECASE=1} NR>3&&$5~/Configured/{print $1}'"
    dbhomes = host.ssh2node(cmd).split("\n")
    if dbhomes:
        for i in dbhomes:
            dbname = cf.generate_string(cf.string1, 8)
            op_dbhome = home_opt(host,i) + " -n %s" % dbname
            if not host.create_database (op_dbhome):
                log.error ("database creation fail! %s" % op_dbhome)
            else:
                if check_uf_ad (host, dbname):
                    log.info ("The db %s is unified auditing enable!" % dbname)
                else:
                    log.info ("The db %s is unified auditing disable!" % dbname)
                option = "-in %s" % dbname
                if host.delete_database (option):
                    log.info ("The db %s is deleted successfully!" % dbname)
                else:
                    log.error ("The db %s deletion fail!" % dbname)


def home_opt(host, homeid):
    d = host.describe_dbhome("-i %s" % homeid)
    de = d["dbEdition"]
    version = d["dbVersion"]
    if host.is_ha_not ():
        dbtype = ['RAC', 'RACONE', 'SI']
    else:
        dbtype = ['SI']
    password = "WElcome12_-"
    type = random.choice (dbtype)
    options = "-hm %s -y %s " % (password, type)
    storage = random.choice (['ACFS', 'ASM'])
    db11class = random.choice (['OLTP', 'DSS'])
    db12class = random.choice (['OLTP', 'DSS', 'IMDB'])
    pdbname = cf.generate_string (cf.string2, 20)
    co = random.choice (["-co", "-no-co"])
    cdb = random.choice (['-c -p %s' % pdbname, '-no-c'])

    if de and de.upper() == "EE":
        if re.match ("11.2", version):
            options += "-dh %s -cl %s -r ACFS %s" % (homeid, db11class, co)
        else:
            options += "-dh %s -cl %s -r %s %s %s" % (homeid, db12class, storage, co, cdb)
    else:
        if re.match ("11.2", version):
            options += "-dh %s -r ACFS %s" % (homeid, co)
        else:
            options += "-dh %s -r %s %s %s" % (homeid, storage, co, cdb)
    return options


def db_op(host,version):
    no_de_version = ['12.1.2.8','12.1.2.8.1','12.1.2.9','12.1.2.10','12.1.2.11', '12.1.2.12','12.2.1.1']
    cdb_true_version = ['12.1.2.8','12.1.2.8.1']
    hidden_m_version = no_de_version + ["12.2.1.2", "12.2.1.3", "12.2.1.4", "18.2.1"]
    s_v = host.system_version()
    s_v = cf.trim_version(s_v)
    if s_v in no_de_version:
        appliance = host.describe_appliance()
        if not appliance:
            log.error ("Describe-appliance return none.")
            return 0
        de = appliance['SysInstance']['dbEdition']
        options = ''
    else:
        de = random.choice(['EE', 'SE'])
        options = '-de %s ' % de
    if s_v not in cdb_true_version:
        pdbname = cf.generate_string(cf.string2, 20)
        co = random.choice(["-co", "-no-co"])
        cdb = random.choice(['-c -p %s' % pdbname, '-no-c'])
    else:
        co = random.choice(["-co True", "-co False"])
        cdb = random.choice(["-c True","-c False"])

    password = "WElcome12_-"
    options += "-hm %s " % password

    if host.is_ha_not():
        dbtype = ['RAC', 'RACONE', 'SI']
    else:
        dbtype = ['SI']
    storage = random.choice(['ACFS', 'ASM'])
    db11class = random.choice(['OLTP','DSS'])
    db12class = random.choice(['OLTP','DSS','IMDB'])

    if de == "SE":
        if re.match ("11.2", version):
            options += "-v %s -r ACFS %s" % (version,co)
        else:
            options += "-v %s -r %s %s %s" % (version, storage, co, cdb)
    elif de == "EE":
        if re.match ("11.2", version):
            options += "-v %s -cl %s -r ACFS %s" % (version, db11class, co)
        else:
            options += "-v %s -cl %s -r %s %s %s" % (version, db12class, storage, co, cdb)
    op = []
    for i in range(len(dbtype)):
        op.append(options + " -y %s" % dbtype[i])
    return op

def initlog(plog):
    oda_lib.initlog(plog)
    c_m_d.initlog(plog)
    backup_recovery.initlog(plog)
    global log
    log = plog

def log_management(hostname):
    global logfile
    logname = "check_unified_auditing_%s.log" % hostname
    logfile = os.path.join (cf.log_dir, logname)
    log = initlogging.initLogging ("unified_auditing", logfile, logging.WARN, logging.DEBUG)
    initlog(log)


if __name__ == '__main__':
    arg = docopt(__doc__)
    print arg
    hostname = arg['-s']
    username = arg['-u']
    password = arg['-p']
    log_management(hostname)
    host = oda_lib.Oda_ha(hostname, username, password)
    if host.is_patch_or_not():
        check_exsiting_db(host)
        create_db(host)
    else:
        create_db(host)
    print "Done, please check the log %s for details!" % logfile