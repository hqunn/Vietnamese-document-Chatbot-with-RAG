# Import các thư viện
import streamlit as st
import os
from dotenv import load_dotenv
import google.generativeai as genai

# Import các thành phần của LangChain
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain_huggingface import HuggingFaceEmbeddings

def main():
    load_dotenv()
    
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        st.error("Chưa tìm thấy Google API Key! Vui lòng thêm key vào file .env.")
        return
    genai.configure(api_key=api_key)

    st.set_page_config(page_title="Hỏi Đáp Tài Liệu Tiếng Việt Miễn Phí", page_icon="🇻🇳")
    st.header("Chatbot Hỏi-Đáp Miễn phí với Google Gemini 🚀")

    if "conversation" not in st.session_state:
        st.session_state.conversation = None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    user_question = st.text_input("Đặt câu hỏi về nội dung tài liệu của bạn:")
    if user_question:
        if st.session_state.conversation:
            response = st.session_state.conversation.invoke({"question": user_question})
            st.session_state.chat_history = response['chat_history']
            
            for i, message in enumerate(st.session_state.chat_history):
                if i % 2 == 0:
                    st.write(f"**Bạn:** {message.content}")
                else:
                    st.write(f"**Chatbot:** {message.content}")
        else:
            st.warning("Vui lòng tải lên tài liệu và nhấn 'Xử lý' trước.")

    with st.sidebar:
        st.subheader("Tài liệu của bạn")
        pdf_docs = st.file_uploader(
            "Tải lên các tệp PDF và nhấn 'Xử lý'",
            accept_multiple_files=True,
            type="pdf"
        )
        if st.button("Xử lý"):
            if pdf_docs:
                with st.spinner("Đang xử lý tài liệu, vui lòng chờ..."):
                    text = ""
                    for pdf in pdf_docs:
                        with open(pdf.name, "wb") as f:
                            f.write(pdf.getbuffer())
                        loader = PyPDFLoader(pdf.name)
                        documents = loader.load()
                        for doc in documents:
                            text += doc.page_content
                        os.remove(pdf.name)

                    text_splitter = RecursiveCharacterTextSplitter(
                        chunk_size=1000,
                        chunk_overlap=200,
                        length_function=len
                    )
                    chunks = text_splitter.split_text(text=text)

                    embeddings = HuggingFaceEmbeddings(
                        model_name="dangvantuan/vietnamese-embedding"
                    )
                    
                    vector_store = FAISS.from_texts(chunks, embedding=embeddings)
                    
                    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.7)
                    
                    st.session_state.conversation = ConversationalRetrievalChain.from_llm(
                        llm=llm,
                        retriever=vector_store.as_retriever(),
                        memory=ConversationBufferMemory(memory_key='chat_history', return_messages=True)
                    )
                    
                    st.success("Xử lý hoàn tất! Bạn có thể bắt đầu hỏi đáp.")
            else:
                st.warning("Vui lòng tải lên ít nhất một tệp PDF.")

if __name__ == '__main__':
    main()