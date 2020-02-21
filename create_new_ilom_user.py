#!/usr/bin/env python
#coding utf-8

"""
Usage:
    create_new_ilom_user.py -h
    create_new_ilom_user.py  -s <ilomhostname> [-u <ilomusername>] [-p <ilompassword>]

Options:
    -h,--help       Show this help message
    -s <ilomhostname>   hostname of ilom
    -u <ilomusername>   username [default: root]
    -p <ilompassword>   password [default: welcome1]
"""


from docopt import docopt
import common_fun as cf
import sys
import datetime

script_dir = cf.scr_dir + "/"
log_dir = cf.log_dir + "/"
ilomnewuser = "imageuser"
ilomnewpassword = "welcome1"
ilomTimeout = 10


def create_new_user(username, ilom, password, log):
    cmd = script_dir + "create_new_user3.sh %s %s %s %s %s %s %s" % (
        username, ilom, password, ilomnewuser, ilomnewpassword, log, ilomTimeout)
    print cmd
    out, err = cf.exc_cmd_new(cmd)
    if err:
        print out
        print "Create new user failed on %s!" % ilom
        sys.exit(0)

def main(hostname, username, password):
    log_stamp = datetime.datetime.today().strftime("%Y%m%d")
    log = log_dir + "create_new_user_%s.log" % log_stamp
    create_new_user(username, hostname, password, log)



if __name__ == '__main__':
    arg = docopt(__doc__)
    print arg
    hostname = arg['-s']
    password = arg['-p']
    username = arg['-u']
    main(hostname, username, password)
