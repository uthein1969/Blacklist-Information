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

    st.header("🚫 Black List Information Management")
    
    # Tab ၂ ခု ခွဲလိုက်ပါမယ် - တစ်ခုက Data သွင်းဖို့၊ တစ်ခုက Data ကြည့်ဖို့
    tab1, tab2 = st.tabs(["➕ Add New Record", "📊 View Records"])

    with tab1:
        st.subheader("Add Information to Blacklist")
        with st.form("entry_form", clear_on_submit=True):
            name = st.text_input("အမည် (Full Name)")
            nrc = st.text_input("မှတ်ပုံတင်အမှတ် (NRC)")
            reason = st.text_area("အကြောင်းရင်း (Reason)")
            
            submitted = st.form_submit_button("Save Data")
            
            if submitted:
                if name and reason:
                    # Supabase ထဲသို့ Data သွင်းခြင်း
                    data = {
                        "full_name": name,
                        "nrc_number": nrc,
                        "reason": reason,
                        "blacklisted_by": st.session_state['user_info']['username']
                    }
                    response = supabase.table("blacklist_records").insert(data).execute()
                    st.success(f"{name} ၏ အချက်အလက်ကို သိမ်းဆည်းပြီးပါပြီ။")
                else:
                    st.warning("အမည်နှင့် အကြောင်းရင်းကို မဖြစ်မနေ ထည့်ပေးပါ။")

    with tab2:
        st.subheader("Blacklist Data")
        # Supabase မှ Data ပြန်ဆွဲထုတ်ခြင်း
        records = supabase.table("blacklist_records").select("*").execute()
        if records.data:
            st.table(records.data)
        else:
            st.write("ဒေတာ မရှိသေးပါ။")
# --- App Entry Point ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    login_form()
else:
    main_app()
