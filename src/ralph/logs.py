import logging

import sys
import os

def start_log(log_location, log_type, event_name=None, stream=False):
    '''
    Function that creates logs for analysts or controller.
    :param log_location: str, location of the log.
    :param log_type: str, which level of logging to initialize.
    :param event_name: str, optional, name of event assigned to the analyst
    :param stream: optional, boolean, should the log be accessible through Kubernetes?

    :return: python logger
    '''

    if (event_name != None):
        log = logging.getLogger('analyst_log')
    else:
        log = logging.getLogger('controller_log')

    if (log_type == 'debug'):
        log_level = logging.DEBUG
    elif (log_type == 'info'):
        log_level = logging.INFO
    else:
        log_level = logging.ERROR

    formatter = logging.Formatter('%(asctime)s.%(msecs)03d - %(levelname)s - %(message)s',
                                  datefmt='%Y-%m-%d %H:%M:%S')

    log.setLevel(log_level)

    if (stream):
        ch = logging.StreamHandler(stream=sys.stdout)
        ch.setLevel(log_level)
        ch.setFormatter(formatter)
        log.addHandler(ch)
    else:
        if (event_name != None):
            filename = log_location + '%s_analyst.log' % event_name
        else:
            filename = log_location + 'controller.log'

        if os.path.isdir(log_location) == False:
            os.makedirs(log_location)
        fh = logging.FileHandler(filename, encoding='utf-8')
        fh.setLevel(log_level)
        fh.setFormatter(formatter)
        log.addHandler(fh)

    log.info("Processing started. Opened log.")
        
    return log

def close_log(log):
    '''
    Function that closes a log.

    :param log: logger instance to close
    '''

    for handler in log.handlers:
        log.info('Processing complete.\n')
        if isinstance(handler, logging.FileHandler):
            handler.close()
        log.removeFilter(handler)
