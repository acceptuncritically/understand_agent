"""
解决在流式输出时的假流式，去消息的最后一位表示更新的问题
"""
import random

"""values 模式下返回的结果
# 第 1 帧：只有初始用户消息
{'messages': [HumanMessage(content='deepseek股价多少，并简单介绍一下这家公司')]}

# 第 2 帧：模型决定调用工具，新增了一条 AIMessage
{'messages': [
    HumanMessage(content='deepseek股价多少，并简单介绍一下这家公司'),
    AIMessage(content='', tool_calls=[...])
]}

# 第 3 帧：工具并行执行完毕，一次性新增了两条 ToolMessage
{'messages': [
    HumanMessage(content='deepseek股价多少，并简单介绍一下这家公司'),
    AIMessage(content='', tool_calls=[...]),
    ToolMessage(content='股票deepseek的价格是20元', name='get_price'),
    ToolMessage(content='股票deepseek，是一家A股上市公司', name='get_info')
]}
"""
from langchain.agents import create_agent
from langchain_core.messages import AIMessage,ToolMessage
from langchain_deepseek import ChatDeepSeek
from langchain_core.tools import tool

@tool(description="用来获得用户当前的天气状况")
def get_weather():
    return "晴天"
@tool(description="用来获得用户所在的位置")
def get_location():
    return random.choice(["北京", "上海", "广州", "深圳"])
model=ChatDeepSeek(model="deepseek-chat",temperature=0.9)
agent=create_agent(
    tools=[get_weather,get_location],
    model=model,
    system_prompt="你是一位助手，需要帮助用户获取天气和位置信息"
)
seen,cnt=0,0
for chunk in agent.stream(
    input={"messages":[{"role":"user","content":"今天我所在的位置天气如何"}]},
    stream_mode="values",
):
    cnt+=1
    message=chunk["messages"]
    if cnt==1:
        seen=len(message)
        continue
    for msg in message[seen:]:
        if isinstance(msg,AIMessage):
            for tool_call in msg.tool_calls:
                print(tool_call['name'])
            print(msg.content)
        if isinstance(msg,ToolMessage):
            print(msg.content,end=" ")
    seen=len(message)


