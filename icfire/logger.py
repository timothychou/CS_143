"""
icfire.logger
~~~~~~~~~~~

Literally just log stuff

"""

logfile = open('out4all.txt', 'w')


def log(msg):
    logfile.write(msg + '\n')
