import streamlit as st
import requests

# ===================== 豆包API配置 =====================
DOUBAO_API_KEY = "ark-8c8dd5e0-2b7f-41c2-bf6b-ce7465dde911-75bd0"
MODEL_ID = "doubao-seed-2-0-lite-260215"

# ===================== 页面设置 =====================
st.set_page_config(page_title="班级学习管理系统", layout="wide")

# ===================== 用户数据 =====================
users = {
    "student1": {"pwd": "123456", "role": "学生", "name": "张三", "wrong_questions": [], "review_count": {}},
    "student2": {"pwd": "123456", "role": "学生", "name": "李四", "wrong_questions": [], "review_count": {}},
    "teacher":  {"pwd": "teacher123", "role": "教师", "name": "王老师"}
}

# ===================== 登录状态 =====================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user" not in st.session_state:
    st.session_state.user = None

# ===================== 登录界面 =====================
if not st.session_state.logged_in:
    st.title("📚 班级学习管理系统")
    username = st.text_input("用户名")
    password = st.text_input("密码", type="password")

    if st.button("登录"):
        if username in users and users[username]["pwd"] == password:
            st.session_state.logged_in = True
            st.session_state.user = users[username]
            st.session_state.username = username
            st.success(f"欢迎 {st.session_state.user['name']}")
            st.rerun()
        else:
            st.error("账号或密码错误")
    st.stop()

# ===================== 已登录 =====================
username = st.session_state.username
user = st.session_state.user

# 顶部栏
col1, col2 = st.columns([4, 1])
with col1:
    st.title(f"📚 学习管理系统 - {user['name']}")
with col2:
    if st.button("退出登录"):
        st.session_state.logged_in = False
        st.rerun()
st.divider()

# ===================== 学生端 =====================
if user["role"] == "学生":
    st.header("👨‍🎓 学生中心")
    menu = st.selectbox("菜单", ["我的错题本", "错题重做"])

    if menu == "我的错题本":
        st.subheader("📕 我的错题")
        wrong = user["wrong_questions"]
        if not wrong:
            st.success("暂无错题！")
        else:
            for i, q in enumerate(wrong):
                st.write(f"{i+1}. {q['题目']}")
                st.info(f"提示：{q['提示']}")

    if menu == "错题重做":
        st.subheader("🔁 错题重做")
        wrong = user["wrong_questions"]
        if not wrong:
            st.success("全部掌握！")
        else:
            q = wrong[0]
            st.write(f"题目：{q['题目']}")
            ans = st.text_input("请作答")
            if st.button("提交"):
                if ans != q["学生答案"]:
                    st.success("正确！")
                    del user["wrong_questions"][0]
                    st.rerun()
                else:
                    st.warning("再想想")

# ===================== 教师端（支持拍照上传） =====================
else:
    st.header("👩‍🏫 教师中心")
    menu = st.selectbox("菜单", [
        "拍照/上传学生作业",
        "布置作业",
        "学生错题总览"
    ])

    # ====== 老师上传学生作业（核心功能）======
    if menu == "拍照/上传学生作业":
        st.subheader("📷 老师上传学生作业 → AI批改")
        student = st.selectbox("选择学生", ["student1", "student2"])
        img = st.file_uploader("上传作业照片", type=["jpg","png","jpeg"])

        if img:
            st.image(img, width=400)

            if st.button("开始AI批改"):
                with st.spinner("批改中..."):
                    prompt = """
你是作业批改老师，严格遵守：
1. 只判断对错
2. 只给思路提示
3. 绝对不给答案
4. 简洁
"""
                    resp = requests.post(
                        "https://ark.cn-beijing.volces.com/api/v3/chat/completions",
                        headers={
                            "Authorization": f"Bearer {DOUBAO_API_KEY}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": MODEL_ID,
                            "messages": [{"role": "user", "content": prompt}]
                        }
                    )
                    result = resp.json()["choices"][0]["message"]["content"]

                    # 显示结果
                    st.subheader("✅ 批改结果")
                    st.success(result)

                    # 自动加入错题
                    if "错误" in result or "❌" in result:
                        users[student]["wrong_questions"].append({
                            "题目": "作业题",
                            "学生答案": "错误答案",
                            "提示": result
                        })
                        st.warning(f"已存入【{users[student]['name']}】错题本")

    # 布置作业
    elif menu == "布置作业":
        st.subheader("📝 布置作业")
        title = st.text_input("标题")
        content = st.text_area("内容")
        if st.button("发布"):
            st.success("发布成功！")

    # 查看所有学生错题
    elif menu == "学生错题总览":
        st.subheader("📊 全班错题一览")
        for s in ["student1", "student2"]:
            with st.expander(f"{users[s]['name']}"):
                wrong = users[s]["wrong_questions"]
                if not wrong:
                    st.write("无错题")
                else:
                    for q in wrong:
                        st.write(f"- {q['题目']} | 提示：{q['提示']}")

st.caption("✅ 老师可拍照上传｜AI只给提示｜错题自动归档")