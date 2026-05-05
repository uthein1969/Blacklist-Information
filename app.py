import streamlit as st
from supabase import create_client, Client

# --- Supabase Configuration ---
# သင်၏ Supabase Project Settings ထဲမှ URL နှင့် API Key ကို ဒီနေရာမှာ ထည့်ပေးပါ
SUPABASE_URL = "https://batsowuihgwhxbboucpy.supabase.co"
SUPABASE_KEY = "sb_publishable_OBTOI4EioNVufb5akpDOwA_75EmAcWr"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def check_login(username, password):
    # 'users' table ထဲမှာ username နဲ့ password ကို စစ်ဆေးခြင်း
    # မှတ်ချက် - လက်တွေ့တွင် password ကို plain text မသိမ်းဘဲ hash လုပ်၍ သိမ်းသင့်သည်
    response = supabase.table("users").select("*").eq("username", username).eq("password", password).execute()
    return response.data

def login_form():
    st.title("🚫 Black List Information System")
    st.subheader("Login to access the system")

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit_button = st.form_submit_button("Login")

        if submit_button:
            user_data = check_login(username, password)
            if user_data:
                st.session_state["logged_in"] = True
                st.session_state["user_info"] = user_data[0]
                st.success("Login အောင်မြင်ပါတယ်!")
                st.rerun() # Page ကို refresh လုပ်ပြီး main content ပြရန်
            else:
                st.error("Username သို့မဟုတ် Password မှားယွင်းနေပါသည်။")

def main_app():
    st.sidebar.write(f"Welcome, {st.session_state['user_info']['username']}")
    if st.sidebar.button("Logout"):
        st.session_state["logged_in"] = False
        st.rerun()

    st.header("Black List Information Management")
    st.info("ယခုအခါ သင်သည် Black List စာရင်းများကို ကြည့်ရှု/ပြင်ဆင်နိုင်ပါပြီ။")
    # ဤနေရာတွင် Black List ရှာဖွေခြင်း၊ ထည့်သွင်းခြင်း လုပ်ဆောင်ချက်များ ဆက်ရေးနိုင်ပါသည်

# --- App Entry Point ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    login_form()
else:
    main_app()
