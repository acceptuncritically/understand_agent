from datetime import datetime

from practice.read_config import agent_config
from practice.path_tool import get_abs_path
import os
import logging
import sys
#不存在就第一次建立目录
log_path=get_abs_path(agent_config["log_path"])
os.makedirs(log_path, exist_ok=True)

LOG_FORMAT=logging.Formatter(
    '%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s')

def get_logger(name:str="practice"):
    # 按照name去注册表中查找logger，有就返回没有就登记
    logger=logging.getLogger(name)
    #将阀门开到最大
    logger.setLevel(logging.DEBUG)
    #防止重复添加handler:
    if logger.handlers:
        return logger

    """
    logging.StreamHandler(...)	    类名固定
    sys.stdout	                    表示输出到标准输出，这是 sys 模块的属性（也可换成 sys.stderr）
    .setLevel(logging.INFO)	        方法名 + 级别常量固定
    .setFormatter(...)	            方法名固定
    logger.addHandler(...)	        方法名固定
    logging.INFO	                日志级别常量，还有 DEBUG/WARNING/ERROR/CRITICAL"""
    #出口A控制台，只看info及其以上
    #默认写stderr，这里明确指定stdut:powershell 里面的输出顺序更加紧密
    console_handler=logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    #日志的输出样貌，以LOG_FORMAT格式
    console_handler.setFormatter(LOG_FORMAT)
    logger.addHandler(console_handler)
    #出口B文件，看所有
    #在log_path的目录下，以当practice.log的文件
    log_file=os.path.join(log_path,f"{datetime.now().strftime('%Y-%m-%d')}.log")
    file_handler=logging.FileHandler(log_file,encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(LOG_FORMAT)
    logger.addHandler(file_handler)
    return logger
