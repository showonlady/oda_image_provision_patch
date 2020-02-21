"""
Usage:
    provision.py -h
    provision.py  -m <mode> -n <name>


Options:
    -h  Show this help message
    -m <mode>  full, partial
    -n <name> name prefix
"""



import os
import time
from docopt import docopt

import simplejson
import sys
import random
from typing import Any

Ash_module = ' launch-db-system -k "$(cat /root/bmc-client/id_rsa.pub)" --image IMAGE -dv NUM -ad $AD1 -sn $SUBNET1_AD1 -s %s  ' \
             '-N CDCVMDBNAME-VERSION -e %s -d $DOMAIN11 --compartment $OPC_COMPARTMENT --agent-url AGENT ' \
             '--agent-md5 MD5 --initialSizeInGB 256 --nodeCount %s -P WWelcome11## -n NAME-VERSION > VMDB/CDCVMDBNAME-VERSION'
s = 'java -Djavax.net.ssl.trustStore=trust.jks -Dsun.net.http.allowRestrictedHeaders=true ' \
    '-Dhttp.proxyHost=www-proxy-adcq7-new.us.oracle.com -Dhttp.proxyPort=80 -jar target/bmc-client-0.6-SNAPSHOT.jar '
SourceFile = 'source /root/bmc-client/vmdb-new.sh; '

file = open('provision.json')
json = simplejson.load(file)
version = json['version']
imageagent = json['image_agent']

shape_rac = ['VM.Standard1.2', 'VM.Standard1.4', 'VM.Standard1.8','VM.Standard1.16']
shape_si = ['VM.Standard1.1', 'VM.Standard1.2', 'VM.Standard1.4', 'VM.Standard1.8','VM.Standard1.16']

edition = ['ENTERPRISE_EDITION', 'ENTERPRISE_EDITION_HIGH_PERFORMANCE', 'STANDARD_EDITION',
           'ENTERPRISE_EDITION_EXTREME_PERFORMANCE']

def short_edition(edition):
    if edition == 'ENTERPRISE_EDITION':
        return 'EE'
    elif edition == 'ENTERPRISE_EDITION_EXTREME_PERFORMANCE':
        return 'XE'
    elif edition == 'ENTERPRISE_EDITION_HIGH_PERFORMANCE':
        return 'HE'
    elif edition == 'STANDARD_EDITION':
        return 'SE'

hostname = []

def add_to_hostname(hn):
    global hostname
    hostname.append(hn)


def general_change():
    global Ash_module
    Ash_module = Ash_module.replace('NAME', name)
    Ash_module = Ash_module.replace('IMAGE', imageagent['image'])
    Ash_module = Ash_module.replace('MD5', imageagent['agentmd5'])
    Ash_module = Ash_module.replace('AGENT', imageagent['agent'])


def change(mode):
    cmd_group=[]
    si_iter_sp = 0
    si_iter_ed = 0
    rac_iter_sp = 0
    random.shuffle(shape_si)
    random.shuffle(shape_rac)

    for ver in version.keys():
        cmd = Ash_module
        cmd = cmd.replace('NUM', version[ver])
        if 'SI' in ver:
            if mode.lower() == 'full':
                for edi in edition:
                    cmdsi = cmd.replace('VERSION', ver + short_edition(edi))
                    try:
                        sp = shape_si[si_iter_sp]
                    except:
                        si_iter_sp = 0
                        sp = shape_si[si_iter_sp]
                    si_iter_sp = si_iter_sp + 1
                    node = '1'
                    cmdsi = cmdsi %(sp,edi,node)
                    cmd_group.append(cmdsi)
                    add_to_hostname(name + '-' + ver + short_edition(edi))
            elif mode.lower() == 'partial':
                try:
                    edi = edition[si_iter_ed]
                except:
                    si_iter_ed = 0
                    edi = edition[si_iter_ed]
                si_iter_ed = si_iter_ed + 1
                cmdsi = cmd.replace('VERSION', ver + short_edition(edi))
                add_to_hostname(name +'-'+ ver + short_edition(edi))
                try:
                    sp = shape_si[si_iter_sp]
                except:
                    si_iter_sp = 0
                    sp = shape_si[si_iter_sp]
                node = '1'
                cmdsi = cmdsi % (sp, edi, node)
                cmd_group.append(cmdsi)
                if short_edition(edi) != 'SE':
                    cmdsi_se = cmdsi.replace(edi, 'STANDARD_EDITION')
                    cmdsi_se = cmdsi_se.replace(ver + short_edition(edi),ver + 'SE')
                    cmd_group.append(cmdsi_se)
                    add_to_hostname(name +'-'+ ver  + 'SE')
                else:
                    edi2=random.choice(edition)
                    cmdsi_nse = cmdsi.replace(edi, edi2)
                    cmdsi_nse = cmdsi_nse.replace(ver + short_edition(edi),ver + short_edition(edi2))
                    cmd_group.append(cmdsi_nse)
                    add_to_hostname(name + '-' + ver + short_edition(edi2))
            else:
                print 'mode is full/partial'
                sys.exit()

        if 'RAC' in ver:
            edi = 'ENTERPRISE_EDITION_EXTREME_PERFORMANCE'
            cmdrac = cmd.replace('VERSION', ver)
            try:
                sp = shape_rac[rac_iter_sp]
            except:
                rac_iter_sp = 0
                sp = shape_si[rac_iter_sp]
            node = '2'
            cmdrac = cmdrac %(sp,edi,node)
            cmd_group.append(cmdrac)
            add_to_hostname(name + '-' + ver + short_edition(edi))
            rac_iter_sp = rac_iter_sp + 1
    return cmd_group


def execute_launch_cmd(launch_cmd_list):
    for cmd in launch_cmd_list:
        os.popen(SourceFile + s + cmd)
        time.sleep(300)
        print cmd


if __name__ == '__main__':
    arg = docopt(__doc__)
    global mode
    global name
    mode = arg['-m']
    name = arg['-n']
    general_change()
    launch_cmd_list = change(mode)
    execute_launch_cmd(launch_cmd_list)
    print hostname
