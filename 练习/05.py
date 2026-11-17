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
@tool
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
{
  "state": {
    "messages": [
      {
        "type": "HumanMessage",
        "content": "Hello, how are you?",
        "additional_kwargs": {},
        "response_metadata": {},
        "id": "52a695c1-3389-4be0-836c-8753cd13d24c"
      }
    ]
  },
  "runtime": {
    "context": null,
    "store": null,
    "stream_writer": "<function Pregel.stream.<locals>.stream_writer at 0x0000021F1CFE67A0>",
    "heartbeat": "<function _no_op_heartbeat at 0x0000021F1AD454E0>",
    "previous": null,
    "execution_info": {
      "checkpoint_id": "1f1e1ba9-76bd-6ca8-8000-84d362e871b9",
      "checkpoint_ns": "my_before_agent.before_agent:a8436fe9-c898-d621-cf90-cb78ef8e1348",
      "task_id": "a8436fe9-c898-d621-cf90-cb78ef8e1348",
      "thread_id": null,
      "run_id": null,
      "node_attempt": 1,
      "node_first_attempt_time": 1794832694.5792606
    },
    "server_info": null,
    "control": "<langgraph.runtime.RunControl object at 0x0000021F1CDBAB00>"
  },
  "output": {
    "messages": [
      {
        "type": "HumanMessage",
        "content": "Hello, how are you?",
        "additional_kwargs": {},
        "response_metadata": {},
        "id": "52a695c1-3389-4be0-836c-8753cd13d24c"
      },
      {
        "type": "AIMessage",
        "content": "Hello! I'm doing well, thank you for asking. 😊 I'm ready to help you with whatever you need—whether it's answering questions, brainstorming ideas, writing, coding, or just having a chat.\n\nHow are you doing today? Is there something I can help you with?",
        "additional_kwargs": {
          "refusal": null
        },
        "response_metadata": {
          "token_usage": {
            "completion_tokens": 59,
            "prompt_tokens": 10,
            "total_tokens": 69,
            "completion_tokens_details": null,
            "prompt_tokens_details": {
              "audio_tokens": null,
              "cache_write_tokens": null,
              "cached_tokens": 0,
              "image_tokens": null,
              "text_tokens": null
            },
            "prompt_cache_hit_tokens": 0,
            "prompt_cache_miss_tokens": 10
          },
          "model_provider": "deepseek",
          "model_name": "deepseek-flash",
          "system_fingerprint": "bc19ba97cbe016479903222bb1578db6",
          "id": "9d32a21e-268d-4567-9ba8-5c2aed2787d9",
          "finish_reason": "stop",
          "logprobs": null
        },
        "id": "lc_run--01a1e45d-7d34-7271-8868-e4691ff49390-0",
        "tool_calls": [],
        "invalid_tool_calls": [],
        "usage_metadata": {
          "input_tokens": 10,
          "output_tokens": 59,
          "total_tokens": 69,
          "input_token_details": {
            "cache_read": 0
          },
          "output_token_details": {}
        }
      }
    ]
  }
}
"""