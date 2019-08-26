# ------------------------------------------------------------------#
# Service: gin-proc
# Project: GIN - https://gin.g-node.org
# Documentation: https://github.com/G-Node/gin-proc/blob/master/docs
# Package: Logger
# ------------------------------------------------------------------#


import logging
import os

from datetime import datetime


def level():

    if 'DEBUG' in os.environ and os.environ['DEBUG']:
        return logging.DEBUG
    else:
        return logging.INFO


FORMAT = "%(asctime)s:%(levelname)s:%(message)s"

if 'LOG_DIR' in os.environ:

    LOG = True
    FILENAME = os.environ['LOG_DIR']

    logging.basicConfig(
        filename=FILENAME,
        format=FORMAT,
        level=level()
        )

else:
    LOG = False

    logging.basicConfig(
        format=FORMAT,
        level=level()
        )


def log(function, message):

    if LOG:
        if function == 'warning':
            logging.warning(message)
        elif function == 'debug':
            logging.debug(message)
        elif function == 'error':
            logging.error(message)
        elif function == 'critical':
            logging.critical(message)
        elif function == 'info':
            logging.info(message)
        elif function == 'exception':
            logging.exception(message)
    else:

        if function != "debug" or (
            'DEBUG' in os.environ and os.environ['DEBUG']
            ):

            print("{1}: [{0}] {2}".format(
                function.upper(),
                datetime.now(),
                message)
                )
