import streamlit as st
from zhipuai_llm import ZhipuAILLM
import os
from langchain_core.output_parsers import StrOutputParser
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA
import sys
from langchain_community.vectorstores import Chroma
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from zhipuai_embedding import ZhipuAIEmbeddings
from dotenv import load_dotenv, find_dotenv
__import__('pysqlite3')
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

_ = load_dotenv(find_dotenv())    # read local .env file
zhipuai_api_key = os.environ['ZHIPUAI_API_KEY']

#带有历史记录的问答链
def get_chat_qa_chain(question:str,zhipuai_api_key:str):
    # 定义 Embeddings
    embeddings = ZhipuAIEmbeddings()
    #embeddings = HuggingFaceEmbeddings(model_name="Hug/sentence-transformer")
    # 向量数据库持久化路径
    persist_directory = 'data_base/vector_db/chroma'
    # 加载数据库
    vectordb = Chroma(
        persist_directory=persist_directory, 
        embedding_function=embeddings
    )

    llm = ZhipuAILLM(model_name = "glm-4", temperature = 0,zhipuai_api_key = zhipuai_api_key)
    memory = ConversationBufferMemory(
        memory_key="chat_history",  # 与 prompt 的输入变量保持一致。
        return_messages=True  # 将以消息列表的形式返回聊天记录，而不是单个字符串
    )
    retriever=vectordb.as_retriever()
    qa = ConversationalRetrievalChain.from_llm(
        llm,
        retriever=retriever,
        memory=memory
    )
    return qa

#不带历史记录的问答链
def get_qa_chain(question:str,zhipuai_api_key:str):
    # 定义 Embeddings
    embeddings = ZhipuAIEmbeddings()
    #embeddings = HuggingFaceEmbeddings(model_name="Hug/sentence-transformer")
    # 向量数据库持久化路径
    persist_directory = 'data_base/vector_db/chroma'
    # 加载数据库
    vectordb = Chroma(
        persist_directory=persist_directory, 
        embedding_function=embeddings
    )

    llm = ZhipuAILLM(model_name = "glm-4", temperature = 0, zhipuai_api_key = zhipuai_api_key)

    template = """使用以下上下文来回答最后的问题。如果你不知道答案，就说你不知道，不要试图编造答
    案。尽量使答案简明扼要。总是在回答的最后说“谢谢你的提问！”。
    {context}
    问题: {question}
    有用的回答:"""

    QA_CHAIN_PROMPT = PromptTemplate(input_variables=["context","question"],
                                 template=template)

    qa_chain = RetrievalQA.from_chain_type(llm,
                                       retriever=vectordb.as_retriever(),
                                       return_source_documents=True,
                                       chain_type_kwargs={"prompt":QA_CHAIN_PROMPT})
    return qa_chain

# Streamlit 应用程序界面
def main():
    st.title('🦜🔗 动手学大模型应用开发')
    zhipuai_api_key = st.sidebar.text_input('OpenAI API Key', type='password')

    # 添加一个选择按钮来选择不同的模型
    #selected_method = st.sidebar.selectbox("选择模式", ["qa_chain", "chat_qa_chain", "None"])
    selected_method = st.radio(
        "你想选择哪种模式进行对话？",
        ["qa_chain", "chat_qa_chain"],
        captions = ["不带历史记录的检索问答模式", "带历史记录的检索问答模式"])

    # 用于跟踪对话历史
    if 'messages' not in st.session_state:
        st.session_state.messages = []

    messages = st.container(height=300)
    if prompt := st.chat_input("Say something"):
        # 将用户输入添加到对话历史中
        st.session_state.messages.append({"role": "user", "text": prompt})

        if selected_method == "qa_chain":
            answer = get_qa_chain(prompt,zhipuai_api_key)
        elif selected_method == "chat_qa_chain":
            answer = get_chat_qa_chain(prompt,zhipuai_api_key)

        # 检查回答是否为 None
        if answer is not None:
            # 将LLM的回答添加到对话历史中
            st.session_state.messages.append({"role": "assistant", "text": answer})

        # 显示整个对话历史
        for message in st.session_state.messages:
            if message["role"] == "user":
                messages.chat_message("user").write(message["text"])
            elif message["role"] == "assistant":
                messages.chat_message("assistant").write(message["text"])   


if __name__ == "__main__":
    main()

