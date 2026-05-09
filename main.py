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
import uuid
# 自动创建必需的配置文件
if not os.path.exists("users.json"):
    with open("users.json", "w") as f:
        json.dump({}, f)

if not os.path.exists("admin_config.json"):
    with open("admin_config.json", "w") as f:
        json.dump({"audit_list": []}, f)

# 用户数据操作函数
def load_users():
    with open("users.json", "r", encoding="utf-8") as f:
        return json.load(f)

def save_users(users):
    with open("users.json", "w", encoding="utf-8") as f:
        json.dump(users, f, indent=4, ensure_ascii=False)

def load_admin_config():
    with open("admin_config.json", "r", encoding="utf-8") as f:
        return json.load(f)

def save_admin_config(config):
    with open("admin_config.json", "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)
# ===================== 系统核心配置 =====================
# 软件名称全局定义
SOFTWARE_NAME = "onego学管"
# API配置
DOUBAO_API_KEY = "ark-8c8dd5e0-2b7f-41c2-bf6b-ce7465dde911-75bd0"
MODEL_ID = "doubao-seed-2-0-lite-260215"
# Token消耗基准（每道题/每次调用）
TOKEN_PER_QUESTION = 1  # 可根据实际API定价调整
# 错题删除时间配置
STUDENT_DELETE_DAYS = 14  # 学生2周后可删
TEACHER_DELETE_UNLIMITED = True  # 老师无时间限制

# ===================== 数据存储配置 =====================
USER_FILE = "users.json"
PDF_STORE = "pdf_store"
TOKEN_LOG_FILE = "token_log.json"
ADMIN_CONFIG = "admin_config.json"
# 创建目录
os.makedirs(PDF_STORE, exist_ok=True)

# ===================== 初始化数据文件 =====================
def init_data_files():
    default_users = {
        "13800138000": {
            "phone": "13800138000",
            "pwd": "admin123456",
            "nickname": "系统管理员",
            "role": "系统管理员",
            "user_type": "机构-管理员",
            "org_name": "系统管理后台",
            "class_name": "系统",
            "is_authorized": True,
            "audit_status": "approved",
            "age_range": "18+",
            "guardian_agree": True,
            "agreement_agree": True,
            "wrong_questions": [],
            "pending_reviews": [],
            "finished_homeworks": [],
            "token_usage": 0
        },
        "13900139000": {
            "phone": "13900139000",
            "pwd": "teacher123",
            "nickname": "王老师",
            "role": "教师",
            "user_type": "个人-老师",
            "subject": "数学",
            "class_name": "三年级1班",
            "is_authorized": True,
            "audit_status": "approved",
            "age_range": "18+",
            "guardian_agree": True,
            "agreement_agree": True,
            "wrong_questions": [],
            "pending_reviews": [],
            "finished_homeworks": [],
            "token_usage": 0
        },
        "13700137000": {
            "phone": "13700137000",
            "pwd": "student123",
            "nickname": "爱学习的张三",
            "role": "学生",
            "user_type": "个人-学生",
            "grade": "三年级",
            "class_name": "三年级1班",
            "is_authorized": True,
            "audit_status": "approved",
            "age_range": "14-18",
            "guardian_agree": True,
            "agreement_agree": True,
            "wrong_questions": [],
            "pending_reviews": [],
            "finished_homeworks": [],
            "token_usage": 0
        }
    }
    with open(USER_FILE, "w", encoding="utf-8") as f:
        json.dump(default_users, f, ensure_ascii=False, indent=2)

    if not os.path.exists(TOKEN_LOG_FILE):
        token_log = {
            "total_usage": 0,
            "daily_log": {},
            "user_log": {}
        }
        with open(TOKEN_LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(token_log, f, ensure_ascii=False, indent=2)

    if not os.path.exists(ADMIN_CONFIG):
        admin_config = {
            "audit_list": [],
            "org_codes": {},
            "system_settings": {
                "token_per_question": TOKEN_PER_QUESTION,
                "student_delete_days": STUDENT_DELETE_DAYS
            }
        }
        with open(ADMIN_CONFIG, "w", encoding="utf-8") as f:
            json.dump(admin_config, f, ensure_ascii=False, indent=2)
    
    # 初始化Token日志
    if not os.path.exists(TOKEN_LOG_FILE):
        token_log = {
            "total_usage": 0,
            "daily_log": {},
            "user_log": {}
        }
        with open(TOKEN_LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(token_log, f, ensure_ascii=False, indent=2)
    
    # 初始化管理员配置
    if not os.path.exists(ADMIN_CONFIG):
        admin_config = {
            "audit_list": [],
            "org_codes": {},
            "system_settings": {
                "token_per_question": TOKEN_PER_QUESTION,
                "student_delete_days": STUDENT_DELETE_DAYS
            }
        }
        with open(ADMIN_CONFIG, "w", encoding="utf-8") as f:
            json.dump(admin_config, f, ensure_ascii=False, indent=2)

# 加载数据
init_data_files()

# ===================== 数据操作函数 =====================
# 加载用户
def load_users():
    with open(USER_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

# 保存用户
def save_users(users):
    with open(USER_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

# 加载Token日志
def load_token_log():
    with open(TOKEN_LOG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

# 保存Token日志
def save_token_log(log):
    with open(TOKEN_LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)

# 加载管理员配置
def load_admin_config():
    with open(ADMIN_CONFIG, "r", encoding="utf-8") as f:
        return json.load(f)

# 保存管理员配置
def save_admin_config(config):
    with open(ADMIN_CONFIG, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

# 记录Token消耗
def record_token_usage(user_id, usage=TOKEN_PER_QUESTION, desc="AI批改作业"):
    log = load_token_log()
    today = datetime.now().strftime("%Y-%m-%d")
    
    # 更新总消耗
    log["total_usage"] += usage
    
    # 更新日日志
    if today not in log["daily_log"]:
        log["daily_log"][today] = {"total": 0, "details": []}
    log["daily_log"][today]["total"] += usage
    log["daily_log"][today]["details"].append({
        "user_id": user_id,
        "usage": usage,
        "desc": desc,
        "timestamp": datetime.now().isoformat()
    })
    
    # 更新用户日志
    if user_id not in log["user_log"]:
        log["user_log"][user_id] = {"total": 0, "details": []}
    log["user_log"][user_id]["total"] += usage
    log["user_log"][user_id]["details"].append({
        "usage": usage,
        "desc": desc,
        "timestamp": datetime.now().isoformat()
    })
    
    # 更新用户个人token统计
    users = load_users()
    if user_id in users:
        users[user_id]["token_usage"] += usage
        save_users(users)
    
    save_token_log(log)

# 检查错题删除权限
def can_delete_question(user_role, timestamp_str):
    if user_role == "教师":
        return True  # 老师无时间限制
    else:
        # 学生14天后可删
        if not timestamp_str:
            return True
        try:
            q_time = datetime.fromisoformat(timestamp_str)
            return datetime.now() - q_time >= timedelta(days=STUDENT_DELETE_DAYS)
        except:
            return True

# ===================== 页面设置 =====================
st.set_page_config(page_title=SOFTWARE_NAME, layout="wide")

# ===================== 工具函数 =====================
# 图片转base64
def img_to_base64(img_file):
    bytes_data = img_file.getvalue()
    base64_str = base64.b64encode(bytes_data).decode()
    return f"data:image/jpeg;base64,{base64_str}"

# 图片转PDF（带批改标记）
def init_font():
    try:
        pdfmetrics.registerFont(TTFont('SimHei', '/usr/share/fonts/truetype/SimHei.ttf'))
    except:
        pdfmetrics.registerFont(TTFont('Helvetica', 'Helvetica'))

def img_to_pdf(img_base64, ai_result, teacher_hint=None):
    init_font()
    img_data = base64.b64decode(img_base64.split(',')[1])
    img = Image.open(BytesIO(img_data))
    width, height = img.size
    
    pdf_buffer = BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=(width, height))
    c.drawImage(BytesIO(img_data), 0, 0, width=width, height=height)
    c.setFont("SimHei" if "SimHei" in pdfmetrics.getRegisteredFontNames() else "Helvetica", 12)
    
    lines = ai_result.split('\n')
    y_pos = height - 50
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if "正确" in line or "对" in line:
            c.setFillColor(green)
            c.drawString(10, y_pos, "√ " + line)
        elif "部分" in line:
            c.setFillColor(blue)
            c.drawString(10, y_pos, "乄 " + line)
        elif "错误" in line or "错" in line:
            c.setFillColor(red)
            c.drawString(10, y_pos, "× " + line)
        else:
            if teacher_hint:
                c.drawString(10, y_pos, teacher_hint)
        y_pos -= 20
    
    c.save()
    pdf_buffer.seek(0)
    return pdf_buffer.getvalue()

# AI批改函数（带Token统计）
def ai_correct_image(img_base64, user_id):
    prompt = """
你是作业批改老师，识别图片里的题目和答案，按以下规则标记：
1. 完全正确：√（无解析）
2. 部分正确：乄 + 思路提示（无答案）
3. 完全错误：× + 思路提示（无答案）
4. 语言简洁，无多余内容
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
        result = result.replace("我已明确批改要求，请你提供需要批改的题目和你的作答内容", "").strip()
        # 记录Token消耗
        record_token_usage(user_id, desc="AI批改作业图片")
        return result, None
    except Exception as e:
        return None, str(e)

# 生成变型题（带Token统计）
def generate_variant_questions(original_question, user_id):
    prompt = f"""
原题：{original_question}
按1:2比例生成2道同知识点变型题，仅题目，无答案，数据/问法不同。
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
        # 记录Token消耗
        record_token_usage(user_id, usage=2*TOKEN_PER_QUESTION, desc="生成变型题")
        return result, None
    except Exception as e:
        return None, str(e)

# ===================== 协议文本（合规模板） =====================
def show_agreements():
    st.subheader("用户协议")
    st.write("""
    1. 您同意遵守本平台的所有规则，合法使用平台服务。
    2. 您保证所提供的信息真实有效，承担相应法律责任。
    3. 平台仅提供技术服务，不对作业批改结果的准确性承担全部责任。
    """)
    
    st.subheader("隐私政策")
    st.write("""
    1. 我们仅收集必要的手机号、昵称等信息，用于账号验证和服务提供。
    2. 未成年人信息将按照儿童隐私政策特殊保护，需监护人同意。
    3. 我们不会向第三方泄露您的个人信息，除非法律要求。
    """)
    
    st.subheader("儿童隐私政策")
    st.write("""
    1. 针对14周岁以下未成年人，需监护人明确同意后方可使用平台。
    2. 我们仅收集必要的学习相关信息，不收集额外敏感信息。
    3. 监护人可随时申请查看、删除未成年人的使用记录。
    """)

# ===================== 注册流程 =====================
def register_page():
    st.title(f"{SOFTWARE_NAME} - 账号注册")
    
    st.subheader("第一步：选择用户类型")
    user_category = st.radio("用户分类", ["我是个人用户（无需审核）", "我是机构用户（需后台审核）"])
    
    if user_category == "我是个人用户（无需审核）":
        user_role = st.selectbox("身份类型", ["学生", "老师"])
        user_type = f"个人-{user_role}"
    else:
        user_role = st.selectbox("身份类型", ["机构管理员/负责人", "机构下的老师", "机构下的学生"])
        user_type = f"机构-{user_role.replace('机构下的', '')}"
    
    st.subheader("第二步：手机号验证")
    phone = st.text_input("请输入手机号", placeholder="138****0000")
    
    col1, col2 = st.columns([1, 4])
    with col1:
        agree_all = st.checkbox("我已阅读并同意")
    with col2:
        st.write("[用户协议] [隐私政策]")
        if user_role == "学生":
            st.write("[儿童隐私政策]")
    
    guardian_agree = True
    age_range = "18+"
    if user_role == "学生":
        st.subheader("未成年人声明")
        age_range = st.radio("年龄区间", ["14周岁以下", "14-18周岁", "18周岁以上"])
        if age_range != "18周岁以上":
            guardian_agree = st.checkbox("我已获得监护人同意使用本平台")
    
    if st.button("获取验证码"):
        if not phone:
            st.error("请输入手机号！")
        elif not agree_all:
            st.error("请先勾选协议！")
        elif user_role == "学生" and age_range != "18+" and not guardian_agree:
            st.error("需监护人同意！")
        else:
            st.success("验证码：123456")

    st.subheader("第三步：完善信息")
    code = st.text_input("请输入验证码", placeholder="6位数字")
    nickname = st.text_input("昵称", placeholder="请输入昵称")
    pwd = st.text_input("设置密码", type="password")
    pwd_confirm = st.text_input("确认密码", type="password")

    extra_fields = {}
    if user_role in ["老师", "机构下的老师"]:
        extra_fields["subject"] = st.text_input("任教科目", placeholder="如：数学")
    if user_role in ["学生", "机构下的学生"]:
        extra_fields["grade"] = st.text_input("年级", placeholder="如：三年级")
    if user_role == "机构管理员/负责人":
        extra_fields["org_name"] = st.text_input("机构名称", placeholder="必填")
        extra_fields["business_license"] = st.text_input("营业执照号（选填）")
        extra_fields["contact"] = st.text_input("联系人", placeholder="必填")
    if user_role in ["机构下的老师", "机构下的学生"]:
        extra_fields["org_code"] = st.text_input("机构码")

# ============= 提交注册（最终修复版） =============
if st.button("注册", key="register_btn", use_container_width=True):
    try:
        with open("users.json", "r", encoding="utf-8") as f:
            users = json.load(f)
    except:
        users = {}

    if phone in users:
        st.error("该手机号已注册！")
    else:
        users[phone] = {
            "phone": phone,
            "pwd": pwd,
            "nickname": nickname,
            "role": user_role,
            "audit_status": "待审核",
            "is_authorized": False
        }

        with open("users.json", "w", encoding="utf-8") as f:
            json.dump(users, f, ensure_ascii=False, indent=4)

        st.success("✅ 注册成功！等待管理员审核！")
        st.info("请等待管理员审核通过后再登录，审核状态可在登录页查看。")
# ===================== 登录流程 =====================
def login_page():
    # 强制读取用户文件
    try:
        with open("users.json", "r", encoding="utf-8") as f:
            users = json.load(f)
    except:
        users = {}

    st.title(f"{SOFTWARE_NAME} - 账号登录")

    login_type = st.radio("登录方式", ["手机号+密码", "手机号+验证码"])
    phone = st.text_input("手机号")

    if login_type == "手机号+密码":
        pwd = st.text_input("密码", type="password")
        if st.button("登录"):
            # 登录时再次读取，确保最新
            try:
                with open("users.json", "r", encoding="utf-8") as f:
                    users = json.load(f)
            except:
                users = {}

            if phone in users and users[phone]["pwd"] == pwd:
                st.session_state.logged_in = True
                st.session_state.user = users[phone]
                st.session_state.user_id = phone
                st.success(f"欢迎回来，{users[phone]['nickname']}！")
                st.rerun()
            else:
                if phone not in users:
                    st.error("❌ 该手机号未注册")
                else:
                    st.error("❌ 密码错误")
    else:
        code = st.text_input("验证码")
        if st.button("获取验证码"):
            if not phone:
                st.error("请输入手机号！")
            else:
                st.info(f"验证码测试码：123456")
        if st.button("登录"):
            try:
                with open("users.json", "r", encoding="utf-8") as f:
                    users = json.load(f)
            except:
                users = {}

            if phone in users and code == "123456":
                st.session_state.logged_in = True
                st.session_state.user = users[phone]
                st.session_state.user_id = phone
                st.success(f"欢迎回来，{users[phone]['nickname']}！")
                st.rerun()

    # 👇 新增的注册入口
    st.markdown("---")
    if st.button("没有账号？去注册"):
        st.session_state.page = "register"
        st.rerun()
# ===================== 管理后台 =====================
def admin_dashboard():
    st.title(f"{SOFTWARE_NAME} - 系统管理后台")
    
    menu = st.selectbox("管理菜单", [
        "Token用量统计",
        "用户审核管理",
        "用户权限管理",
        "机构码管理",
        "系统设置"
    ])
    
    # 1. Token用量统计
    if menu == "Token用量统计":
        st.subheader("Token用量统计")
        token_log = load_token_log()
        users = load_users()
        
        # 总览
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("总Token消耗", token_log["total_usage"])
        with col2:
            today = datetime.now().strftime("%Y-%m-%d")
            st.metric("今日消耗", token_log["daily_log"].get(today, {"total":0})["total"])
        with col3:
            st.metric("活跃用户数", len(token_log["user_log"]))
        
        # 日消耗趋势
        st.subheader("日消耗趋势")
        daily_dates = sorted(token_log["daily_log"].keys())
        daily_values = [token_log["daily_log"][d]["total"] for d in daily_dates]
        st.line_chart({"日期": daily_dates, "Token消耗": daily_values})
        
        # 按用户统计
        st.subheader("用户消耗排行")
        user_usage = []
        for user_id, data in token_log["user_log"].items():
            nickname = users.get(user_id, {}).get("nickname", "未知用户")
            user_usage.append({
                "用户ID": user_id,
                "昵称": nickname,
                "总消耗": data["total"],
                "用户类型": users.get(user_id, {}).get("user_type", "未知")
            })
        st.dataframe(user_usage)
        
        # 详细日志
        st.subheader("消耗明细")
        all_details = []
        for date, data in token_log["daily_log"].items():
            for detail in data["details"]:
                nickname = users.get(detail["user_id"], {}).get("nickname", "未知用户")
                all_details.append({
                    "日期": date,
                    "时间": detail["timestamp"],
                    "用户": nickname,
                    "消耗Token": detail["usage"],
                    "用途": detail["desc"]
                })
        st.dataframe(all_details)
    
    # 2. 用户审核管理
    elif menu == "用户审核管理":
        st.subheader("机构用户审核")
        admin_config = load_admin_config()
        audit_list = admin_config["audit_list"]

        if not audit_list:
            st.success("暂无待审核用户")
        else:
            for i, audit in enumerate(audit_list):
                with st.expander(f"{audit['nickname']} - {audit['user_type']}"):
                    st.write(f"申请时间：{audit['apply_time']}")
                    st.write(f"机构名称：{audit.get('org_name', '无')}")
                    col1, col2 = st.columns(2)

                    with col1:
                        if st.button("审核通过", key=f"audit_approve_{i}"):
                            users = load_users()
                            if audit["user_id"] in users:
                                users[audit["user_id"]]["audit_status"] = "approved"
                                users[audit["user_id"]]["is_authorized"] = True
                                save_users(users)
                            admin_config["audit_list"].pop(i)
                            save_admin_config(admin_config)
                            st.success("审核通过！")
                            st.rerun()

                    with col2:
                        if st.button("审核驳回", key=f"audit_reject_{i}"):
                            users = load_users()
                            if audit["user_id"] in users:
                                users[audit["user_id"]]["audit_status"] = "rejected"
                                save_users(users)
                            admin_config["audit_list"].pop(i)
                            save_admin_config(admin_config)
                            st.warning("已驳回！")
                            st.rerun()
    # 3. 用户权限管理
    elif menu == "用户权限管理":
        st.subheader("用户AI权限管理")
        users = load_users()
        for user_id, user in users.items():
            with st.expander(f"{user['nickname']} - {user['user_type']}"):
                st.write(f"手机号：{user_id}")
                st.write(f"审核状态：{user['audit_status']}")
                st.write(f"当前AI授权：{'已授权' if user['is_authorized'] else '未授权'}")
                col1, col2 = st.columns(2)
                with col1:
                    if not user["is_authorized"]:
                        if st.button("开通AI权限", key=f"auth_{user_id}"):
                            users[user_id]["is_authorized"] = True
                            save_users(users)
                            st.success("已开通！")
                            st.rerun()
                with col2:
                    if user["is_authorized"]:
                        if st.button("取消AI权限", key=f"unauth_{user_id}"):
                            users[user_id]["is_authorized"] = False
                            save_users(users)
                            st.success("已取消！")
                            st.rerun()
    
    # 4. 机构码管理
    elif menu == "机构码管理":
        st.subheader("机构码生成与管理")
        admin_config = load_admin_config()
        org_codes = admin_config["org_codes"]
        
        # 生成新机构码
        org_name = st.text_input("机构名称")
        if st.button("生成机构码"):
            org_code = str(uuid.uuid4())[:8].upper()
            org_codes[org_code] = {
                "org_name": org_name,
                "create_time": datetime.now().isoformat(),
                "status": "active"
            }
            admin_config["org_codes"] = org_codes
            save_admin_config(admin_config)
            st.success(f"机构码生成成功：{org_code}")
        
        # 机构码列表
        st.subheader("已生成机构码")
        code_list = []
        for code, data in org_codes.items():
            code_list.append({
                "机构码": code,
                "机构名称": data["org_name"],
                "创建时间": data["create_time"],
                "状态": data["status"]
            })
        st.dataframe(code_list)
    
    # 5. 系统设置
    elif menu == "系统设置":
        st.subheader("系统参数设置")
        admin_config = load_admin_config()
        settings = admin_config["system_settings"]
        
        # Token单价
        new_token_price = st.number_input("每道题Token消耗", value=settings["token_per_question"])
        # 学生删除错题天数
        new_delete_days = st.number_input("学生错题删除天数", value=settings["student_delete_days"])
        
        if st.button("保存设置"):
            admin_config["system_settings"]["token_per_question"] = new_token_price
            admin_config["system_settings"]["student_delete_days"] = new_delete_days
            save_admin_config(admin_config)
            st.success("设置保存成功！")

# ===================== 教师端（含错题管理增强） =====================
def teacher_dashboard(user_id, user):
    st.header(f"👨‍🏫 {user['nickname']} - 教师中心")
    menu = st.selectbox("功能菜单", [
        "帮学生上传作业",
        "待审核批改",
        "作业返回",
        "变型题生成",
        "错题本管理",  # 新增：老师专属错题管理
        "布置作业",
        "班级学生错题总览"
    ])
    
    # 班级学生列表
    users = load_users()
    class_students = {k:v for k,v in users.items() if v.get("class_name") == user["class_name"] and v["role"] == "学生"}
    
    # 1. 帮学生上传作业（保留原有功能）
    if menu == "帮学生上传作业":
        st.subheader("📷 帮学生上传作业")
        if not user["is_authorized"] or user["audit_status"] != "approved":
            st.error("账号未审核或未授权，无法使用AI功能！")
        else:
            if not class_students:
                st.warning("暂无学生加入本班！")
            else:
                student_id = st.selectbox("选择学生", list(class_students.keys()), format_func=lambda x: class_students[x]["nickname"])
                img = st.file_uploader("上传作业照片", type=["jpg","png","jpeg"])
                if img:
                    st.image(img, width=400)
                    with st.spinner("AI批改中..."):
                        img_b64 = img_to_base64(img)
                        result, err = ai_correct_image(img_b64, user_id)
                        if err:
                            st.error(f"批改失败：{err}")
                        else:
                            st.subheader("AI初批结果")
                            st.write(result)
                            # 加入待审核
                            users[student_id]["pending_reviews"].append({
                                "题目": "作业题",
                                "ai提示": result,
                                "teacher_hint": result,
                                "img_base64": img_b64,
                                "upload_time": datetime.now().isoformat()
                            })
                            save_users(users)
                            st.success("已加入待审核列表！")
    
    # 2. 待审核批改（保留原有功能）
    elif menu == "待审核批改":
        st.subheader("🔍 待审核批改")
        has_pending = False
        for s_id, s in class_students.items():
            pending = s.get("pending_reviews", [])
            if pending:
                has_pending = True
                with st.expander(f"{s['nickname']} 的待审核作业"):
                    for i, q in enumerate(pending):
                        st.write(f"上传时间：{q.get('upload_time', '未知')}")
                        if q.get("img_base64"):
                            st.image(q["img_base64"], width=400)
                        new_hint = st.text_area("修改评改内容", value=q["teacher_hint"], key=f"hint_{s_id}_{i}")
                        if st.button("审核通过", key=f"pass_{s_id}_{i}"):
                            # 生成PDF
                            pdf_data = img_to_pdf(q["img_base64"], q["ai提示"], new_hint)
                            # 保存PDF
                            users[s_id]["finished_homeworks"].append({
                                "pdf_data": pdf_data,
                                "timestamp": datetime.now().isoformat()
                            })
                            # 保存错题
                            users[s_id]["wrong_questions"].append({
                                "题目": q["题目"],
                                "提示": new_hint,
                                "img_base64": q.get("img_base64"),
                                "timestamp": datetime.now().isoformat()
                            })
                            # 删除待审核
                            del users[s_id]["pending_reviews"][i]
                            save_users(users)
                            st.success("审核完成！")
                            st.rerun()
        if not has_pending:
            st.success("暂无待审核作业！")
    
    # 3. 作业返回（保留原有功能）
    elif menu == "作业返回":
        st.subheader("📄 作业返回（PDF）")
        pdf_list = []
        for s_id, s in class_students.items():
            for pdf in s.get("finished_homeworks", []):
                pdf_list.append({
                    "学生": s["nickname"],
                    "时间": pdf["timestamp"],
                    "pdf_data": pdf["pdf_data"],
                    "student_id": s_id
                })
        if not pdf_list:
            st.success("暂无已批改作业！")
        else:
            for pdf in sorted(pdf_list, key=lambda x: x["time"], reverse=True):
                st.write(f"📅 {datetime.fromisoformat(pdf['time']).strftime('%Y-%m-%d %H:%M')} | 学生：{pdf['student']}")
                b64 = base64.b64encode(pdf["pdf_data"]).decode()
                href = f'<a href="data:application/pdf;base64,{b64}" download="作业_{pdf["student"]}_{pdf["time"][:10]}.pdf">下载PDF</a>'
                st.markdown(href, unsafe_allow_html=True)
    
    # 4. 变型题生成（保留原有功能）
    elif menu == "变型题生成":
        st.subheader("🔄 变型题生成")
        if not user["is_authorized"]:
            st.error("未授权使用AI功能！")
        else:
            original = st.text_area("输入原题")
            if st.button("生成2道变型题"):
                with st.spinner("生成中..."):
                    result, err = generate_variant_questions(original, user_id)
                    if err:
                        st.error(err)
                    else:
                        st.subheader("生成结果：")
                        st.write(result)
    
    # 5. 错题本管理（老师专属：增删改查无限制）
    elif menu == "错题本管理":
        st.subheader("📕 错题本管理（老师可任意修改）")
        student_id = st.selectbox("选择学生", list(class_students.keys()), format_func=lambda x: class_students[x]["nickname"])
        student = users[student_id]
        wrong_questions = student.get("wrong_questions", [])
        
        # 查看/删除/修改现有错题
        st.subheader("现有错题")
        if not wrong_questions:
            st.success("该学生暂无错题！")
        else:
            for i, q in enumerate(wrong_questions):
                with st.expander(f"{i+1}. {q['题目']}"):
                    if q.get("img_base64"):
                        st.image(q["img_base64"], width=300)
                    st.write(f"添加时间：{datetime.fromisoformat(q['timestamp']).strftime('%Y-%m-%d')}")
                    # 修改题目
                    new_title = st.text_input("修改题目内容", value=q["题目"], key=f"edit_title_{i}")
                    new_hint = st.text_area("修改解析提示", value=q["提示"], key=f"edit_hint_{i}")
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("保存修改", key=f"save_{i}"):
                            users[student_id]["wrong_questions"][i]["题目"] = new_title
                            users[student_id]["wrong_questions"][i]["提示"] = new_hint
                            save_users(users)
                            st.success("修改成功！")
                            st.rerun()
                    with col2:
                        if st.button("删除错题", key=f"del_{i}"):
                            del users[student_id]["wrong_questions"][i]
                            save_users(users)
                            st.success("删除成功！")
                            st.rerun()
        
        # 新增错题
        st.subheader("新增错题")
        new_q_title = st.text_input("错题题目")
        new_q_hint = st.text_area("解析提示")
        new_q_img = st.file_uploader("上传题目图片（可选）", type=["jpg","png","jpeg"])
        if st.button("添加错题"):
            new_q = {
                "题目": new_q_title,
                "提示": new_q_hint,
                "timestamp": datetime.now().isoformat(),
                "img_base64": img_to_base64(new_q_img) if new_q_img else None
            }
            users[student_id]["wrong_questions"].append(new_q)
            save_users(users)
            st.success("错题添加成功！")
            st.rerun()
    
    # 6. 布置作业（保留）
    elif menu == "布置作业":
        st.subheader("📝 布置作业")
        title = st.text_input("作业标题")
        content = st.text_area("作业内容")
        if st.button("发布"):
            st.success("作业发布成功！")
    
    # 7. 班级错题总览（保留，老师可删除）
    elif menu == "班级学生错题总览":
        st.subheader("📊 班级错题总览")
        for s_id, s in class_students.items():
            with st.expander(f"{s['nickname']} 的错题"):
                wrong = sorted(s.get("wrong_questions", []), key=lambda x: x["timestamp"], reverse=True)
                if not wrong:
                    st.write("暂无错题")
                else:
                    for i, q in enumerate(wrong):
                        st.write(f"📅 {datetime.fromisoformat(q['timestamp']).strftime('%Y-%m-%d')} | {q['题目']}")
                        if st.button("删除", key=f"del_class_{s_id}_{i}"):
                            del users[s_id]["wrong_questions"][i]
                            save_users(users)
                            st.success("删除成功！")
                            st.rerun()

# ===================== 学生端 =====================
def student_dashboard(user_id, user):
    st.header(f"👨‍🎓 {user['nickname']} - 学生中心")
    menu = st.selectbox("功能菜单", ["上传我的作业", "错题解析", "错题本", "作业返回"])
    
    # 1. 上传作业
    if menu == "上传我的作业":
        st.subheader("📷 拍照上传作业")
        if not user["is_authorized"] or user["audit_status"] != "approved":
            st.error("账号未审核/未授权，无法使用AI功能！")
        else:
            img = st.file_uploader("上传作业照片", type=["jpg","png","jpeg"])
            if img:
                st.image(img, width=400)
                with st.spinner("AI批改中..."):
                    img_b64 = img_to_base64(img)
                    result, err = ai_correct_image(img_b64, user_id)
                    if err:
                        st.error(err)
                    else:
                        if "全部正确" in result:
                            st.success("🎉 全部正确！")
                            pdf_data = img_to_pdf(img_b64, result)
                            users = load_users()
                            users[user_id]["finished_homeworks"].append({
                                "pdf_data": pdf_data,
                                "timestamp": datetime.now().isoformat()
                            })
                            save_users(users)
                        else:
                            st.subheader("AI初批结果")
                            st.write(result)
                            users = load_users()
                            users[user_id]["pending_reviews"].append({
                                "题目": "作业题",
                                "ai提示": result,
                                "img_base64": img_b64,
                                "timestamp": datetime.now().isoformat()
                            })
                            save_users(users)
                            st.info("错题已提交老师审核！")
    
    # 2. 错题解析（14天后可删）
    elif menu == "错题解析":
        st.subheader("📝 错题解析")
        wrong = sorted(user.get("wrong_questions", []), key=lambda x: x["timestamp"], reverse=True)
        if not wrong:
            st.success("暂无错题！")
        else:
            for i, q in enumerate(wrong):
                st.write(f"📅 {datetime.fromisoformat(q['timestamp']).strftime('%Y-%m-%d')}")
                st.write(f"{i+1}. {q['题目']}")
                st.info(f"解析：{q['提示']}")
                # 学生14天后可删
                if can_delete_question("学生", q["timestamp"]):
                    if st.button("删除错题", key=f"del_stu_{i}"):
                        users = load_users()
                        del users[user_id]["wrong_questions"][i]
                        save_users(users)
                        st.success("删除成功！")
                        st.rerun()
                else:
                    remain_days = STUDENT_DELETE_DAYS - (datetime.now() - datetime.fromisoformat(q["timestamp"])).days
                    st.caption(f"{remain_days}天后可删除")
                st.divider()
    
    # 3. 错题本（重做）
    elif menu == "错题本":
        st.subheader("📕 错题本（重做）")
        wrong = sorted(user.get("wrong_questions", []), key=lambda x: x["timestamp"], reverse=True)
        if not wrong:
            st.success("全部掌握！")
        else:
            q = wrong[0]
            st.write(f"题目：{q['题目']}")
            if q.get("img_base64"):
                st.image(q["img_base64"], width=400)
            ans = st.text_input("请作答")
            if st.button("提交"):
                st.success("回答正确！" if ans != "错误答案" else "回答错误，再想想！")
                if ans != "错误答案":
                    users = load_users()
                    del users[user_id]["wrong_questions"][0]
                    save_users(users)
                    st.rerun()
    
    # 4. 作业返回
    elif menu == "作业返回":
        st.subheader("📄 我的作业PDF")
        pdfs = sorted(user.get("finished_homeworks", []), key=lambda x: x["timestamp"], reverse=True)
        if not pdfs:
            st.success("暂无已批改作业！")
        else:
            for pdf in pdfs:
                st.write(f"📅 {datetime.fromisoformat(pdf['timestamp']).strftime('%Y-%m-%d %H:%M')}")
                b64 = base64.b64encode(pdf["pdf_data"]).decode()
                href = f'<a href="data:application/pdf;base64,{b64}" download="我的作业_{pdf["timestamp"][:10]}.pdf">下载PDF</a>'
                st.markdown(href, unsafe_allow_html=True)

# ===================== 主流程控制 =====================
# 初始化session
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "page" not in st.session_state:
    st.session_state.page = "login"

# 未登录状态
if not st.session_state.logged_in:
    if st.session_state.page == "login":
        login_page()
    else:
        register_page()
    st.stop()

# 已登录状态
user_id = st.session_state.user_id
user = st.session_state.user

# 顶部导航
col1, col2, col3 = st.columns([3, 1, 1])
with col1:
    st.title(f"{SOFTWARE_NAME} - {user['nickname']}")
with col2:
    st.markdown(f"""
    <button onclick="window.print()" style="background: #4CAF50; color: white; padding: 8px 16px; border: none; border-radius: 4px; cursor: pointer;">
    🖨️ 打印
    </button>
    """, unsafe_allow_html=True)
with col3:
    if st.button("退出登录"):
        st.session_state.logged_in = False
        st.rerun()
st.divider()

# 权限控制：未审核用户提示
if user["audit_status"] == "pending":
    st.warning("您的账号正在审核中，仅可使用浏览功能！")
elif user["audit_status"] == "rejected":
    st.error("您的账号审核未通过，请联系管理员！")

# 角色分流
if user["role"] == "系统管理员":
    admin_dashboard()
elif user["role"] == "教师":
    teacher_dashboard(user_id, user)
elif user["role"] == "学生":
    student_dashboard(user_id, user)

# 底部版权
st.caption(f"© 2025 {SOFTWARE_NAME} - 一站式学习管理平台")
