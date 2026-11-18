from langchain_core.prompts import  ChatPromptTemplate
from langchain_deepseek import ChatDeepSeek
from langchain_core.output_parsers import StrOutputParser
from langchain.agents import create_agent
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.tools import tool
from langchain_community.embeddings import ZhipuAIEmbeddings
from langchain_community.document_loaders import TextLoader
import os

from setuptools import glob

RAG_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "你是一名扫地机器人推销方面的顾问。\n"
     "请你严格按照下面的参考资料回答问题，资料中并没有写到的内容不要擅自猜测和回答。\n\n"
     "参考资料：\n{context}"),
    ("human", "问题：'{{input}}'"),   # ← 你的"问题:{input}"改成这种形式
])

model=ChatDeepSeek(model="deepseek-chat",temperature=0.7,timeout=10)

# 可能以后会查找数据库中的内容，如果与数据库的名不完全一致
# 就会新创建一个部分，不会读取到原来的部分
the_collection_name="first"
persist_directory_path= "chroma"
def build_store():
    """
    通过Chroma将数据传入数据库中，
        collection_name 为整个数据库中的一个部分
        persist_directory 为整个数据库所存在的位置
        其中使用了SQLite
    :return:
    """
    vs=Chroma(
        collection_name=the_collection_name,
        persist_directory=persist_directory_path,
        embedding_function=ZhipuAIEmbeddings(
            model="embedding-3",
            api_key=os.getenv("ZHIPU_API_KEY"),
        )
    )
    # 先去查询库里是否存在，有就跳过
    """
    vs是一个集合的实例，调用vs.get()时默认会找到集合中的所有数据
    并会返回一个字典
    {
    "ids": ["id_1", "id_2", "id_3"],
    "embeddings": [...],
    "metadatas": [...],
    "documents": [...]
}
    """
    documents=[]
    # 假设你准备插入一批新数据，它们的 ID 是 new_ids 列表
    for txt_path in sorted(glob.glob(os.path.join("data", "*.txt"))):
        """
        os.path.join("data", "*.txt")  # 将data目录下的所有txt文件路径智能的拼接在一起
        glob.glob将所有txt文件的路径装在一个列表中(无序)
        在通过sorted函数对列表进行排序
        """
        documents.extend(TextLoader(txt_path,encoding="utf-8").load())
    splitter = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=20)
    chunks = splitter.split_documents(documents)
    # 2. 为每个 chunk 生成唯一的 ID (比如用 md5 哈希)
    import hashlib
    # 通过将chunk编码成字节串，然后计算md5值，通过哈希得到一个16字节的哈希值，最后转换成十六进制字符串

    new_ids = [hashlib.md5(chunk.page_content.encode('utf-8')).hexdigest() for chunk in chunks]

    # 3. 拿着 new_ids 去查重
    existing_ids = vs.get(ids=new_ids)["ids"]

    # 4. 找出真正需要新增的数据
    # 将对应的文本放在chunks_to_add列表中
    # 将对应的id放在ids_to_add列表中
    chunks_to_add = []
    ids_to_add = []
    for i, chunk_id in enumerate(new_ids):
        if chunk_id not in existing_ids:  # 如果这个ID不在库里
            ids_to_add.append(chunk_id)
            chunks_to_add.append(chunks[i])

    # 5. 如果全都在库里了，直接跳过
    if not chunks_to_add:
        print("所有数据已存在，跳过建库。")
        return vs

    # 6. 只有新的数据才去算向量并存入 (这里才是真正耗钱耗时的)
    # print(f"发现 {len(chunks_to_add)} 条新数据，开始计算向量...")
    vs.add_documents(
        ids=ids_to_add,
        documents=chunks_to_add
        # embedding_function 会自动处理 chunks_to_add 算向量
    )

    return vs
@tool(description="通过返回rag调用后的")
def rag_return(query):
    return rag_retriever_combine(query)

def rag_retriever_combine(query):
    docs=retriever.invoke(query)
    context = "\n".join(f"参考消息{i}: {doc.page_content}" for i, doc in enumerate(docs))
    return rag_chain.invoke({"messages":[{"role":"user","content":query}],
                            "context":context})
def main():
    global rag_chain,retriever
    vs=build_store()
    retriever =vs.as_retriever(search_kwargs={"k": 4})
    rag_chain=RAG_PROMPT|model|StrOutputParser()

    agent=create_agent(
        model=model,
        tools=[rag_return],
        system_prompt="请严格按照ReAct的格式先思\n"
                      "后一个一个调用模型保证每次调用前都要先思考一遍",
    )
    query="扫地机器人的工作原理是什么？"
    res=agent.invoke({"messages":[{"role":"user","content":query}]})
    print(res["messages"][-1].content)
if __name__=="__main__":
    main()
