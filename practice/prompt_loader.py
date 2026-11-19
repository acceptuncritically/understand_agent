import config
from practice import logger
from read_config import prompts_config
from practice.path_tool import get_abs_path
def prompt_loader():
    try:
        prompt_path=get_abs_path(prompts_config["main_prompts"])
    except KeyError as e:
        message=(f"{prompt_path}不存在\n"
                 f"请检查{prompts_config['main_prompts']}路径是否正确")
        logger.error(message)
        raise FileNotFoundError(message)
    with open(prompt_path,"r",encoding="utf-8") as f:
        return f.read().strip()
