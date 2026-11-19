from practice.path_tool import get_abs_path
import yaml
"""
从配置文件中获取信息
yaml.load(f, ...) —— f 是 open('config.yml') 返回的文件对象。
load 把里面的 YAML 文本解析成对应的 Python 对象：
key: value 的映射	dict
- item 的列表	    list
5432 / 3.14	        int / float
true / false	    True / False
null / 留空	        None
"""
def config_rag():
    rag_path = get_abs_path("config/rag.yml")
    with open(rag_path, 'r') as f:
        return yaml.load(f, Loader=yaml.FullLoader)
def config_agent():
    agent_path = get_abs_path("config/agent.yml")
    with open(agent_path, 'r') as f:
        return yaml.load(f, Loader=yaml.FullLoader)
def config_chroma():
    chroma_path = get_abs_path("config/chroma.yml")
    with open(chroma_path, 'r') as f:
        return yaml.load(f, Loader=yaml.FullLoader)
def config_prompts():
    prompts_path = get_abs_path("config/prompts.yml")
    with open(prompts_path, 'r') as f:
        return yaml.load(f, Loader=yaml.FullLoader)
rag_config = config_rag()
agent_config = config_agent()
chroma_config = config_chroma()
prompts_config = config_prompts()
