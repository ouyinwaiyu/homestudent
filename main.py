import streamlit as st
import requests
import json
import os

# ===================== 豆包API配置 =====================
DOUBAO_API_KEY = "ark-8c8dd5e0-2b7f-41c2-bf6b-ce7465dde911-75bd0"
MODEL_ID = "doubao-seed-2-0-lite-260215"

# ===================== 页面设置 =====================
st.set_page_config(page_title="班级学习管理系统", layout="wide")

# ===================== 用户数据持久化 =====================
USER_FILE = "users.json"

# 加载用户数据
def load_users():
    if os.path.exists(USER_FILE):
        with open(USER_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    # 默认用户
    return {
        "teacher": {"pwd": "teacher123", "role": "教师", "name": "王老师", "wrong_questions": []},
        "student1": {"pwd": "123456", "role": "学生", "name": "张三", "wrong_questions": []},
        "student2": {"pwd": "123456", "role": "学生", "name": "李四", "wrong_questions": []}
    }

# 保存用户数据
def save_users(users):
    with open(USER_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

# 初始化用户数据
users = load_users()

# ===================== 登录状态 =====================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user" not in st.session_state:
    st.session_state.user = None
if "page" not in st.session_state:
    st.session_state.page = "login"  # login / register

# ===================== 注册页面 =====================
def register_page():
    st.title("📝 新用户注册")
    username = st.text_input("用户名（登录用）")
    password = st.text_input("密码", type="password")
    name = st.text_input("你的姓名")
    role = st.selectbox("你的身份", ["学生", "教师"])

    if st.button("注册账号"):
        if not username or not password or not name:
            st.error("请填写完整信息！")
            return
        if username in users:
            st.error("这个用户名已经被注册了！")
            return
        
        # 添加新用户
        users[username] = {
            "pwd": password,
            "role": role,
            "name": name,
            "wrong_questions": []
        }
        save_users(users)
        st.success("注册成功！快去登录吧！")
        st.session_state.page = "login"
        st.rerun()
    
    if st.button("已有账号？去登录"):
        st.session_state.page = "login"
        st.rerun()

# ===================== 登录页面 =====================
def login_page():
    st.title("📚 班级学习管理系统")
    st.subheader("请登录")
    username = st.text_input("用户名")
    password = st.text_input("密码", type="password")

    if st.button("登录"):
        if username in users and users[username]["pwd"] == password:
            st.session_state.logged_in = True
            st.session_state.user = users[username]
            st.session_state.username = username
            st.success(f"登录成功！欢迎，{users[username]['name']}")
            st.rerun()
        else:
            st.error("用户名或密码错误，请重试")
    
    if st.button("没有账号？去注册"):
        st.session_state.page = "register"
        st.rerun()

# ===================== 未登录 =====================
if not st.session_state.logged_in:
    if st.session_state.page == "login":
        login_page()
    else:
        register_page()
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
        st.session_state.user = None
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
            st.success("暂无错题！太棒了！")
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
                    st.success("回答正确！")
                    # 移除错题
                    del users[username]["wrong_questions"][0]
                    save_users(users)
                    st.rerun()
                else:
                    st.warning("回答错误，再想想！提示：" + q["提示"])

# ===================== 教师端（支持拍照上传） =====================
else:
    st.header("👩‍🏫 教师中心")
    menu = st.selectbox("菜单", [
        "拍照/上传学生作业",
        "布置作业",
        "学生错题总览"
    ])

    # ====== 老师上传学生作业 ======
    if menu == "拍照/上传学生作业":
        st.subheader("📷 老师上传学生作业 → AI批改")
        # 列出所有学生用户
        student_list = [k for k, v in users.items() if v["role"] == "学生"]
        if not student_list:
            st.warning("还没有学生用户，让学生先注册吧！")
        else:
            student = st.selectbox("选择学生", student_list, format_func=lambda x: users[x]["name"])
            img = st.file_uploader("上传作业照片", type=["jpg","png","jpeg"])

            if img:
                st.image(img, width=400)

                if st.button("开始AI批改"):
                    with st.spinner("AI正在批改中..."):
                        prompt = """
你是作业批改老师，严格遵守：
1. 只判断对错
2. 只给思路提示
3. 绝对不给答案
4. 语言简洁，适合学生自主订正
"""
                        try:
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

                            # 自动加入学生错题本
                            if "错误" in result or "❌" in result:
                                users[student]["wrong_questions"].append({
                                    "题目": "作业题",
                                    "学生答案": "错误答案",
                                    "提示": result
                                })
                                save_users(users)
                                st.warning(f"已存入【{users[student]['name']}】的错题本！")
                        except Exception as e:
                            st.error(f"批改出错了：{e}")

    # 布置作业
    elif menu == "布置作业":
        st.subheader("📝 布置作业")
        title = st.text_input("作业标题")
        content = st.text_area("作业内容")
        if st.button("发布给全班"):
            st.success("作业发布成功！")

    # 查看所有学生错题
    elif menu == "学生错题总览":
        st.subheader("📊 全班错题一览")
        student_list = [k for k, v in users.items() if v["role"] == "学生"]
        if not student_list:
            st.info("还没有学生用户哦")
        else:
            for s in student_list:
                with st.expander(f"{users[s]['name']} 的错题本"):
                    wrong = users[s]["wrong_questions"]
                    if not wrong:
                        st.write("暂无错题")
                    else:
                        for q in wrong:
                            st.write(f"- {q['题目']} | 提示：{q['提示']}")

st.caption("✅ 支持新用户注册｜老师可拍照上传｜AI只给提示｜错题自动归档")
