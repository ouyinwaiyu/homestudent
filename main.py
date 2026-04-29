import streamlit as st
import requests
import json
import os
import base64
from io import BytesIO

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
        "teacher": {"pwd": "teacher123", "role": "教师", "name": "王老师", "class_name": "默认班级", "wrong_questions": [], "pending_reviews": []},
        "student1": {"pwd": "123456", "role": "学生", "name": "张三", "class_name": "默认班级", "wrong_questions": [], "pending_reviews": []},
        "student2": {"pwd": "123456", "role": "学生", "name": "李四", "class_name": "默认班级", "wrong_questions": [], "pending_reviews": []}
    }

# 保存用户数据
def save_users(users):
    with open(USER_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

# 初始化用户数据
users = load_users()
# 兼容旧数据，给老用户加上班级字段
for uname, u in users.items():
    if "class_name" not in u:
        users[uname]["class_name"] = "默认班级"
    if "pending_reviews" not in u:
        users[uname]["pending_reviews"] = []
save_users(users)

# ===================== 登录状态 =====================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user" not in st.session_state:
    st.session_state.user = None
if "page" not in st.session_state:
    st.session_state.page = "login"  # login / register

# 图片转base64
def img_to_base64(img_file):
    bytes_data = img_file.getvalue()
    base64_str = base64.b64encode(bytes_data).decode()
    return f"data:image/jpeg;base64,{base64_str}"

# AI批改函数
def ai_correct_image(img_base64):
    prompt = """
你是作业批改老师，现在我给你发了学生的作业照片，你要：
1. 识别图片里的题目和学生的答案
2. 判断对错
3. 只给思路提示，绝对不给答案
4. 语言简洁，适合学生自主订正
5. 如果有多个题目，逐个说明
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
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": img_base64}}
                        ]
                    }
                ]
            }
        )
        result = resp.json()["choices"][0]["message"]["content"]
        return result, None
    except Exception as e:
        return None, str(e)

# ===================== 注册页面 =====================
def register_page():
    st.title("📝 新用户注册")
    username = st.text_input("用户名（登录用）")
    password = st.text_input("密码", type="password")
    name = st.text_input("你的姓名")
    role = st.selectbox("你的身份", ["学生", "教师"])
    class_name = st.text_input("你的班级名称（比如：三年级1班，同一个班级的老师和学生填一样的）", placeholder="同一个班级的人填一样的班级名，就能一起用了")

    if st.button("注册账号"):
        if not username or not password or not name or not class_name:
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
            "class_name": class_name,
            "wrong_questions": [],
            "pending_reviews": []
        }
        save_users(users)
        st.success(f"注册成功！你已加入【{class_name}】，快去登录吧！")
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
            st.success(f"登录成功！欢迎，{users[username]['name']}，班级：{users[username]['class_name']}")
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
current_class = user["class_name"]

# 拿到当前班级的所有用户
class_users = {k:v for k,v in users.items() if v["class_name"] == current_class}
class_students = {k:v for k,v in class_users.items() if v["role"] == "学生"}

# 顶部栏
col1, col2, col3 = st.columns([3, 1, 1])
with col1:
    st.title(f"📚 学习管理系统 - {user['name']}【{current_class}】")
with col2:
    # 打印按钮
    st.markdown("""
    <button onclick="window.print()" style="
        background-color: #4CAF50;
        border: none;
        color: white;
        padding: 10px 20px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 16px;
        margin: 4px 2px;
        cursor: pointer;
        border-radius: 8px;
    ">🖨️ 打印当前页面</button>
    """, unsafe_allow_html=True)
with col3:
    if st.button("退出登录"):
        st.session_state.logged_in = False
        st.rerun()
st.divider()

# ===================== 学生端 =====================
if user["role"] == "学生":
    st.header("👨‍🎓 学生中心")
    menu = st.selectbox("菜单", ["上传我的作业", "我的错题本", "错题重做"])

    if menu == "上传我的作业":
        st.subheader("📷 拍照上传我的作业")
        st.write("上传后会自动AI初批，然后交给老师审定~")
        img = st.file_uploader("上传作业照片（手机可以直接拍照哦）", type=["jpg","png","jpeg"])

        if img:
            st.image(img, width=400)
            # 自动AI初批
            with st.spinner("AI正在自动批改中..."):
                img_b64 = img_to_base64(img)
                result, err = ai_correct_image(img_b64)
                if err:
                    st.error(f"批改出错了：{err}")
                else:
                    st.subheader("✅ AI初批结果")
                    st.success(result)
                    # 加入待审核
                    users[username]["pending_reviews"].append({
                        "题目": "作业题",
                        "学生答案": "学生提交的作业",
                        "ai提示": result,
                        "teacher_hint": result
                    })
                    save_users(users)
                    st.info("已提交给老师审核啦！老师审定后，错题就会存入你的错题本了！")

    if menu == "我的错题本":
        st.subheader("📕 我的错题")
        wrong = user["wrong_questions"]
        if not wrong:
            st.success("暂无错题！太棒了！")
        else:
            for i, q in enumerate(wrong):
                st.write(f"{i+1}. {q['题目']}")
                st.info(f"提示：{q['提示']}")
                if "错因分析" in q:
                    st.write(f"错因：{q['错因分析']}")

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

# ===================== 教师端 =====================
else:
    st.header("👩‍🏫 教师中心")
    menu = st.selectbox("菜单", [
        "帮学生上传作业",
        "待审核批改",
        "布置作业",
        "班级学生错题总览"
    ])

    # ====== 老师帮学生上传作业 ======
    if menu == "帮学生上传作业":
        st.subheader("📷 帮学生上传作业 → 自动AI初批")
        # 列出当前班级的学生
        if not class_students:
            st.warning("还没有学生加入这个班级哦，让学生注册的时候填一样的班级名就行！")
        else:
            student = st.selectbox("选择学生", list(class_students.keys()), format_func=lambda x: class_students[x]["name"])
            img = st.file_uploader("上传作业照片", type=["jpg","png","jpeg"])

            if img:
                st.image(img, width=400)
                # 自动AI初批
                with st.spinner("AI正在自动批改中..."):
                    img_b64 = img_to_base64(img)
                    result, err = ai_correct_image(img_b64)
                    if err:
                        st.error(f"批改出错了：{err}")
                    else:
                        st.subheader("✅ AI初批结果")
                        st.success(result)
                        # 加入待审核
                        users[student]["pending_reviews"].append({
                            "题目": "作业题",
                            "学生答案": "错误答案",
                            "ai提示": result,
                            "teacher_hint": result
                        })
                        save_users(users)
                        st.info(f"已存入【{class_students[student]['name']}】的待审核列表！你可以去'待审核批改'页面审定了！")

    # ====== 待审核批改 ======
    elif menu == "待审核批改":
        st.subheader("🔍 待审核批改（审定后学生才能看到）")
        has_pending = False
        
        for s in class_students.keys():
            s_user = users[s]
            pending = s_user["pending_reviews"]
            if pending:
                has_pending = True
                with st.expander(f"{s_user['name']} 的待审核作业"):
                    for i, q in enumerate(pending):
                        st.write(f"题目：{q['题目']}")
                        st.write(f"AI初批提示：{q['ai提示']}")
                        
                        # 老师可以修改提示
                        new_hint = st.text_area(f"你可以修改/补充提示", value=q["teacher_hint"], key=f"hint_{s}_{i}")
                        cause = st.text_input("错因分析（可选）", key=f"cause_{s}_{i}")
                        
                        if st.button("审核通过，存入错题本", key=f"pass_{s}_{i}"):
                            # 移到错题本
                            users[s]["wrong_questions"].append({
                                "题目": q["题目"],
                                "学生答案": q["学生答案"],
                                "提示": new_hint,
                                "错因分析": cause
                            })
                            # 从待审核里删掉
                            del users[s]["pending_reviews"][i]
                            save_users(users)
                            st.success("审核完成！已存入学生错题本，学生现在可以看到了！")
                            st.rerun()
        
        if not has_pending:
            st.success("太棒了！所有待审核的作业都处理完了！")

    # 布置作业
    elif menu == "布置作业":
        st.subheader("📝 布置作业")
        title = st.text_input("作业标题")
        content = st.text_area("作业内容")
        if st.button("发布给全班"):
            st.success(f"作业已发布给【{current_class}】全班！")

    # 查看所有学生错题
    elif menu == "班级学生错题总览":
        st.subheader(f"📊 {current_class} 全班错题一览")
        if not class_students:
            st.info("还没有学生加入这个班级哦")
        else:
            for s in class_students.keys():
                with st.expander(f"{users[s]['name']} 的错题本"):
                    wrong = users[s]["wrong_questions"]
                    if not wrong:
                        st.write("暂无错题")
                    else:
                        for q in wrong:
                            st.write(f"- {q['题目']} | 提示：{q['提示']}")
                            if "错因分析" in q and q["错因分析"]:
                                st.write(f"  错因：{q['错因分析']}")

st.caption("✅ 班级隔离｜多老师支持｜学生自助上传｜AI自动批改｜老师审核｜打印功能｜错题归档")
