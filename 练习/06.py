from langchain.agents import create_agent
from langchain.tools import tool
from langchain_deepseek import ChatDeepSeek
from langchain.agents.middleware import (before_model, dynamic_prompt, wrap_tool_call, ModelRequest)
import csv
import os
import sys

# Windows 控制台默认是 GBK，模型回复里偶尔带 emoji，直接 print 会抛 UnicodeEncodeError，这里兜底
sys.stdout.reconfigure(errors="replace")


REPORT_PROMPT = """你是专业的扫地机器人报告写手。请根据工具查到的使用记录，用 Markdown 输出一份报告：

1. 一级标题（#）+ 一句话概况
2. 根据数据内容自行提炼 2~4 个分析维度作为二级标题（##），每个维度下列出相关发现
3. 常见分析维度可参考：使用亮点、改进建议、清扫效率、异常记录、区域覆盖情况等，但请根据实际数据灵活选择

只依据工具返回的数据，不要编造；不要输出工具调用过程。"""

MAIN_PROMPT = """你是扫地机器人智能客服"小扫"，语气亲切，回答简短。
【报告规则】用户想生成/查看个人使用报告时，按顺序执行：
1. 如果用户还没提供用户ID，先礼貌询问用户ID，直接询问不要告诉用户id的格式，此时不要调用任何工具，更不要编造ID
2. 拿到用户ID后，先调 fill_context_for_report（报告模式开关，不调不算报告场景）
3. 再调 get_user_id，把用户提供的ID作为 custom_id 参数传入
4. 最后调 fetch_record 查询使用记录
拿到记录后给出中文建议，不要编造数据。"""
@tool(description="无入参，发现客户想要生成报告，这是生成报告前必须调用的开关")
def fill_context_for_report():
    return "已切换报告模式"
@tool(description="获取当前客户的id，custom_id 为用户在对话中提供的用户ID")
def get_user_id(custom_id:str):
    return custom_id
RECORD_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resourse", "record.csv")

@tool(description="查询用户上个月的扫地机器人使用情况")
def fetch_record(user_id:str):
    research_dict={}
    with open(RECORD_PATH, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
              research_dict[row["用户ID"]]=row
    return research_dict.get(user_id, "")
@wrap_tool_call
def monitor_tool(request,handler):
    # 把工具调用打印出来，方便看到报告模式开关和用户ID到底有没有被真正获取
    print(f"\n[工具调用] {request.tool_call['name']} 参数={request.tool_call['args']}")
    result=handler(request)
    if request.tool_call["name"]=="fill_context_for_report":
        #检测是否调用了工具，调用工具将内容转换，使得后面的模型知道当前模式
        request.runtime.context["report"]=True
    return result
@dynamic_prompt
def report_prompt_switch(request):
    is_report=request.runtime.context.get("report",False)
    return REPORT_PROMPT if is_report else MAIN_PROMPT

agent=create_agent(
    model=ChatDeepSeek(model="deepseek-chat",timeout=60),
    tools=[fetch_record,get_user_id,fill_context_for_report],
    middleware=[monitor_tool,report_prompt_switch],
)
messages=[]  # 保存完整对话（含工具调用），让 Agent 记得上一轮聊过什么
while True:
    try:
        user_input=input("User: ")
    except (EOFError,KeyboardInterrupt):
        print("\n再见！")
        break
    messages.append({"role":"user","content":user_input})
    # context 直接传 {"report": False}；每轮新建，避免报告模式残留到下一轮对话
    res=agent.invoke({"messages":messages},context={"report": False})
    messages=res["messages"]
    print(res["messages"][-1].content)
