#! /usr/bin/env python
# encoding utf-8
import logging, os
import logging.handlers

def initLogging(loggername, logfile,  clevel=logging.WARN, Flevel=logging.DEBUG):
    logger = logging.getLogger(loggername)
    logger.setLevel(logging.DEBUG)
    LOG_FORMAT = "%(asctime)s-%(name)s-[%(module)s][%(lineno)d] %(levelname)s:  %(message)s"
    #LOG_FORMAT = '%(asctime)s %(name)s %(levelname)s: %(message)s'
    fmt = logging.Formatter(LOG_FORMAT, '%Y-%m-%d %H:%M:%S')
    sh = logging.StreamHandler()
    sh.setFormatter(fmt)
    sh.setLevel(clevel)
    fh = logging.handlers.TimedRotatingFileHandler(logfile, when='D', interval=1)
    fh.suffix = "%Y-%m-%d.log"
    fh.setFormatter(fmt)
    fh.setLevel(Flevel)
    logger.addHandler(sh)
    logger.addHandler(fh)
    return logger

# class initLogging:
#     def __init__(self, loggername, logfile, clevel=logging.WARN, Flevel=logging.DEBUG):
#         self.logger = logging.getLogger(loggername)
#         self.logger.setLevel(logging.DEBUG)
#
#         LOG_FORMAT = '%(asctime)s %(name)s %(levelname)s: %(message)s'
#         fmt = logging.Formatter(LOG_FORMAT, '%Y-%m-%d %H:%M:%S')
#         sh = logging.StreamHandler()
#         sh.setFormatter(fmt)
#         sh.setLevel(clevel)
#         fh = logging.handlers.TimedRotatingFileHandler(logfile, when='D',interval=1)
#         fh.suffix = "%Y-%m-%d.log"
#         fh.setFormatter(fmt)
#         fh.setLevel(Flevel)
#         self.logger.addHandler(sh)
#         self.logger.addHandler(fh)
#
#     def debug(self, message):
#         self.logger.debug(message)
#
#     def info(self, message):
#         self.logger.info(message)
#
#     def war(self, message):
#         self.logger.warn(message)
#
#     def error(self, message):
#         self.logger.error(message)
#
#     def cri(self, message):
#         self.logger.critical(message)


if __name__ == '__main__':


    logyyx = initLogging("test", "yyx.log")
    logyyx.debug('deg')
    logyyx.info('info')
    logyyx.warn('warning')
    logyyx.error('error')
    logyyx.critical('critical')