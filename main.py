import streamlit as st
import requests
import json
import os
import base64
from io import BytesIO
from datetime import datetime, timedelta
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import red, green, blue
from PIL import Image

# ===================== 系统配置 =====================
DOUBAO_API_KEY = "ark-8c8dd5e0-2b7f-41c2-bf6b-ce7465dde911-75bd0"
MODEL_ID = "doubao-seed-2-0-lite-260215"
ADMIN_USER = "admin"  # 后台管理员账号

# ===================== 页面设置 =====================
st.set_page_config(page_title="班级学习管理系统", layout="wide")

# ===================== 用户数据持久化 =====================
USER_FILE = "users.json"
PDF_STORE = "pdf_store"
os.makedirs(PDF_STORE, exist_ok=True)

# 加载用户数据
def load_users():
    if os.path.exists(USER_FILE):
        with open(USER_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    # 默认用户
    return {
        "admin": {"pwd": "admin123", "role": "总监", "name": "管理员", "class_name": "系统", "wrong_questions": [], "pending_reviews": [], "is_authorized": True, "finished_homeworks": []},
        "teacher": {"pwd": "teacher123", "role": "教师", "name": "王老师", "class_name": "默认班级", "wrong_questions": [], "pending_reviews": [], "is_authorized": True, "finished_homeworks": []},
        "student1": {"pwd": "123456", "role": "学生", "name": "张三", "class_name": "默认班级", "wrong_questions": [], "pending_reviews": [], "is_authorized": True, "finished_homeworks": []},
        "student2": {"pwd": "123456", "role": "学生", "name": "李四", "class_name": "默认班级", "wrong_questions": [], "pending_reviews": [], "is_authorized": True, "finished_homeworks": []}
    }

# 保存用户数据
def save_users(users):
    with open(USER_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

# 初始化字体（支持中文）
def init_font():
    # 注册中文字体
    pdfmetrics.registerFont(TTFont('SimHei', '/usr/share/fonts/truetype/SimHei.ttf'))

# 图片转PDF
def img_to_pdf(img_base64, ai_result, teacher_hint=None):
    init_font()
    # 解码图片
    img_data = base64.b64decode(img_base64.split(',')[1])
    img = Image.open(BytesIO(img_data))
    width, height = img.size
    # PDF尺寸和图片一致
    pdf_buffer = BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=(width, height))
    # 画图片
    c.drawImage(BytesIO(img_data), 0, 0, width=width, height=height)
    c.setFont("SimHei", 12)
    
    # 解析AI的结果，处理标记
    lines = ai_result.split('\n')
    y_pos = height - 50  # 从顶部开始写解析
    for line in lines:
        line = line.strip()
        if not line:
            continue
        # 处理对错标记
        if "正确" in line or "对" in line:
            c.drawString(10, y_pos, "√")
            c.setFillColor(green)
        elif "部分" in line:
            c.drawString(10, y_pos, "乄")
            c.setFillColor(blue)
            # 写解析
            c.drawString(30, y_pos, line)
            y_pos -= 20
        elif "错误" in line or "错" in line:
            c.drawString(10, y_pos, "×")
            c.setFillColor(red)
            # 写解析
            c.drawString(30, y_pos, line)
            y_pos -= 20
        else:
            # 老师修改的解析
            if teacher_hint:
                c.drawString(10, y_pos, teacher_hint)
                y_pos -= 20
    
    c.save()
    pdf_buffer.seek(0)
    return pdf_buffer.getvalue()

# 图片转base64
def img_to_base64(img_file):
    bytes_data = img_file.getvalue()
    base64_str = base64.b64encode(bytes_data).decode()
    return f"data:image/jpeg;base64,{base64_str}"

# AI批改函数
def ai_correct_image(img_base64):
    prompt = """
你是作业批改老师，现在我给你发了学生的作业照片，你要：
1. 识别图片里的所有题目和学生的答案
2. 逐个判断：
   - 完全正确的，只标记，不用解析
   - 部分正确的，标记"乄"，然后在后面写解析提示
   - 完全错误的，标记"×"，然后在后面写解析提示
3. 绝对不给答案，只给思路提示
4. 语言简洁，不要多余的话
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
        # 过滤多余文字
        result = result.replace("我已明确批改要求，请你提供需要批改的题目和你的作答内容", "").strip()
        return result, None
    except Exception as e:
        return None, str(e)

# 生成变型题
def generate_variant_questions(original_question):
    prompt = f"""
我给你一道题目，请你按照1:2的比例，生成2道同类型的变型题，知识点一样，但是题目数据或者问法不一样，不要给答案，只给题目：
原题：{original_question}
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
        return resp.json()["choices"][0]["message"]["content"], None
    except Exception as e:
        return None, str(e)

# 检查错题是否可以删除
def can_delete(timestamp_str):
    if not timestamp_str:
        return True
    try:
        q_time = datetime.fromisoformat(timestamp_str)
        return datetime.now() - q_time >= timedelta(days=6)
    except:
        return True

# 初始化用户数据
users = load_users()
# 兼容旧数据
for uname, u in users.items():
    if "class_name" not in u:
        users[uname]["class_name"] = "默认班级"
    if "pending_reviews" not in u:
        users[uname]["pending_reviews"] = []
    if "is_authorized" not in u:
        users[uname]["is_authorized"] = False
    if "finished_homeworks" not in u:
        users[uname]["finished_homeworks"] = []
    # 给旧错题加上时间戳和图片字段
    for q in users[uname].get("wrong_questions", []):
        if "timestamp" not in q:
            q["timestamp"] = (datetime.now() - timedelta(days=7)).isoformat()
        if "img_base64" not in q:
            q["img_base64"] = None
save_users(users)

# ===================== 登录状态 =====================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user" not in st.session_state:
    st.session_state.user = None
if "page" not in st.session_state:
    st.session_state.page = "login"

# ===================== 注册页面 =====================
def register_page():
    st.title("📝 新用户注册")
    username = st.text_input("用户名（登录用）")
    password = st.text_input("密码", type="password")
    name = st.text_input("你的姓名")
    role = st.selectbox("你的身份", ["学生", "教师", "总监"])
    class_name = st.text_input("你的班级名称（同一个班级的填一样的）", placeholder="比如：三年级1班")

    if st.button("注册账号"):
        if not username or not password or not name or not class_name:
            st.error("请填写完整信息！")
            return
        if username in users:
            st.error("这个用户名已经被注册了！")
            return
        
        # 新用户默认未授权，需要管理员开权限
        users[username] = {
            "pwd": password,
            "role": role,
            "name": name,
            "class_name": class_name,
            "wrong_questions": [],
            "pending_reviews": [],
            "is_authorized": False,
            "finished_homeworks": []
        }
        save_users(users)
        st.success(f"注册成功！你已加入【{class_name}】，请联系管理员开通AI权限后即可使用全部功能！")
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
            auth_tip = "（已开通AI权限）" if users[username]["is_authorized"] else "（未开通AI权限，仅可使用基础功能）"
            st.success(f"登录成功！欢迎，{users[username]['name']}，班级：{users[username]['class_name']} {auth_tip}")
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
is_authorized = user["is_authorized"]

# 拿到当前班级的所有用户
class_users = {k:v for k,v in users.items() if v["class_name"] == current_class}
class_students = {k:v for k,v in class_users.items() if v["role"] == "学生"}
all_users = users  # 总监用的

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

# ===================== 总监端 =====================
if user["role"] == "总监":
    st.header("👔 总监管理中心")
    menu = st.selectbox("菜单", [
        "用户授权管理",
        "全平台内容总览",
        "作业返回",
        "变型题生成"
    ])

    if menu == "用户授权管理":
        st.subheader("🔑 用户授权管理")
        for uname, u in all_users.items():
            with st.expander(f"{u['name']} - {u['role']} - 班级：{u['class_name']}"):
                st.write(f"用户名：{uname}")
                st.write(f"当前授权状态：{'已授权' if u['is_authorized'] else '未授权'}")
                if not u['is_authorized']:
                    if st.button("开通AI权限", key=f"auth_{uname}"):
                        users[uname]["is_authorized"] = True
                        save_users(users)
                        st.success("已开通！")
                        st.rerun()
                else:
                    if st.button("取消AI权限", key=f"unauth_{uname}"):
                        users[uname]["is_authorized"] = False
                        save_users(users)
                        st.success("已取消！")
                        st.rerun()

    if menu == "全平台内容总览":
        st.subheader("📊 全平台所有用户内容")
        for uname, u in all_users.items():
            with st.expander(f"{u['name']} - {u['role']} - 班级：{u['class_name']}"):
                wrong = sorted(u["wrong_questions"], key=lambda x: x.get("timestamp", ""), reverse=True)
                if wrong:
                    st.write("错题：")
                    for q in wrong:
                        st.write(f"- {q['题目']} | 解析：{q['提示']}")
                else:
                    st.write("暂无错题")
                pending = u["pending_reviews"]
                if pending:
                    st.write("待审核作业：")
                    for q in pending:
                        st.write(f"- {q['题目']}")
                else:
                    st.write("暂无待审核作业")

    if menu == "作业返回":
        st.subheader("📄 作业返回（已审核的作业PDF）")
        all_pdfs = []
        for uname, u in all_users.items():
            for pdf in u.get("finished_homeworks", []):
                pdf["student_name"] = u["name"]
                all_pdfs.append(pdf)
        if not all_pdfs:
            st.success("暂无已完成的作业")
        else:
            for pdf in sorted(all_pdfs, key=lambda x: x["timestamp"], reverse=True):
                st.write(f"📅 {datetime.fromisoformat(pdf['timestamp']).strftime('%Y-%m-%d')} | 学生：{pdf['student_name']}")
                # 下载按钮
                b64 = base64.b64encode(pdf["pdf_data"]).decode()
                href = f'<a href="data:application/pdf;base64,{b64}" download="作业_{pdf["student_name"]}_{datetime.fromisoformat(pdf["timestamp"]).strftime("%Y%m%d")}.pdf">下载PDF</a>'
                st.markdown(href, unsafe_allow_html=True)
                st.divider()

    if menu == "变型题生成":
        st.subheader("🔄 变型题生成")
        if not is_authorized:
            st.error("你还没有开通AI权限，无法使用这个功能！")
        else:
            original = st.text_area("输入原题，系统会自动生成2道同类型变型题")
            if st.button("生成变型题"):
                with st.spinner("生成中..."):
                    result, err = generate_variant_questions(original)
                    if err:
                        st.error(err)
                    else:
                        st.subheader("生成的变型题：")
                        st.write(result)
                        st.info("你可以把这些题手动发给学生了！")

# ===================== 教师端 =====================
elif user["role"] == "教师":
    st.header("👩‍🏫 教师中心")
    menu = st.selectbox("菜单", [
        "帮学生上传作业",
        "待审核批改",
        "作业返回",
        "变型题生成",
        "布置作业",
        "班级学生错题总览"
    ])

    if menu == "帮学生上传作业":
        st.subheader("📷 帮学生上传作业")
        if not is_authorized:
            st.error("你还没有开通AI权限，无法使用AI批改功能！请联系总监开通！")
        else:
            if not class_students:
                st.warning("还没有学生加入这个班级哦")
            else:
                student = st.selectbox("选择学生", list(class_students.keys()), format_func=lambda x: class_students[x]["name"])
                img = st.file_uploader("上传作业照片，自动转PDF批改", type=["jpg","png","jpeg"])

                if img:
                    st.image(img, width=400)
                    # 自动AI初批
                    with st.spinner("AI正在自动批改中..."):
                        img_b64 = img_to_base64(img)
                        result, err = ai_correct_image(img_b64)
                        if err:
                            st.error(f"批改出错了：{err}")
                        else:
                            if "##全部正确" in result:
                                st.success(f"🎉 {class_students[student]['name']}这次作业全对！")
                                # 生成PDF
                                pdf_data = img_to_pdf(img_b64, result)
                                # 存到作业返回
                                users[student]["finished_homeworks"].append({
                                    "pdf_data": pdf_data,
                                    "timestamp": datetime.now().isoformat()
                                })
                                save_users(users)
                                st.info("已生成作业PDF，存入作业返回了！")
                            else:
                                st.subheader("✅ AI初批结果")
                                st.success(result)
                                # 加入待审核，带图片
                                users[student]["pending_reviews"].append({
                                    "题目": "作业题",
                                    "student_name": class_students[student]["name"],
                                    "ai提示": result,
                                    "teacher_hint": result,
                                    "img_base64": img_b64
                                })
                                save_users(users)
                                st.info("已存入待审核，你可以直接修改评改内容，审核后生成PDF！")

    if menu == "待审核批改":
        st.subheader("🔍 待审核批改")
        has_pending = False
        
        for s in class_students.keys():
            s_user = users[s]
            pending = s_user["pending_reviews"]
            if pending:
                has_pending = True
                with st.expander(f"{s_user['name']} 的待审核作业"):
                    for i, q in enumerate(pending):
                        st.write(f"题目：{q['题目']}")
                        if q.get("img_base64"):
                            st.image(q["img_base64"], width=400, caption="作业原图")
                        
                        # 老师直接修改评改内容
                        new_hint = st.text_area(f"直接修改评改解析", value=q["teacher_hint"], key=f"hint_{s}_{i}")
                        cause = st.text_input("错因分析（可选）", key=f"cause_{s}_{i}")
                        
                        if st.button("审核通过，生成PDF", key=f"pass_{s}_{i}"):
                            # 生成带解析的PDF
                            pdf_data = img_to_pdf(q["img_base64"], q["ai提示"], new_hint)
                            # 存到作业返回
                            users[s]["finished_homeworks"].append({
                                "pdf_data": pdf_data,
                                "timestamp": datetime.now().isoformat()
                            })
                            # 错题存入错题本
                            users[s]["wrong_questions"].append({
                                "题目": q["题目"],
                                "学生答案": q["学生答案"],
                                "提示": new_hint,
                                "错因分析": cause,
                                "timestamp": datetime.now().isoformat(),
                                "img_base64": q.get("img_base64")
                            })
                            # 删掉待审核
                            del users[s]["pending_reviews"][i]
                            save_users(users)
                            st.success("审核完成！PDF已存入作业返回，错题也存入了！")
                            st.rerun()
        
        if not has_pending:
            st.success("所有待审核的都处理完了！")

    if menu == "作业返回":
        st.subheader("📄 作业返回（已审核的作业PDF）")
        my_pdfs = []
        for s in class_students.keys():
            for pdf in users[s].get("finished_homeworks", []):
                pdf["student_name"] = users[s]["name"]
                my_pdfs.append(pdf)
        if not my_pdfs:
            st.success("暂无已完成的作业")
        else:
            for pdf in sorted(my_pdfs, key=lambda x: x["timestamp"], reverse=True):
                st.write(f"📅 {datetime.fromisoformat(pdf['timestamp']).strftime('%Y-%m-%d')} | 学生：{pdf['student_name']}")
                b64 = base64.b64encode(pdf["pdf_data"]).decode()
                href = f'<a href="data:application/pdf;base64,{b64}" download="作业_{pdf["student_name"]}_{datetime.fromisoformat(pdf["timestamp"]).strftime("%Y%m%d")}.pdf">下载PDF</a>'
                st.markdown(href, unsafe_allow_html=True)
                st.divider()

    if menu == "变型题生成":
        st.subheader("🔄 变型题生成")
        if not is_authorized:
            st.error("你还没有开通AI权限，无法使用这个功能！")
        else:
            original = st.text_area("输入原题，系统会自动生成2道同类型变型题")
            if st.button("生成变型题"):
                with st.spinner("生成中..."):
                    result, err = generate_variant_questions(original)
                    if err:
                        st.error(err)
                    else:
                        st.subheader("生成的变型题：")
                        st.write(result)
                        st.info("你可以把这些题手动发给学生了！")

    # 原来的功能保留
    elif menu == "布置作业":
        st.subheader("📝 布置作业")
        title = st.text_input("作业标题")
        content = st.text_area("作业内容")
        if st.button("发布给全班"):
            st.success(f"作业已发布给【{current_class}】全班！")

    elif menu == "班级学生错题总览":
        st.subheader(f"📊 {current_class} 全班错题一览")
        if not class_students:
            st.info("还没有学生加入这个班级哦")
        else:
            for s in class_students.keys():
                with st.expander(f"{users[s]['name']} 的错题"):
                    wrong = sorted(users[s]["wrong_questions"], key=lambda x: x.get("timestamp", ""), reverse=True)
                    if not wrong:
                        st.write("暂无错题")
                    else:
                        for i, q in enumerate(wrong):
                            st.write(f"📅 {datetime.fromisoformat(q['timestamp']).strftime('%Y-%m-%d')}")
                            st.write(f"- {q['题目']} | 解析：{q['提示']}")
                            if "错因分析" in q and q["错因分析"]:
                                st.write(f"  错因：{q['错因分析']}")
                            if can_delete(q.get("timestamp")):
                                if st.button("删除这条错题", key=f"del_teacher_{s}_{i}"):
                                    del users[s]["wrong_questions"][i]
                                    save_users(users)
                                    st.success("已删除！")
                                    st.rerun()
                            else:
                                st.caption("6天后可删除")
                            st.divider()

# ===================== 学生端 =====================
else:
    st.header("👨‍🎓 学生中心")
    menu = st.selectbox("菜单", ["上传我的作业", "错题解析", "错题本", "作业返回"])

    if menu == "上传我的作业":
        st.subheader("📷 拍照上传我的作业")
        if not is_authorized:
            st.error("你还没有开通AI权限，无法使用AI批改功能！请联系老师/总监开通！")
        else:
            st.write("上传后自动转PDF批改，正确的打√，错误的打×加解析~")
            img = st.file_uploader("上传作业照片", type=["jpg","png","jpeg"])

            if img:
                st.image(img, width=400)
                with st.spinner("AI正在自动批改中..."):
                    img_b64 = img_to_base64(img)
                    result, err = ai_correct_image(img_b64)
                    if err:
                        st.error(f"批改出错了：{err}")
                    else:
                        if "##全部正确" in result:
                            st.success("🎉 太棒了！这次作业全对！")
                            pdf_data = img_to_pdf(img_b64, result)
                            users[username]["finished_homeworks"].append({
                                "pdf_data": pdf_data,
                                "timestamp": datetime.now().isoformat()
                            })
                            save_users(users)
                            st.info("已生成作业PDF，存入作业返回了！")
                        else:
                            st.subheader("✅ AI初批结果")
                            st.success(result)
                            users[username]["pending_reviews"].append({
                                "题目": "作业题",
                                "ai提示": result,
                                "teacher_hint": result,
                                "img_base64": img_b64
                            })
                            save_users(users)
                            st.info("错题已提交给老师审核啦！")

    if menu == "错题解析":
        st.subheader("📝 错题解析")
        wrong = sorted(user["wrong_questions"], key=lambda x: x.get("timestamp", ""), reverse=True)
        if not wrong:
            st.success("暂无错题！太棒了！")
        else:
            for i, q in enumerate(wrong):
                st.write(f"📅 {datetime.fromisoformat(q['timestamp']).strftime('%Y-%m-%d')}")
                st.write(f"{i+1}. {q['题目']}")
                st.info(f"解析提示：{q['提示']}")
                if "错因分析" in q and q["错因分析"]:
                    st.write(f"错因：{q['错因分析']}")
                
                if can_delete(q.get("timestamp")):
                    if st.button("删除这条错题", key=f"del_ana_{i}"):
                        del users[username]["wrong_questions"][i]
                        save_users(users)
                        st.success("已删除！")
                        st.rerun()
                else:
                    st.caption("6天后可删除这条错题")
                st.divider()

    if menu == "错题本":
        st.subheader("📕 错题本（原题）")
        wrong = sorted(user["wrong_questions"], key=lambda x: x.get("timestamp", ""), reverse=True)
        if not wrong:
            st.success("全部掌握！没有错题啦！")
        else:
            q = wrong[0]
            st.write(f"📅 错题时间：{datetime.fromisoformat(q['timestamp']).strftime('%Y-%m-%d')}")
            st.write(f"题目：{q['题目']}")
            if q.get("img_base64"):
                st.image(q["img_base64"], width=400, caption="原题照片")
            
            ans = st.text_input("请作答")
            if st.button("提交"):
                if ans != q["学生答案"]:
                    st.success("回答正确！")
                    del users[username]["wrong_questions"][0]
                    save_users(users)
                    st.rerun()
                else:
                    st.warning("回答错误，再想想！提示：" + q["提示"])

    if menu == "作业返回":
        st.subheader("📄 我的作业PDF")
        my_pdfs = user.get("finished_homeworks", [])
        if not my_pdfs:
            st.success("暂无已完成的作业")
        else:
            for pdf in sorted(my_pdfs, key=lambda x: x["timestamp"], reverse=True):
                st.write(f"📅 {datetime.fromisoformat(pdf['timestamp']).strftime('%Y-%m-%d')}")
                b64 = base64.b64encode(pdf["pdf_data"]).decode()
                href = f'<a href="data:application/pdf;base64,{b64}" download="我的作业_{datetime.fromisoformat(pdf["timestamp"]).strftime("%Y%m%d")}.pdf">下载我的作业PDF</a>'
                st.markdown(href, unsafe_allow_html=True)
                st.divider()

st.caption("✅ 分级权限｜API授权｜PDF作业批改｜作业返回｜变型题｜错题归档")
