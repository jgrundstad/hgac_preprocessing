import sys
import time
import subprocess

__author__ = 'Miguel Brown'


def date_time():
    cur = ">" + time.strftime("%c") + '\n'
    return cur


def job_manager(cmd_list=None, threads=None, interval=None):
    x = len(cmd_list)
    # cur position in command list
    cur = 0
    # completed
    comp = 0
    # initialize process list
    p = {}
    sys.stderr.write(date_time() + 'Initializing run\n')
    n = int(threads)
    if n > x:
        n = x
    for i in xrange(0, n, 1):
        p[i] = {}
        p[i]['job'] = subprocess.Popen(cmd_list[i], shell=True)
        p[i]['cmd'] = cmd_list[i]
        p[i]['status'] = 'Running'
        sys.stderr.write(cmd_list[i] + '\n')
        cur += 1
    s = 0
    j = interval  # sleep seconds between job submissions
    m = interval  # time seconds between status messages
    while comp < x:
        if s % m == 0:
            # sys.stderr.write(
            #     date_time() + 'Checking job statuses. ' + str(comp) + ' of ' + str(x) + ' completed. ' + str(
            #         s) + ' seconds have passed\n')
            for i in xrange(0, n, 1):
                check = p[i]['job'].poll()
                if str(check) == '1':
                    sys.stderr.write(
                        date_time() + 'Job returned an error while running ' + p[i]['cmd'] + '  aborting!\n')
                    for k in xrange(0, n, 1):
                        p[k]['job'].kill()
                        sys.stderr.write('Killing job ' + str(k) + '\n')
                    exit(1)
                if str(check) == '0' and p[i]['status'] != str(check):
                    comp += 1
                    p[i]['status'] = str(check)
                    if comp <= (x - n):
                        try:
                            p[i]['job'] = subprocess.Popen(cmd_list[cur], shell=True)
                            p[i]['cmd'] = cmd_list[cur]
                            p[i]['status'] = 'Running'
                            cur += 1
                            completed = comp + 1
                            sys.stderr.write(date_time() + 'Checking job statuses. ' + str(completed) + ' of ' +
                                            str(x) + ' completed. ' + str(s) + ' seconds have passed\n')
                        except:
                            sys.stderr.write(date_time() + "Tried to queue command " + p[i]['cmd'] + '\n was ' + str(
                                cur) + ' in command list, ' + str(i) + ' in queue list\n')
                            exit(1)
        s += j
        sleep_cmd = 'sleep ' + str(j) + 's'
        subprocess.call(sleep_cmd, shell=True)
    sys.stderr.write(date_time() + str(comp) + ' jobs completed\n')
    return 0
