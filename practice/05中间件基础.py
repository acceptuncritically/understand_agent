from langchain.agents.middleware import (before_agent, after_agent, before_model,
                                        after_model, wrap_model_call, wrap_tool_call)
from langchain.agents import create_agent, AgentState
from langchain_deepseek import ChatDeepSeek
from langchain_core.tools import tool
from langgraph.runtime import Runtime
"""
state["messages"] = [
    HumanMessage(content="Hello, how are you?", id="52a695c1..."), 
    AIMessage(content="模型返回的内容", id="abc123...")
]
runtime 拥有控制权
    1 动态控制工作流的走向（导航能力）
    2. 动态配置模型或工具（配置能力）
    3. 读取当前执行环境的信息（上下文感知）
在before 和after model时可以运行很多次，而agent只能运行一次
在after agent 后才能获得真正的返回消息
主要作用是进行监控，查看运行过程中可能出现的问题
"""
@tool(description="Get the weather")
def get_weather():
    return "Sunny"
@before_agent
def my_before_agent(state:AgentState,runtime:Runtime):
    """
        @before_agent
    def prepare_agent(state: AgentState, runtime: Runtime) -> None:
        # 场景1：初始化状态
        if "history" not in state:
            state["history"] = []

        # 场景2：记录开始时间，用于性能监控
        state["start_time"] = time.time()

        # 场景3：用户权限校验，无权限直接拒绝
        if not state.get("user_authorized"):
            state["messages"] = [AIMessage(content="您没有权限执行此操作")]
            runtime.jump_to("end")  # 整个 Agent 不跑了
    """
    print(f"state:{state}")
    print(f"runtime:{runtime}")
@after_agent
def my_after_agent(state:AgentState,runtime:Runtime):
    """
        @after_agent
    def cleanup_agent(state: AgentState, runtime: Runtime) -> None:
        # 场景1：计算总耗时
        elapsed = time.time() - state.get("start_time", time.time())
        print(f"Agent 总耗时: {elapsed:.2f}s")

        # 场景2：格式化最终输出，去掉中间的工具调用记录
        final_answer = state["messages"][-1].content
        state["final_output"] = final_answer  # 只留干净的结果

        # 场景3：持久化日志到数据库
        db.save_session(state)
    """
    print(state["messages"][-1])
@before_model
def my_before_model(state:AgentState,runtime:Runtime):
    """
        @before_model
    def add_system_prompt(state: AgentState, runtime: Runtime) -> None:
        # 场景1：统一注入系统提示词（无需在每个节点重复加）
        state["messages"].insert(0, SystemMessage(content="你是一个严格的JSON生成器"))

        # 场景2：敏感词拦截，发现违规直接阻止模型调用
        last = state["messages"][-1]
        if "密码" in last.content:
            runtime.jump_to("end")  # 直接终止，不调用模型了
    """
    print(f"state:{state}, runtime:{runtime}")
@after_model
def my_after_model(state:AgentState,runtime:Runtime):
    """
        @after_model
    def fix_json_format(state: AgentState, runtime: Runtime) -> None:
        # 场景1：修复模型输出的错误格式
        last = state["messages"][-1]
        if last.content:
            try:
                # 模型返回的 JSON 少了个引号？手动修好
                fixed = json.loads(last.content.replace("'", '"'))
                last.content = json.dumps(fixed)  # 写回 state，后续节点拿到的是修正版
            except:
                # 场景2：格式彻底坏了，让模型重写
                runtime.jump_to("model")  # 重新调用模型
    """
    print(f"state:{state}, runtime:{runtime}")

"""
对于wrap_model_call,用于包装模型调用(洋葱模型)可以在其中进行自定义的处理逻辑。操纵的是模型的API调用
其中request 是一个ModelRequest对象，包含模型调用的所有信息，可以用override更改内容
    request.messages | 消息列表（用户输入、历史对话等） 
    request.model    | 当前使用的模型实例 |
    request.tools    | 本次可用的工具列表 |
    request.system_message | 系统提示词 |
handler是一个可调用函数，用于调用大模型

其中的参数在调用agent后内部自动处理
"""
@wrap_model_call
def my_wrap_model_call(request, handler):
    print("wrap_model_call", "进入 —— 包住模型调用")
    response = handler(request)  # 这里才真正请求大模型
    print("wrap_model_call", "退出 —— 模型已返回")
    return response
@wrap_tool_call
def my_wrap_tool_call(request, handler):
    print("wrap_tool_call", f"进入 —— 工具={request.tool_call['name']} 参数={request.tool_call['args']}")
    result = handler(request)  # 这里才真正执行工具函数
    print("wrap_tool_call", f"退出 —— 工具返回 {str(result.content)[:30]}")
    return result

agent = create_agent(
    model=ChatDeepSeek(model="deepseek-chat", temperature=0.9),
    middleware=[my_before_agent, my_after_agent, my_before_model,
                my_after_model, my_wrap_model_call, my_wrap_tool_call]
)
res=agent.invoke({"messages": [{"role": "user", "content": "Hello, how are you?"}]})
print(res)
"""
[
  {
    "stage": "before_agent",
    "runtime": {
      "checkpoint_ns": "my_before_agent.before_agent",
      "task_id": "2319f704-6894-ed76-d896-41009ce0372e",
      "node_attempt": 1,
      "node_first_attempt_time": 1794968880.9259467,
      "context": null,
      "store": null
    },
    "messages": [
      { "type": "HumanMessage", "content": "Hello, how are you?" }
    ]
  },
  {
    "stage": "before_model",
    "runtime": {
      "checkpoint_ns": "my_before_model.before_model",
      "task_id": "88dc16a0-0ab5-7f5a-dc66-e19703c4147c",
      "node_attempt": 1,
      "node_first_attempt_time": 1794968880.9265897,
      "context": null,
      "store": null
    },
    "messages": [
      { "type": "HumanMessage", "content": "Hello, how are you?" }
    ]
  },
  { "event": "wrap_model_call 进入 —— 包住模型调用" },
  { "event": "wrap_model_call 退出 —— 模型已返回" },
  {
    "stage": "after_model",
    "runtime": {
      "checkpoint_ns": "my_after_model.after_model",
      "task_id": "a34ba55b-895a-a679-0f65-9362e85369ac",
      "node_attempt": 1,
      "node_first_attempt_time": 1794968883.2960064,
      "context": null,
      "store": null
    },
    "messages": [
      { "type": "HumanMessage", "content": "Hello, how are you?" },
      {
        "type": "AIMessage",
        "content": "Hello! I'm doing well, thank you for asking. 😊 I'm ready to help you with whatever you need—whether it's answering questions, brainstorming ideas, writing, coding, or just having a chat. How are you doing today?",
        "model": "deepseek-flash",
        "finish_reason": "stop",
        "tokens": { "input": 10, "output": 50, "total": 60 }
      }
    ]
  }
]
"""