from langchain.agents import create_agent
from langchain_deepseek import ChatDeepSeek
from langchain_core.tools import tool
from langchain_core.messages import AIMessage
import csv,time
def parse_records(path="resourse/record.csv")->dict:
    records = {}
    try:
        with open(path, encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                records[row["用户ID"]] = row
        return records
    except Exception as e:
        print(f"Error parsing records: {e}")
        return {}
records = parse_records()
@tool(description="获取当前用户的id，并搜索数据库得到过去的使用记录")
def get_user_history(id:str):
    if not records.get(id):
        return "没有找到该用户ID，请重新输入"
    else:
        return records.get(id)


SYSTEM_PROMPT = ("你是一个严格遵循 ReAct 的智能助手，流程必须是：思考 -> 行动 -> 观察 -> 再思考。\n"
"每一轮只能调用一个工具，禁止同时调用多个工具。\n"
"如果要查用户使用记录，请从用户的输入中提取 user_id，然后调用 get_user_history 查询记录；\n"
"如果用户没有提供 ID，请礼貌地询问用户的 ID。信息足够后再给出最终回答。\n"
"调用工具前，先用一句中文说明你的思考。")
agent = create_agent(
    model=ChatDeepSeek(
    model="deepseek-chat",
    max_retries=3, # 遇到网络问题自动重试 3 次
    timeout=30.0,  # 设置超时时间
    ),
    tools=[get_user_history],
    system_prompt=SYSTEM_PROMPT,
)
question="我的id是1005,请帮我查询过去的使用记录,并给我一些建议"
cnt,seen=0,0
try:
    for chunk in agent.stream(
        {
        "messages": [
            {"role": "user", "content": question},
        ]
        },
        stream_mode="values",
    ):
        # if cnt==1:
        #     seen=len(chunk["messages"])
        #     continue
        for char in chunk["messages"][seen:]:
            if isinstance(char, AIMessage):
                cnt+=1
                for ch in char.content:
                    time.sleep(0.01)
                    print(ch,end="",flush=True)
        seen=len(chunk["messages"])
except Exception as e:
    print(f"Error: {e}")

