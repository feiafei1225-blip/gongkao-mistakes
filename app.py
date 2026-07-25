import streamlit as st
import pandas as pd
from datetime import datetime
import os

# 设置页面配置
st.set_page_config(
    page_title="公考错题智能管理系统",
    page_icon="📌",
    layout="wide"
)

# 定义数据保存路径
DATA_FILE = "gongkao_mistakes_data.csv"

# 初始化本地数据文件
if not os.path.exists(DATA_FILE):
    df_init = pd.DataFrame(columns=[
        "ID", "核心板块", "二级考点", "题目简述", 
        "我的错误答案", "正确答案", "核心错误原因归类", 
        "复盘思路", "题目难度", "错误次数", "录入时间"
    ])
    df_init.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")

# 读取数据函数
def load_data():
    return pd.read_csv(DATA_FILE, encoding="utf-8-sig")

# 保存数据函数
def save_data(new_row):
    df = load_data()
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")

# 侧边栏导航
st.sidebar.markdown("### 📌 公考错题智能管理系统")
st.sidebar.markdown("---")
menu = st.sidebar.radio(
    "导航菜单", 
    ["✏️ 录入新错题", "📊 数据分析看板", "📖 错题复习本", "📱 扫码题库/试卷管理", "⚙️ 数据管理"]
)

# 获取 URL 参数（用于手机扫码自动识别题目）
query_params = st.query_params
scan_qid = query_params.get("qid", None)

# ================= 模块一：录入新错题 =================
if menu == "✏️ 录入新错题":
    st.markdown("## 📖 智能复习与巩固")
    
    df_all = load_data()
    
    # 如果是通过手机扫码带了 qid 参数进来，自动检索已有数据或初始化模板
    default_block = "言语理解"
    default_sub = "逻辑填空"
    default_desc = ""
    
    if scan_qid:
        st.info(f"📱 已通过手机扫码锁定题目编号：【 {scan_qid} 】")
        matched = df_all[df_all["ID"].astype(str) == str(scan_qid)]
        if not matched.empty:
            default_block = matched.iloc[0]["核心板块"]
            default_sub = matched.iloc[0]["二级考点"]
            default_desc = matched.iloc[0]["题目简述"]
            st.success("✨ 已自动检索并加载该题目的云端基础信息！")

    with st.form("mistake_form"):
        col1, col2 = st.columns(2)
        with col1:
            core_block = st.selectbox(
                "核心板块", 
                ["言语理解", "数量关系", "判断推理", "资料分析", "申论写作", "常识判断"],
                index=["言语理解", "数量关系", "判断推理", "资料分析", "申论写作", "常识判断"].index(default_block) if default_block in ["言语理解", "数量关系", "判断推理", "资料分析", "申论写作", "常识判断"] else 0
            )
        with col2:
            sub_point = st.text_input("二级考点/题型", value=default_sub)

        question_desc = st.text_area("题目简述 / 核心题干 / 错题出处", value=default_desc, placeholder="例如：2026国考地市级第35题，关于逻辑填空的语境分析...")

        col3, col4 = st.columns(2)
        with col3:
            my_answer = st.text_input("我的错误答案", placeholder="例如：B")
        with col4:
            correct_answer = st.text_input("正确答案", placeholder="例如：C")

        error_reason = st.selectbox(
            "核心错误原因归类",
            ["概念理解偏差/知识盲区", "审题不清/看错条件", "计算失误/粗心", "陷阱项干扰/思维定势", "时间不够仓促蒙错", "申论要点提取不全"]
        )

        review_notes = st.text_area("错题复盘与正确解题思路", placeholder="总结为什么错？正确切入点是什么？陷阱在哪里？")

        col5, col6 = st.columns(2)
        with col5:
            difficulty = st.slider("题目难度", 1, 5, 3)
        with col6:
            error_count = st.number_input("错误次数", min_value=1, value=1, step=1)

        submitted = st.form_submit_button("💾 保存错题到云端库")

        if submitted:
            if not question_desc.strip():
                st.warning("请至少填写题目简述或题干信息！")
            else:
                new_id = scan_qid if scan_qid else datetime.now().strftime("%Y%m%d%H%M%S")
                new_row = {
                    "ID": new_id,
                    "核心板块": core_block,
                    "二级考点": sub_point,
                    "题目简述": question_desc,
                    "我的错误答案": my_answer,
                    "正确答案": correct_answer,
                    "核心错误原因归类": error_reason,
                    "复盘思路": review_notes,
                    "题目难度": difficulty,
                    "错误次数": error_count,
                    "录入时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                save_data(new_row)
                st.success("🎉 错题保存成功！已实时同步至云端数据库。")

# ================= 模块二：数据分析看板 =================
elif menu == "📊 数据分析看板":
    st.markdown("## 📊 备考数据分析看板")
    df = load_data()
    
    if df.empty:
        st.info("目前还没有录入错题，快去“录入新存题”添加几道题吧！")
    else:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("累计收录错题", len(df))
        with col2:
            st.metric("高频错题总数 (错误次数>1)", len(df[df["错误次数"] > 1]))
        with col3:
            st.metric("涉及核心板块数", df["核心板块"].nunique())

        st.markdown("---")
        st.subheader("各板块错题分布")
        block_counts = df["核心板块"].value_counts()
        st.bar_chart(block_counts)

# ================= 模块三：错题复习本 =================
elif menu == "📖 错题复习本":
    st.markdown("## 📖 错题高效回顾与复习")
    df = load_data()
    
    if df.empty:
        st.info("暂无错题记录。")
    else:
        selected_block = st.selectbox("筛选核心板块进行复习", ["全部"] + list(df["核心板块"].unique()))
        if selected_block != "全部":
            df = df[df["核心板块"] == selected_block]

        for index, row in df.iterrows():
            with st.expander(f"【{row['核心板块']}】 {row['题目简述'][:30]}... (难度: {'⭐'*int(row['题目难度'])})"):
                st.markdown(f"**二级考点：** {row['二级考点']}")
                st.markdown(f"**完整题干/出处：** {row['题目简述']}")
                c1, c2 = st.columns(2)
                with c1:
                    st.error(f"我的错误答案：{row['我的错误答案']}")
                with c2:
                    st.success(f"正确答案：{row['正确答案']}")
                st.info(f"**错误原因：** {row['核心错误原因归类']}")
                st.markdown(f"**💡 复盘思路：** {row['复盘思路']}")
                st.caption(f"录入时间：{row['录入时间']} | 错误次数：{row['错误次数']}")

# ================= 模块四：手机扫码与试卷管理 =================
elif menu == "📱 扫码题库/试卷管理":
    st.markdown("## 📱 手机扫码录入配置与管理")
    st.markdown("在这里你可以预先录入题目基本信息，系统会为你生成专属的**题目编号与扫码直达链接**。你可以把链接转成二维码贴在纸质试卷上，手机一扫即可实现快速检索和补全！")
    
    with st.form("preset_form"):
        p_id = st.text_input("题目编号/题号 (例如: 2026_guo_35)", value=f"Q_{datetime.now().strftime('%H%M%S')}")
        p_block = st.selectbox("核心板块", ["言语理解", "数量关系", "判断推理", "资料分析", "申论写作", "常识判断"])
        p_sub = st.text_input("二级考点", value="综合题")
        p_desc = st.text_area("题目简述/题干摘要")
        
        p_submitted = st.form_submit_button("生成可扫码题目档案")
        if p_submitted:
            new_row = {
                "ID": p_id,
                "核心板块": p_block,
                "二级考点": p_sub,
                "题目简述": p_desc,
                "我的错误答案": "",
                "正确答案": "",
                "核心错误原因归类": "未复盘",
                "复盘思路": "",
                "题目难度": 3,
                "错误次数": 1,
                "录入时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            save_data(new_row)
            st.success(f"题目 【{p_id}】 档案创建成功！")

    st.markdown("---")
    st.subheader("当前已生成的题目及扫码直达链接")
    df_preset = load_data()
    if not df_preset.empty:
        # 获取当前网页的域名基础（通过 Streamlit 默认环境获取或引导用户拼接）
        st.dataframe(df_preset[["ID", "核心板块", "二级考点", "题目简述", "录入时间"]])
        st.info("💡 **使用提示**：你的手机扫码链接格式为：`你的网页地址/?qid=题目ID`。例如编号为 `2026_guo_35` 的题目，其扫码直达链接网页就是 `你的网址/?qid=2026_guo_35`。你可以用草料二维码等工具将该网址转成二维码打印贴在试卷上！")

# ================= 模块五：数据管理 =================
elif menu == "⚙️ 数据管理":
    st.markdown("## ⚙️ 数据管理与备份")
    df = load_data()
    
    if not df.empty:
        csv = df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
        st.download_button(
            label="📥 导出全部错题数据 (CSV格式)",
            data=csv,
            file_name=f"gongkao_mistakes_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
        )
    else:
        st.info("当前暂无数据可导出。")
