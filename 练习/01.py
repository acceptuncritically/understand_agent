import time
from langchain_deepseek import ChatDeepSeek
from langchain.agents import create_agent
from langchain_core.tools import tool
@tool(description="用来获取当前用户所在城市的天气")
def get_weather():
    return "晴天"
model=ChatDeepSeek(model="deepseek-chat",temperature=0.9)
agent=create_agent(
    tools=[get_weather],
    model=model,
    system_prompt="你是一位天气查询助手"
)
"""
基础的文本调用invoke时只会有role和content两个字段
system (systemMessage)系统提示词 
user (HumanMessage)代表来自用户的提问 
assistant (AIMessage)代表来自模型的回复 让AI记住自己的历史对话
tool (ToolMessage)代表工具调用的结果,丰富AI得到的内容
"""

res=agent.invoke(
    {"messages":[{"role":"user","content":"今天适合跑步吗"}]},
    stream_mode="values",#1保证返回完整状态字典，2正确处理中断信息
)
# print(res["messages"])
# print(res["messages"][-1].text)
# print(res["messages"][-1].content)
# content 是“原始数据”，而 text 是“安全提取器”
# 不同的大模型厂商会返回不同类型的结果
"""通过调用invoke返回的结果
{
    "messages": [  // 消息列表，按时间顺序包含整个对话过程
        HumanMessage(content="用户的问题"), 
        AIMessage(content="Agent的回复"), 
        ToolMessage(content="工具调用的结果"), 
        AIMessage(content="最终回复") 
    ],
    // ... 可能还有其他状态字段
}
"""
#获得的已经是每一个字块了
res_stream=agent.stream(
    {"messages":[{"role":"user","content":"今天适合跑步吗"}]},
    stream_mode="values"#返回每一步的详细信息
)
"""
# 步骤1
{'messages': [HumanMessage("今天天气？")]}
# 步骤2（包含历史）
{'messages': [HumanMessage("今天天气？"), AIMessage(tool_calls=[...])]}
# 步骤3（包含历史）
{'messages': [HumanMessage(...), AIMessage(...), ToolMessage("晴天，25度")]}
# 步骤4（包含所有历史）
{'messages': [HumanMessage(...), AIMessage(...), ToolMessage(...), AIMessage("今天是晴天，25度。")]}

chunk 每次都是一个完整的字典，比如 
{"messages": [HumanMessage(...), AIMessage(...)]}

"""
# for chunk in res_stream:
#     # print(chunk)
#     for char in chunk["messages"][-1].content:
#         time.sleep(0.01)
#         print(char,end="",flush=True)

other_res_stream=agent.stream(
    {"messages":[{"role":"user","content":"今天适合跑步吗"}]},
    stream_mode="updates"#返回每一步增加的信息
)
"""
# 步骤1：用户提问
{'messages': [HumanMessage(content="今天天气？")]}
# 步骤2：AI 调用工具（只返回这一步新增的 AI 消息）
{'messages': [AIMessage(content="", tool_calls=[...])]} 
# 步骤3：工具返回结果（只返回这一步新增的工具消息）
{'messages': [ToolMessage(content="晴天，25度")]}
# 步骤4：AI 生成最终回答（只返回这一步新增的 AI 消息）
{'messages': [AIMessage(content="今天是晴天，25度。")]}
"""

the_other_res_stream=agent.stream(
    {"messages":[{"role":"user","content":"今天适合跑步吗"}]},
    stream_mode="messages"#获得真正的打字机效果
)
#通过解包将tuple解包成两个变量获取其中的AIMessage
for chunk,metadata in the_other_res_stream:
    if chunk.type=="AIMessageChunk":
        # 完整的 AIMessage → type 是 "ai"
        # 流式的 AIMessageChunk → type 是 "AIMessageChunk
        print(chunk.content,end="",flush=True)
""" the_other_res_stream 返回的结果
(
    # 第 1 部分：message_chunk (AIMessageChunk 对象)
    AIMessageChunk(
        content='你', 
        additional_kwargs={}, 
        response_metadata={}, 
        id='run-6a3b...', 
        type='AIMessageChunk'  # <--- 注意这里的 type
    ), 
    
    # 第 2 部分：metadata (字典)
    {
        'langgraph_node': 'agent',   # 当前在哪个节点运行
        'langgraph_step': 1,         # 第几步
        'langgraph_triggers': ['start:agent'],
        'langgraph_checkpoint_ns': 'agent:...',
        'checkpoint_ns': 'agent:...',
        'checkpoint_id': '1ef...'
    }
)
"""