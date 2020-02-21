#!/usr/bin/env python
#encoding utf-8
"""
Usage:
    create_multiple_db.py -h
    create_multiple_db.py -s <servername> [-u <username>] [-p <password>] [-v <dbversion>]

Options:
    -h,--help       Show this help message
    -s <servername>  hostname of machine, if vlan,use ip instead
    -u <username>  username [default: root]
    -p <password>  password [default: welcome1]
    -v <dbversion>  deversion,like 180717
"""
from docopt import docopt
import oda_lib
import random
import string
import sys
import os
import re
import common_fun as cf
import datetime
import logging
import initlogging
log_dir = cf.log_dir


dbclone={"12.1.0.2.170117" : "oda-sm-12.1.2.10.0-170205-DB-12.1.0.2.zip",
"12.1.0.2.161018" : "oda-sm-12.1.2.9.0-161116-DB-12.1.0.2.zip",
"12.1.0.2.160719" : "oda-sm-12.1.2.8.0-160809-DB-12.1.0.2.zip",
"12.1.0.2.160419" : "oda-sm-12.1.2.7.0-160601-DB-12.1.0.2.zip",
"11.2.0.4.161018" : "oda-sm-12.1.2.9.0-161007-DB-11.2.0.4.zip",
"11.2.0.4.160719" : "oda-sm-12.1.2.8.0-160817-DB-11.2.0.4.zip",
"11.2.0.4.160419" : "oda-sm-12.1.2.7.0-160601-DB-11.2.0.4.zip",
"12.1.0.2.170418" : "oda-sm-12.1.2.11.0-170503-DB-12.1.0.2.zip",
"11.2.0.4.170418" : "oda-sm-12.1.2.11.0-170503-DB-11.2.0.4.zip",
"11.2.0.4.170814_x7" : "oda-sm-12.2.1.1.0-171026-DB-11.2.0.4.zip",
"12.1.0.2.170814_x7" : "oda-sm-12.2.1.1.0-171026-DB-12.1.0.2.zip",
"12.2.0.1.170814_x7" : "oda-sm-12.2.1.1.0-171025-DB-12.2.1.1.zip",
"11.2.0.4.170814_x6" : "oda-sm-12.1.2.12.0-170905-DB-11.2.0.4.zip",
"12.1.0.2.170814_x6" : "oda-sm-12.1.2.12.0-170905-DB-12.1.0.2.zip",
"11.2.0.4.171017" : "oda-sm-12.2.1.2.0-171124-DB-11.2.0.4.zip",
"12.1.0.2.171017" : "oda-sm-12.2.1.2.0-171124-DB-12.1.0.2.zip",
"12.2.0.1.171017" : "oda-sm-12.2.1.2.0-171124-DB-12.2.0.1.zip",
"11.2.0.4.180116" : "odacli-dcs-12.2.1.3.0-180315-DB-11.2.0.4.zip",
"12.1.0.2.180116" : "odacli-dcs-12.2.1.3.0-180320-DB-12.1.0.2.zip",
"12.2.0.1.180116" : "odacli-dcs-12.2.1.3.0-180418-DB-12.2.0.1.zip",
"11.2.0.4.180417" : "odacli-dcs-12.2.1.4.0-180617-DB-11.2.0.4.zip",
"12.1.0.2.180417" : "odacli-dcs-12.2.1.4.0-180617-DB-12.1.0.2.zip",
"12.2.0.1.180417" : "odacli-dcs-12.2.1.4.0-180617-DB-12.2.0.1.zip",
"18.2.0.0.180417" : "odacli-dcs-18.2.0.0.0-180626-DB-18.0.0.0.zip",
"11.2.0.4.180717" : "odacli-dcs-18.3.0.0.0-180905-DB-11.2.0.4.zip",
"12.1.0.2.180717" : "odacli-dcs-18.3.0.0.0-180905-DB-12.1.0.2.zip",
"12.2.0.1.180717" : "odacli-dcs-18.3.0.0.0-180905-DB-12.2.0.1.zip",
"18.3.0.0.180717" : "odacli-dcs-18.3.0.0.0-180905-DB-18.0.0.0.zip",
"11.2.0.4.181016" : "odacli-dcs-18.4.0.0.0-181217.1-DB-11.2.0.4.zip",
"12.1.0.2.181016" : "odacli-dcs-18.4.0.0.0-181217.1-DB-12.1.0.2.zip",
"12.2.0.1.181016" : "odacli-dcs-18.4.0.0.0-181217.1-DB-12.2.0.1.zip",
"18.4.0.0.181016" : "odacli-dcs-18.4.0.0.0-181217.1-DB-18.4.0.0.zip",
"11.2.0.4.190115" : "odacli-dcs-18.5.0.0.0-190227-DB-11.2.0.4.zip",
"12.1.0.2.190115" : "odacli-dcs-18.5.0.0.0-190227-DB-12.1.0.2.zip",
"12.2.0.1.190115" : "odacli-dcs-18.5.0.0.0-190227-DB-12.2.0.1.zip",
"18.5.0.0.190115" : "odacli-dcs-18.5.0.0.0-190416-DB-18.5.0.0.zip",
"11.2.0.4.190416" : "odacli-dcs-18.6.0.0.0-190502-DB-11.2.0.4.zip",
"12.1.0.2.190416" : "odacli-dcs-18.6.0.0.0-190502-DB-12.1.0.2.zip",
"12.2.0.1.190416" : "odacli-dcs-18.6.0.0.0-190502-DB-12.2.0.1.zip",
"18.6.0.0.190416" : "odacli-dcs-18.6.0.0.0-190502-DB-18.6.0.0.zip",
"11.2.0.4.190716" : "odacli-dcs-18.7.0.0.0-190814-DB-11.2.0.4.zip",
"12.1.0.2.190716" : "odacli-dcs-18.7.0.0.0-190807-DB-12.1.0.2.zip",
"12.2.0.1.190716" : "odacli-dcs-18.7.0.0.0-190807-DB-12.2.0.1.zip",
"18.7.0.0.190716" : "odacli-dcs-18.7.0.0.0-190830-DB-18.7.0.0.zip",
"19.4.0.0.190716" : "odacli-dcs-19.4.0.0.0-191007-DB-19.4.0.0.zip",
"19.5.0.0.191015" : "odacli-dcs-19.5.0.0.0-191017-DB-19.5.0.0.zip",
"11.2.0.4.191015" : "odacli-dcs-18.8.0.0.0-191118-DB-11.2.0.4.zip",
"12.1.0.2.191015" : "odacli-dcs-18.8.0.0.0-191118-DB-12.1.0.2.zip",
"12.2.0.1.191015" : "odacli-dcs-18.8.0.0.0-191118-DB-12.2.0.1.zip",
"18.8.0.0.191015" : "odacli-dcs-18.8.0.0.0-191201-DB-18.8.0.0.zip"
}

d_version={
    "12.1.2.8.1": "160719",
    "12.1.2.9": "161018",
    "12.1.2.10": "170117",
    "12.1.2.11": "170418",
    "12.1.2.12": "170814",
    "12.2.1.1": "170814",
    "12.2.1.2": "171017",
    "12.2.1.3": "180116",
    "12.2.1.4": "180417",
    "18.2.1": "180417",
    "18.3": "180717",
    "18.4": "181016",
    "18.5": "190115",
    "18.6": "190416",
    "18.7": "190716",
    "19.4" : "190716",
    "19.5" : "191015",
    "18.8" : "191015"
   }
def create_multiple_db(*a):
    host = a[0]
    if len(a) == 1:
        s_v = host.system_version()
        s_v = cf.trim_version(s_v)
        version = d_version[s_v]
        log.info(version)
    else:
        version = a[1]
    version_list = db_versions(host,version)
    if len(version_list) == 0:
        sys.exit(1)
    log.info(version_list)
    for i in version_list:
        if not is_clone_exists_or_not(host, i):
            scp_unpack_clone_file(host, i)
        for j in range(2):
           op = db_op(host, i)
           if not host.create_database(op):
               log.error("database creation fail! %s" % op)




def is_clone_exists_or_not(host, version):
    b = version.split("_")
    if re.match("18.|19.", version):
        c = b[0][0:2]+b[0][-7:]
    else:
        c = b[0][0:2]+b[0][3]+b[0][-7:]
    file = "db" + c + ".tar.gz"
    cmd = "ls -l /opt/oracle/oak/pkgrepos/orapkgs/clones/%s" % file
    result = host.ssh2node(cmd)
    log.info(result)
    if re.search("No such", result):
        return 0
    else:
        return 1

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

    # if s_v in hidden_m_version:
    #     options += "-hm %s " % password
    # else:
    #     options += "-m %s " % password
    options += "-hm %s " % password

    version = version.split('_')[0]
    dbname = cf.generate_string(cf.string1, 8)



    if host.is_ha_not():
        dbtype = random.choice(['RAC', 'RACONE', 'SI'])
    else:
        dbtype = 'SI'
    storage = random.choice(['ACFS', 'ASM'])

    db11class = random.choice(['OLTP','DSS'])
    db12class = random.choice(['OLTP','DSS','IMDB'])

    if de == "SE":
        if re.match ("11.2", version):
            options += "-n %s -v %s -r ACFS -y %s %s" % (dbname, version, dbtype, co)
        else:
        # elif de == "SE" and re.match("12.|18.", version):
            options += "-n %s -v %s -r %s -y %s %s %s" % (dbname, version, storage, dbtype, co, cdb)
    elif de == "EE":
        if re.match ("11.2", version):
            options += "-n %s -v %s -cl %s -r ACFS -y %s %s" % (dbname, version, db11class, dbtype, co)
        else:
            options += "-n %s -v %s -cl %s -r %s -y %s %s %s" % (dbname, version, db12class, storage, dbtype, co, cdb)
    return options


def scp_unpack_clone_file(host,version):
    clonefile = dbclone[version]
    a = clonefile.split('-')[2]
    b = cf.trim_version(a)
    c = 'ODA'+b
    d = "/chqin/%s/oda-sm/%s" %(c,clonefile)
    if os.path.exists(d):
        remote_file = os.path.join("/tmp", os.path.basename(d))
        host.scp2node(d, remote_file)
        if host.update_repository("-f %s" % remote_file):
            host.ssh2node("rm -rf %s" % remote_file)
    else:
        log.error("there is no clone file %s under %s" % (version,d))
        sys.exit(0)




def db_versions(host, version):
    list = []
    s_v = host.system_version()
    s_v = cf.trim_version(s_v)
    if s_v == "18.2.1":
        list = ["18.2.0.0.180417"]
        return list
    if s_v == "19.4":
        list = ["19.4.0.0.190716"]
        return list

    if s_v == "19.5":
        list = ["19.5.0.0.191015"]
        return list

    if version == "170814" and host.is_x6():
        version_f = "170814_x6"
    elif version == "170814" and host.is_x7():
        version_f = "170814_x7"
    else:
        version_f = version
    for i in dbclone.keys():
        if re.search(version_f,i) and not re.match('18.2|19.4|19.5', i):
            list.append(i)
    return list


def initlogger(hostname):
    logname = "create_multiple_databases_%s.log" % hostname
    logfile = os.path.join(log_dir, logname)
    log = initlogging.initLogging("create_db", logfile, logging.WARN, logging.DEBUG)
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
    log_management(hostname)
    host = oda_lib.Oda_ha(hostname, username, password)

    if arg['-v']:
        version = arg['-v']
        create_multiple_db(host, version)
    else:
        create_multiple_db(host)







