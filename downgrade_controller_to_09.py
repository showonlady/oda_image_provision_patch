#!/usr/bin/env python
#coding utf-8

"""
Usage:
    downgrade_controller_to_09.py  -s <servername> [-u <username>] [-p <password>]
    downgrade_controller_to_09.py  -s <servername> [-u <username>] [-p <password>]

Options:
    -h,--help       Show this help message
    -v,--version     Show version
    -s <servername>  hostname of machine, if vlan,use ip instead
    -u <username>  username [default: root]
    -p <password>  password [default: welcome1]
"""

from docopt import docopt
import oda_lib
import common_fun as cf
import os,sys

scripts  = "/home/chqin/qcl/scripts/chunling/TBD/downgrade_controller_09.sh"
remote_dir = "/tmp"

def main(host):
    scp_script_to_host(host, scripts)
    remote_file = os.path.join (remote_dir, os.path.basename (vm_script))
    cmd = "sh %s" % remote_file
    print cmd
    result = host.ssh2node (cmd)
    print result
    sys.stdout.flush ()

def scp_script_to_host(host, scripts):
    remote_file = os.path.join(remote_dir, os.path.basename(scripts))
    host.scp2node(scripts, remote_file)

if __name__ == '__main__':
    arg = docopt(__doc__)
    print arg
    hostname = arg['-s']
    username = arg['-u']
    password = arg['-p']
    host = oda_lib.Oda_ha(hostname, username, password)
    main(host)