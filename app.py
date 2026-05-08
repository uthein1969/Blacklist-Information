import streamlit as st
from supabase import create_client, Client
import time

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

def translate_numbers(text):
    mm_nums = "၀၁၂၃၄၅၆၇၈၉"
    en_nums = "0123456789"
    # မြန်မာမှ အင်္ဂလိပ်သို့
    to_en = text.translate(str.maketrans(mm_nums, en_nums))
    # အင်္ဂလိပ်မှ မြန်မာသို့
    to_mm = text.translate(str.maketrans(en_nums, mm_nums))
    return to_en, to_mm
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
                    
                    msg_container = st.empty() # Message ပြမယ့် နေရာအလွတ်လေး ဆောက်လိုက်တယ်
                    msg_container.success(f"{name} ၏ အချက်အလက်ကို သိမ်းဆည်းပြီးပါပြီ။")
                    time.sleep(3) # ၃ စက္ကန့် စောင့်မယ်
                    msg_container.empty()
                else:
                    st.warning("အမည်နှင့် အကြောင်းရင်းကို မဖြစ်မနေ ထည့်ပေးပါ။")

    with tab2:
        st.subheader("📊 Blacklist Data")
        
        search_query = st.text_input("🔍 Search by NRC/PB (မြန်မာ/English နောက်ဆုံး ၆ လုံး)", placeholder="ဥပမာ - ၁၂၃၄၅၆ သို့မဟုတ် 123456 ")
        
        if search_query:
            # ဂဏန်းတွေကို နှစ်မျိုးလုံးပြောင်းလိုက်မယ်
            query_en, query_mm = translate_numbers(search_query)
            
            # Database မှာ or condition နဲ့ နှစ်မျိုးလုံးကို ရှာခိုင်းမယ်
            records = supabase.table("blacklist_records").select("*").or_(f"nrc_number.ilike.%{query_en},nrc_number.ilike.%{query_mm}").order("created_at", desc=True).execute()
        else:
            records = supabase.table("blacklist_records").select("*").order("created_at", desc=True).execute()
        
        if records.data:
            st.write(f"တွေ့ရှိသည့် အရေအတွက်: {len(records.data)} ခု")
            # enumerate ကို အသုံးပြုပြီး loop ပတ်ပါမယ် (i က နံပါတ်စဉ်ပါ)
            for i, record in enumerate(records.data, start=1):
                # NRC/PB ခွဲခြားသည့် Logic
                raw_nrc = str(record['nrc_number']).strip()
                prefix = "NRC" if raw_nrc and raw_nrc[0].isdigit() else "PB"
                
                # Expander တွင် နံပါတ်စဉ် {i} ကိုပါ ထည့်သွင်းပြသခြင်း
                with st.expander(f"{i} 👤 {record['full_name']} ({prefix}: {raw_nrc})"):
                    # Edit mode သတ်မှတ်ခြင်း
                    edit_key = f"edit_mode_{record['id']}"
                    if edit_key not in st.session_state:
                        st.session_state[edit_key] = False
                    
                    # ဒီနေရာမှာ အရှေ့က View/Edit Form code တွေကို ဆက်ရေးပါ
                    # ...

                    # Edit Mode မဟုတ်ရင် (ပုံမှန်ပြသရန်)
                    if not st.session_state[edit_key]:
                        st.write(f"**Reason:** {record['reason']}")
                        st.write(f"**Listed by:** {record['blacklisted_by']}")
                        st.write(f"**Company:** {record['Remark1']}")
                        st.write(f"**Address:** {record['Remark2']}")
                        
                        if st.session_state['user_info']['username'] == 'admin':
                            col1, col2 = st.columns(2)
                            with col1:
                                if st.button("📝 Edit", key=f"btn_edit_{record['id']}"):
                                    st.session_state[edit_key] = True # ဒီမှာ သုံးထားလို့ အပေါ်မှာ အရင်ကြေညာရတာပါ
                                    st.rerun()
                            with col2:
                                if st.button("🗑️ Delete", key=f"btn_del_{record['id']}"):
                                    supabase.table("blacklist_records").delete().eq("id", record["id"]).execute()
                                    st.success("Data ဖျက်ပြီးပါပြီ။")
                                    time.sleep(1)
                                    st.rerun()
                    
                    # Edit Mode ဖြစ်နေလျှင် (Form ပြရန်)
                    else:
                        with st.form(key=f"form_edit_{record['id']}"):
                            new_name = st.text_input("Name", value=record['full_name'])
                            new_nrc = st.text_input("NRC", value=record['nrc_number'])
                            new_reason = st.text_area("Reason", value=record['reason'])
                            
                            f_col1, f_col2 = st.columns(2)
                            with f_col1:
                                if st.form_submit_button("✅ Update"):
                                    update_data = {"full_name": new_name, "nrc_number": new_nrc, "reason": new_reason}
                                    supabase.table("blacklist_records").update(update_data).eq("id", record["id"]).execute()
                                    st.session_state[edit_key] = False
                                    st.success("ပြင်ဆင်ပြီးပါပြီ။")
                                    time.sleep(1)
                                    st.rerun()
                            with f_col2:
                                if st.form_submit_button("❌ Cancel"):
                                    st.session_state[edit_key] = False
                                    st.rerun()
        else:
            st.write("ဒေတာ မရှိသေးပါ။")
# --- App Entry Point ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    login_form()
else:
    main_app()
