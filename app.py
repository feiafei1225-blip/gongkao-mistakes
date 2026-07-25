import streamlit as st
import pandas as pd
import sqlite3
import os
from datetime import datetime, timedelta

# Page config for mobile responsiveness
st.set_page_config(
    page_title="公考刷题错题本",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Database setup
DB_FILE = "mistakes_notebook.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mistakes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            section TEXT,
            subcategory TEXT,
            question_desc TEXT,
            my_answer TEXT,
            correct_answer TEXT,
            analysis TEXT,
            error_reason TEXT,
            difficulty INTEGER,
            error_count INTEGER,
            next_review_date TEXT,
            created_at TEXT,
            status TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def run_query(query, params=()):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(query, params)
    conn.commit()
    conn.close()

def load_data(query="SELECT * FROM mistakes", params=()):
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

# UI Navigation
st.sidebar.title("📌 公考错题智能管理系统")
menu = st.sidebar.radio("导航菜单", ["📝 录入新错题", "📊 数据分析看板", "📖 错题复习本", "⚙️ 数据管理"])

# Sections and Subcategories mapping
SECTIONS_MAP = {
    "言语理解": ["逻辑填空", "片段阅读", "语句表达", "篇章阅读"],
    "常识判断": ["政治", "法律", "历史人文", "科技地理", "经济常识", "其他"],
    "数量关系": ["工程问题", "行程问题", "排列组合", "几何问题", "经济利润", "最值问题", "其他"],
    "资料分析": ["增长问题", "比重问题", "平均数/倍数", "综合分析", "计算技巧错误"],
    "判断推理": ["图形推理", "定义判断", "类比推理", "逻辑判断-必然性", "逻辑判断-可能性"],
    "申论": ["归纳概括", "提出对策", "综合分析", "应用文写作", "大作文文章写作"]
}

ERROR_REASONS = [
    "概念理解偏差/知识盲区", 
    "审题不清/看错条件", 
    "计算错误/粗心", 
    "思维定势/陷入陷阱", 
    "时间不够/慌乱盲选", 
    "方法选择错误/效率低下"
]

# 1. 录入新错题
if menu == "📝 录入新错题":
    st.subheader("✍️ 记录纸质错题")
    
    with st.form("mistake_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            section = st.selectbox("核心板块", list(SECTIONS_MAP.keys()))
        with col2:
            subcategory = st.selectbox("二级考点/题型", SECTIONS_MAP[section])
            
        question_desc = st.text_area("题目简述 / 核心题干 / 错题出处", placeholder="例如：2026国考地市级第35题，关于逻辑填空的语境分析...")
        
        c1, c2 = st.columns(2)
        with c1:
            my_answer = st.text_input("我的错误答案", placeholder="例如：B")
        with c2:
            correct_answer = st.text_input("正确答案", placeholder="例如：C")
            
        error_reason = st.selectbox("核心错误原因归类", ERROR_REASONS)
        analysis = st.text_area("错题复盘与正确解题思路", placeholder="总结为什么错？正确切入点是什么？陷阱在哪里？")
        
        col_d, col_f = st.columns(2)
        with col_d:
            difficulty = st.slider("题目难度", 1, 5, 3)
        with col_f:
            error_count = st.number_input("错误次数", min_value=1, value=1, step=1)
            
        submitted = st.form_submit_button("💾 确认提交入库", use_container_width=True)
        if submitted:
            now_str = datetime.now().strftime("%Y-%m-%d")
            next_review = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
            
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO mistakes (section, subcategory, question_desc, my_answer, correct_answer, analysis, error_reason, difficulty, error_count, next_review_date, created_at, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (section, subcategory, question_desc, my_answer, correct_answer, analysis, error_reason, difficulty, error_count, next_review, now_str, "待复习"))
            conn.commit()
            conn.close()
            st.success("🎉 错题录入成功！已自动加入复习计划。")

# 2. 数据分析看板
elif menu == "📊 数据分析看板":
    st.subheader("📊 错题数据全景分析")
    df = load_data()
    
    if df.empty:
        st.info("💡 目前还没有录入错题，快去录入第一道错题吧！")
    else:
        total_mistakes = len(df)
        high_freq = len(df[df["error_count"] > 1])
        
        m1, m2, m3 = st.columns(3)
        m1.metric("累计错题总数", f"{total_mistakes} 道")
        m2.metric("重复出错红牌", f"{high_freq} 道")
        m3.metric("涵盖板块数", f"{df['section'].nunique()} 个")
        
        st.markdown("---")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("### 📌 各板块错题分布")
            section_counts = df["section"].value_counts()
            st.bar_chart(section_counts)
            
        with c2:
            st.markdown("### ⚠️ 核心失分原因占比")
            reason_counts = df["error_reason"].value_counts()
            st.bar_chart(reason_counts)
            
        st.markdown("### 🔥 重复错题 / 高频盲区清单")
        repeat_df = df[df["error_count"] >= 1]
        if not repeat_df.empty:
            st.dataframe(repeat_df[["created_at", "section", "subcategory", "error_reason", "error_count", "question_desc"]], use_container_width=True)

# 3. 错题复习本
elif menu == "📖 错题复习本":
    st.subheader("📖 智能复习与巩固")
    df = load_data()
    
    if df.empty:
        st.info("💡 当前错题本为空。")
    else:
        filter_section = st.selectbox("按板块筛选复习", ["全部"] + list(SECTIONS_MAP.keys()))
        if filter_section != "全部":
            df_filtered = df[df["section"] == filter_section]
        else:
            df_filtered = df
            
        st.write(f"共筛选出 {len(df_filtered)} 条错题记录：")
        
        for index, row in df_filtered.iterrows():
            with st.expander(f"【{row['section']} - {row['subcategory']}】录入时间: {row['created_at']} (错{row['error_count']}次)"):
                st.markdown(f"**题目简述**: {row['question_desc']}")
                col_a, col_b = st.columns(2)
                col_a.error(f"我的答案: {row['my_answer']}")
                col_b.success(f"正确答案: {row['correct_answer']}")
                st.info(f"**错误原因**: {row['error_reason']}")
                st.markdown(f"**深度复盘与解析**: {row['analysis']}")
                
                c_btn1, c_btn2 = st.columns(2)
                if c_btn1.button("✅ 我已彻底掌握", key=f"master_{row['id']}"):
                    run_query("DELETE FROM mistakes WHERE id = ?", (row['id'],))
                    st.success("太棒了！该错题已从错题本移出。")
                    st.rerun()
                if c_btn2.button("🔄 又做错了(错误次数+1)", key=f"again_{row['id']}"):
                    run_query("UPDATE mistakes SET error_count = error_count + 1 WHERE id = ?", (row['id'],))
                    st.warning("已更新错误次数，继续加油！")
                    st.rerun()

# 4. 数据管理
elif menu == "⚙️ 数据管理":
    st.subheader("⚙️ 数据备份与管理")
    df = load_data()
    if not df.empty:
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 导出所有错题为 CSV 表格",
            data=csv,
            file_name=f"cagong_mistakes_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )