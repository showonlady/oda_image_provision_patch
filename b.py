import pexpect,time,sys
def sendCommt():
    demo = open("result.txt", "ab")
    demo.write('==========Log Tile: demo==========\n')
    print user
    child = pexpect.spawn('ssh %s@%s' % (user,ip))
    while True:
        i = child.expect(patterns)
        if i == CONTINUES:
            child.sendline(flag)
        elif i == PASSWD:
            child.sendline(passwd)
        elif i == OPFLAG:
            break
    for cmd in cmds:
        child.logfile = demo
        #child.expect(".*#")
        child.sendline(cmd)
        index = child.expect ([pexpect.EOF, ".*#",pexpect.TIMEOUT], timeout = 600)
        if index == 1:
            print "success"
        elif index == 2:
            print "fail"
        else:
            print "hahah"
    # for cmd in cmds:
    #     time.sleep(2)
    #     p = pexpect.spawn(cmd)
    #     p.logfile = demo
    #     p.write('=====================\n')
    #     index = p.expect([pexpect.EOF,".*#"])
    #     if index == 1:
    #         print "success"
    #     else:
    #         print cmd
    demo.close()
    child.close()

if __name__ == '__main__':
    user = 'root'
    ip = 'rwsoda310c1n2'
    passwd = 'welcome1'
    cmds = ['df','ls','pwd','ifconfig','date']
    patterns = ['Are you sure you want to continue connecting (yes/no)?','[Pp]assword:','#']
    CONTINUES,PASSWD,OPFLAG = range(len(patterns))
    flag = 'yes'
    group = '1'
    try:
        sendCommt()
    except pexpect.TIMEOUT:
        print "TIMEOUT"
    except pexpect.EOF:
        print "EOF"