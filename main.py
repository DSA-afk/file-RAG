"""
案例2：技术文档问答系统
主程序 - Streamlit Web应用
"""

import streamlit as st
from typing import List, Dict
import os
from dotenv import load_dotenv

from hybrid_retriever import HybridRetriever
from reranker import CrossEncoderReranker
from doc_qa_system import TechDocQA

# 页面配置
st.set_page_config(
    page_title="技术文档问答系统",
    page_icon="📚",
    layout="wide"
)

# 加载环境变量
load_dotenv()

# 自定义CSS
st.markdown("""
<style>
    .main {
        padding-top: 2rem;
    }
    .stTextInput > div > div > input {
        font-size: 16px;
    }
</style>
""", unsafe_allow_html=True)


def initialize_system():
    """初始化系统"""
    try:
        # 创建混合检索器
        retriever = HybridRetriever()

        # 创建重排序器
        reranker = CrossEncoderReranker()

        # 创建QA系统
        qa_system = TechDocQA(
            retriever=retriever,
            reranker=reranker
        )

        return qa_system
    except Exception as e:
        st.error(f"系统初始化失败: {str(e)}")
        return None


def main():
    """主函数"""

    # 标题
    st.title("📚 技术文档问答系统")
    st.markdown("### 快速搜索API文档、代码示例和技术说明")

    st.markdown("---")

    # 初始化系统
    if "qa_system" not in st.session_state:
        with st.spinner("正在初始化系统..."):
            st.session_state.qa_system = initialize_system()

    qa_system = st.session_state.qa_system

    if qa_system is None:
        st.error("⚠️ 系统初始化失败，请检查配置")
        return

    # 侧边栏
    with st.sidebar:
        st.header("⚙️ 检索设置")

        # 检索模式
        retrieval_mode = st.radio(
            "检索模式",
            ["混合检索（推荐）", "向量检索", "关键词检索"],
            index=0
        )

        # 参数调整
        top_k = st.slider("检索文档数", 3, 20, 5)
        use_reranking = st.checkbox("启用重排序", value=True)

        # 显示统计
        st.markdown("---")
        st.info(f"""
        **知识库统计**：
        - 文档数：{qa_system.retriever.doc_count}
        - 代码片段：{qa_system.retriever.code_count}
        """)

        # 清除历史
        if st.button("🗑️ 清除查询历史"):
            if "query_history" in st.session_state:
                del st.session_state.query_history
            st.rerun()

    # 示例查询
    example_queries = [
        "如何使用FastAPI创建API？",
        "Python列表推导式的语法是什么？",
        "PyTorch中如何定义神经网络？",
        "Django的MVC架构是怎样的？"
    ]

    # 显示示例
    if len(st.session_state) <= 2 or "query_history" not in st.session_state:
        st.markdown("### 💡 示例查询")
        cols = st.columns(2)
        for i, example in enumerate(example_queries):
            col = cols[i % 2]
            if col.button(example, key=f"example_{i}"):
                st.session_state.example_query = example
                st.rerun()

    # 查询输入
    if "example_query" in st.session_state:
        default_text = st.session_state.example_query
        del st.session_state.example_query
    else:
        default_text = ""

    if query := st.text_input(
        "🔍 输入你的技术问题",
        value=default_text,
        placeholder="例如：如何在Python中使用装饰器？"
    ).strip():

        # 保存到历史
        if "query_history" not in st.session_state:
            st.session_state.query_history = []

        st.session_state.query_history.append(query)

        # 查询处理
        with st.spinner("🤔 正在搜索技术文档..."):
            try:
                # 确定检索模式
                mode_map = {
                    "混合检索（推荐）": "hybrid",
                    "向量检索": "vector",
                    "关键词检索": "keyword"
                }
                mode = mode_map[retrieval_mode]

                # 执行查询
                result = qa_system.query(
                    question=query,
                    mode=mode,
                    top_k=top_k,
                    use_reranking=use_reranking
                )

                # 显示答案
                st.markdown("### 📖 答案")
                st.markdown(result["answer"])
                st.caption(f"置信度: {result['confidence']:.1%}")

                # 显示检索到的文档
                if result.get("documents") and len(result["documents"]) > 0:
                    st.markdown("---")
                    st.markdown("### 📚 参考文档")

                    for i, doc in enumerate(result["documents"][:5], 1):
                        with st.expander(f"文档 {i}: {doc['title']}", expanded=(i == 1)):
                            st.markdown(f"**类型**: {doc['metadata']['type']}")
                            st.markdown(f"**相关度**: {doc['score']:.2%}")
                            st.markdown("---")
                            st.markdown(doc['content'])

                            # 代码高亮
                            if doc['metadata']['type'] == 'code':
                                st.code(doc['content'], language='python')

                # 显示相关查询
                if result.get("related_queries"):
                    st.markdown("---")
                    st.markdown("### 🔗 相关查询")
                    related_cols = st.columns(min(3, len(result["related_queries"])))
                    for i, related_q in enumerate(result["related_queries"]):
                        related_cols[i].button(related_q, key=f"related_{i}_{query}")

            except Exception as e:
                st.error(f"❌ 查询失败: {str(e)}")

    # 显示历史
    if "query_history" in st.session_state and len(st.session_state.query_history) > 0:
        st.markdown("---")
        st.markdown("### 📜 查询历史")
        for i, hist_query in enumerate(reversed(st.session_state.query_history[-5:]), 1):
            if st.button(hist_query, key=f"hist_{i}"):
                st.session_state.example_query = hist_query
                st.rerun()


if __name__ == "__main__":
    main()
