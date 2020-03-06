#!/usr/bin/env python
#coding utf-8
#
# Copyright (c) 2018, Oracle and/or its affiliates. All rights reserved.
#
#    NAME
#      create_database.py
#
#    DESCRIPTION
#      Sanity check for the database commands
#
#    NOTES
#
#
#    MODIFIED   (MM/DD/YY)
#    chqin    4/15/18 - Creation
"""
Usage:
    create_database.py -h
    create_database.py -s <servername> [-u <username>] [-p <password>]

Options:
    -h,--help       Show this help message
    -s <servername>  hostname of machine, if vlan,use ip instead
    -u <username>  username [default: root]
    -p <password>  password [default: welcome1]
"""
from docopt import docopt
import oda_lib
import random
import string
import re
import common_fun as cf
import datetime
import create_multiple_db as c_m_d
import logging
import initlogging
import os

string1 = string.ascii_letters + string.digits
string2 = string.ascii_letters + string.digits + "_"

#rwsoda6f004 = oda_lib.Oda_ha('rwsoda6f004','root','welcome1')
#options = "-hm WElcome12__ -n chqin2 -v 12.1.0.2"
#result = rwsoda6f004.create_database(options)
#print result

def get_version(host):
    dbversion = []
    s_v = host.system_version()
    s_v = cf.trim_version(s_v)
    bp_version = c_m_d.d_version[s_v]
    version_list = c_m_d.db_versions(host, bp_version)
    if len(version_list) == 0:
        sys.exit(1)
    log.info(version_list)

    #db_version = ['12.2.0.1.%s' % bp_version,'12.1.0.2.%s' % bp_version,'11.2.0.4.%s' % bp_version]
    for i in version_list:
        if not c_m_d.is_clone_exists_or_not(host, i):
            c_m_d.scp_unpack_clone_file(host, i)
    for i in version_list:
        dbversion.append(i.split("_")[0])
    return dbversion



def generate_string(source, length):
    len1 = random.randint(1, length)
    cha = random.choice(string.ascii_letters)
    chb = ''.join(random.sample(source, len1-1))
    return cha+chb

def create_database_options(host):
    options = []
    de = ['SE','EE']
    db_storage = ['ASM', 'ACFS']
    #db_storage = ['ASM']
    #db_class = [ 'DSS']
    db_class = ['OLTP', 'DSS', 'IMDB']
    db11_class = ['OLTP', 'DSS']
    db_version = get_version(host)

    for edition in de:
        for version in db_version:
            if edition == 'SE':
                option = '-cl OLTP '
            elif re.search('11.2.0.4', version):
                option = '-cl %s ' % random.choice(db11_class)
            else:
                option = '-cl %s ' % random.choice(db_class)
            if re.search('11.2.0.4', version):
                a = option + "-de %s -v %s -r %s " %(edition, version, 'ACFS')
                options.append(a)
            else:
                for storage in db_storage:
                    a = option + "-de %s -v %s -r %s " %(edition, version, storage)
                    if random.choice([True, False]):
                        pdbname = generate_string(string2, 30)
                        a += '-c -p %s ' %pdbname
                    options.append(a)
    return options

def create_database_options2(host):
    options = create_database_options(host)
    options2 = []
    characterSet = ['AL32UTF8', 'AR8ADOS710', 'AR8ADOS720', 'AR8ADOS720T', 'AR8APTEC715', 'AR8APTEC715T', 'AR8ARABICMACS', 'AR8ASMO708PLUS', 'AR8ASMO8X', 'AR8HPARABIC8T', 'AR8ISO8859P6', 'AR8MSWIN1256', 'AR8MUSSAD768', 'AR8MUSSAD768T', 'AR8NAFITHA711', 'AR8NAFITHA711T', 'AR8NAFITHA721', 'AR8NAFITHA721T', 'AR8SAKHR706', 'AR8SAKHR707', 'AR8SAKHR707T', 'AZ8ISO8859P9E', 'BG8MSWIN', 'BG8PC437S', 'BLT8CP921', 'BLT8ISO8859P13', 'BLT8MSWIN1257', 'BLT8PC775', 'BN8BSCII', 'CDN8PC863', 'CEL8ISO8859P14', 'CL8ISO8859P5', 'CL8ISOIR111', 'CL8KOI8R', 'CL8KOI8U', 'CL8MACCYRILLICS', 'CL8MSWIN1251', 'EE8ISO8859P2', 'EE8MACCES', 'EE8MACCROATIANS', 'EE8MSWIN1250', 'EE8PC852', 'EL8DEC', 'EL8ISO8859P7', 'EL8MACGREEKS', 'EL8MSWIN1253', 'EL8PC437S', 'EL8PC851', 'EL8PC869', 'ET8MSWIN923', 'HU8ABMOD', 'HU8CWI2', 'IN8ISCII', 'IS8PC861', 'IW8ISO8859P8', 'IW8MACHEBREWS', 'IW8MSWIN1255', 'IW8PC1507', 'JA16EUC', 'JA16EUCTILDE', 'JA16SJIS', 'JA16SJISTILDE', 'JA16VMS', 'KO16KSC5601', 'KO16KSCCS', 'KO16MSWIN949', 'LA8ISO6937', 'LA8PASSPORT', 'LT8MSWIN921', 'LT8PC772', 'LT8PC774', 'LV8PC1117', 'LV8PC8LR', 'LV8RST104090', 'N8PC865', 'NE8ISO8859P10', 'NEE8ISO8859P4', 'RU8BESTA', 'RU8PC855', 'RU8PC866', 'SE8ISO8859P3', 'TH8MACTHAIS', 'TH8TISASCII', 'TR8DEC', 'TR8MACTURKISHS', 'TR8MSWIN1254', 'TR8PC857', 'US8PC437', 'UTF8', 'VN8MSWIN1258', 'VN8VN3', 'WE8DEC', 'WE8DG', 'WE8ISO8859P1', 'WE8ISO8859P15', 'WE8ISO8859P9', 'WE8MACROMAN8S', 'WE8MSWIN1252', 'WE8NCR4970', 'WE8NEXTSTEP', 'WE8PC850', 'WE8PC858', 'WE8PC860', 'WE8ROMAN8', 'ZHS16CGB231280', 'ZHS16GBK', 'ZHT16BIG5', 'ZHT16CCDC', 'ZHT16DBT', 'ZHT16HKSCS', 'ZHT16MSWIN950', 'ZHT32EUC', 'ZHT32SOPS', 'ZHT32TRIS', 'US7ASCII']
    dbLanuage = ["ALBANIAN", "AMERICAN", "ARABIC", "ASSAMESE", "AZERBAIJANI", "BANGLA", "BELARUSIAN", "BRAZILIAN PORTUGUESE", "BULGARIAN", "CANADIAN FRENCH", "CATALAN", "CROATIAN", "CYRILLIC KAZAKH", "CYRILLIC SERBIAN", "CYRILLIC UZBEK", "CZECH", "DANISH", "DUTCH", "EGYPTIAN", "ENGLISH", "ESTONIAN", "FINNISH", "FRENCH", "GERMAN", "GERMAN DIN", "GREEK", "GUJARATI", "HEBREW", "HINDI", "HUNGARIAN", "ICELANDIC", "INDONESIAN", "IRISH", "ITALIAN", "JAPANESE", "KANNADA", "KOREAN", "LATIN AMERICAN SPANISH", "LATIN SERBIAN", "LATIN UZBEK", "LATVIAN", "LITHUANIAN", "MACEDONIAN", "MALAY", "MALAYALAM", "MARATHI", "MEXICAN SPANISH", "NORWEGIAN", "ORIYA", "POLISH", "PORTUGUESE", "PUNJABI", "ROMANIAN", "RUSSIAN", "SIMPLIFIED CHINESE", "SLOVAK", "SLOVENIAN", "SPANISH", "SWEDISH", "TAMIL", "TELUGU", "THAI", "TRADITIONAL CHINESE", "TURKISH", "UKRAINIAN", "VIETNAMESE"]
    dbTerritory = ["ALBANIA", "ALGERIA", "AMERICA", "ARGENTINA", "AUSTRALIA", "AUSTRIA", "AZERBAIJAN", "BAHRAIN", "BANGLADESH", "BELARUS", "BELGIUM", "BRAZIL", "BULGARIA", "CANADA", "CATALONIA", "CHILE", "CHINA", "COLOMBIA", "COSTA RICA", "CROATIA", "CYPRUS", "CZECH REPUBLIC", "DJIBOUTI", "ECUADOR", "EGYPT", "EL SALVADOR", "ESTONIA", "FINLAND", "FRANCE", "FYR MACEDONIA", "GERMANY", "GREECE", "GUATEMALA", "HONG KONG", "HUNGARY", "ICELAND", "INDIA", "INDONESIA", "IRAQ", "IRELAND", "ISRAEL", "ITALY", "JAPAN", "JORDAN", "KAZAKHSTAN", "KOREA", "KUWAIT", "LATVIA", "LEBANON", "LIBYA", "LITHUANIA", "LUXEMBOURG", "MALAYSIA", "MAURITANIA", "MEXICO", "MONTENEGRO", "MOROCCO", "NEW ZEALAND", "NICARAGUA", "NORWAY", "OMAN", "PANAMA", "PERU", "PHILIPPINES", "POLAND", "PORTUGAL", "PUERTO RICO", "QATAR", "ROMANIA", "RUSSIA", "SAUDI ARABIA", "SERBIA", "SINGAPORE", "SLOVAKIA", "SLOVENIA", "SOMALIA", "SOUTH AFRICA", "SPAIN", "SUDAN", "SWEDEN", "SWITZERLAND", "SYRIA", "TAIWAN", "THAILAND", "THE NETHERLANDS", "TUNISIA", "TURKEY", "UKRAINE", "UNITED ARAB EMIRATES", "UNITED KINGDOM", "UZBEKISTAN", "VENEZUELA", "VIETNAM", "YEMEN"]
    nlsCharacterset =["AL16UTF16", "UTF8"]
    dbconsole = ['-co', '-no-co']
    levelzerobackupday = ['Monday','Tuesday', 'Wednesday','Thursday','Friday','Saturday','Sunday']
    for i in options:
        if ([True, False]):
            i +=  '-cs %s ' % random.choice(characterSet)
        if random.choice([True, False]):
            i += "-l '%s' " % random.choice(dbLanuage)
        if random.choice([True, False]):
            i += "-dt '%s' " % random.choice(dbTerritory)
        if random.choice([True, False]):
            i +=  '-ns %s ' % random.choice(nlsCharacterset)
        if random.choice([True, False]):
            i +=  '%s '% random.choice(dbconsole)
        if random.choice([True, False]):
            i +=  '-lb %s '% random.choice(levelzerobackupday)
        i += '-s odb1 '
        options2.append(i)
    return options2

def flash():
    i = ''
    flash = ['-f', '-no-f']
    flashcache = ['-fc', '-no-fc']
    if random.choice([True, False]):
        i += '%s ' % random.choice(flash)
    if random.choice([True, False]):
        i += '%s ' % random.choice(flashcache)
    return i

def dbtype():
    db_type = ['RAC','RACONE', 'SI']
    db_type_choice = random.choice(db_type)
    option = '-y %s ' % db_type_choice
    if db_type_choice != 'RAC':
        option += '-g %s ' % random.choice(['0','1'])
    return option

def describe_db_check(host, db_name):
    result = host.describe_database("-in %s" % db_name)
    return result

def compare_result(d, op):
    aa = re.findall('-cl\s+(\S+)',op)
    bb = re.findall('-de\s+(\S+)',op)
    cc = re.findall('-v\s+(\S+)',op)
    dd = re.findall('-r\s+(\S+)',op)
    ee = re.findall('-s\s+(\S+)',op)
    ff = re.findall('-g\s+(\S+)',op)
    #cc_r = '.'.join( cc[0].split('.')[0:4])
    cc_r = cc[0]
    if ff:
        db_info = [aa[0], bb[0], cc_r, dd[0], ee[0], ff[0]]
    else:
        db_info = [aa[0], bb[0], cc_r, dd[0], ee[0], '0']
    result = [d['dbClass'], d['dbEdition'], d['dbVersion'], d['dbStorage'], d['dbShape'], d['dbTargetNodeNumber']]
    if db_info == result and d['state']['status'] == 'CONFIGURED':
        return 1
    else:
        print db_info
        print result
        return 0


def delete_database(host, dbname, dbid):
    if random.choice([True, False]):
        op = "-in %s" % dbname
        #op = "-in %s -fd" % dbname

    else:
        op = "-i %s" % dbid
        #op = "-i %s -fd" % dbid
    return host.delete_database(op)



def create_database_case(host):
    options = create_database_options2(host)
    password = "WElcome12#_"
    dbname = []
    new_options = []
    # if host.is_ha_not():
    #     for i in range(0, len(options)):
    #         options[i] += dbtype()
    if host.is_ha_not():
        for i in range(0, len(options)):
            for j in ['-y RAC ','-y RACONE -g 0 ','-y RACONE -g 1 ', '-y SI -g 0 ', '-y SI -g 1 ']:
                a = options[i] + j
                new_options.append(a)
        options = new_options
    if host.is_flash():
        for i in range(0, len(options)):
            options[i] += flash()

    for i in range(0,len(options)):
        db_name = generate_string(string1, 8)
        options[i] = "-hm %s -n %s " % (password, db_name) + options[i]
        result = host.create_database(options[i])
        if result:
            dbname.append(db_name)
            log.info("create database %s successfully!\n" % db_name)
            describe_db = describe_db_check(host, db_name)
            if not describe_db:
                log.error ("Describe-db return none.")
                return 0
            dbid = describe_db['id']
            dbhomeid = describe_db['dbHomeId']
            if not compare_result(describe_db, options[i]):
                log.error("describe database %s fail!\n" % db_name)
            else:
                if not delete_database(host, db_name, dbid):
                    log.error("delete database %s fail!\n" % db_name)
                if not host.delete_dbhome("-i %s" % dbhomeid):
                    log.error("delete dbhome %s fail!\n" % dbhomeid)

        else:
            log.error("create database %s failed!" % db_name)


def delete_all_dbhomes(host):
    cmd = "/opt/oracle/dcs/bin/odacli list-dbhomes|awk 'NR>3 {print $1}'"
    home_id = host.ssh2node(cmd)
    for i in home_id.split():
        if not host.delete_dbhome("-i %s" % i):
            log.error("delete dbhome %s fail!\n" % i)


def initlogger(hostname):
    global logfile
    logname = "create_database_%s.log" % hostname
    logfile = os.path.join(cf.log_dir, logname)
    log = initlogging.initLogging("db_check", logfile, logging.WARN, logging.DEBUG)
    return log


def initlog(plog):
    oda_lib.initlog(plog)
    c_m_d.initlog(plog)
    global log
    log = plog


def log_management(hostname):
    log = initlogger(hostname)
    initlog(log)




def main(hostname, username, password):
    #logfile_name = 'check_create_database_%s.log' % hostname
    #fp, out, err,log = cf.logfile_name_gen_open(logfile_name)
    #out, err = sys.stdout, sys.stderr
    #fp = open(logfile_name_stamp, 'a')
    #sys.stdout, sys.stderr = fp, fp
    log_management(hostname)
    host = oda_lib.Oda_ha(hostname,username,password)
    create_database_case(host)
    delete_all_dbhomes(host)
    error = cf.check_log(logfile)
    return error


if __name__ == '__main__':
    arg = docopt(__doc__)
    print arg
    hostname = arg['-s']
    username = arg['-u']
    password = arg['-p']
    main(hostname, username, password)
