# coding: utf-8
# Date 2021-03-11 10:44:21

import os
import sys
import logging
import logging.config
from log import log_conf

LOG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")

try:
    if not os.path.exists(LOG_PATH):
        os.makedirs(LOG_PATH)
except Exception as e:
    print("log目录文件初始化失败%s" % e)
    sys.exit(1)


def get_logger(log_name="data", log_path=LOG_PATH):
    """
    :param log_name: 只提供data(debug) 和 mail(Critical)
    :param log_path: 默认目录为hik-log
    :return:
    """
    try:
        logging.config.dictConfig(log_conf.logging_conf(log_path))
    except Exception as e:
        print('日志初始化失败[%s]' % e)
        sys.exit(1)
    logger = logging.getLogger(log_name)

    return logger