import streamlit as st
from supabase import create_client, Client
import time
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import streamlit as st
import datetime
import pytz

GOOGLE_SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1gyRkba-zWKZymQup952pMuX0hTg-r3Jl7q9DtpTFjAg/edit?gid=1494517596#gid=1494517596"

# --- Supabase Configuration ---
SUPABASE_URL = "https://batsowuihgwhxbboucpy.supabase.co"
SUPABASE_KEY = "sb_publishable_OBTOI4EioNVufb5akpDOwA_75EmAcWr"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ========================================================
# ⚙️ LIVE CONNECTION TOGGLE SWITCHES (ပိတ်/ဖွင့် စမ်းသပ်ရန် ခလုတ်များ)
# ========================================================
ENABLE_SUPABASE = True      # False ထားပါက Supabase ထဲသို့ Data မသိမ်းဘဲ ကျော်သွားမည်
ENABLE_GOOGLE_SHEET = True  # False ထားပါက Google Sheet ထဲသို့ Sync မလုပ်ဘဲ ကျော်သွားမည်

def check_login(username, password):
    # 'users' table ထဲမှာ username နဲ့ password ကို စစ်ဆေးခြင်း
    response = supabase.table("users").select("*").eq("username", username).eq("password", password).execute()
    return response.data



# ========================================================
# 🛡️ GOOGLE SHEETS REAL-TIME SYNC SYSTEM (SAFE HYBRID METHOD)
# ========================================================
import gspread
import streamlit as st
from oauth2client.service_account import ServiceAccountCredentials
import requests
import os  # 🎯 ဖိုင်ရှိ/မရှိ စစ်ဆေးရန်အတွက်

def get_google_sheet():
    import gspread
    import streamlit as st
    import os
    from google.oauth2.service_account import Credentials

    try:
        scopes = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive.file",
            "https://www.googleapis.com/auth/drive"
        ]
        
        # 🔑 လမ်းကြောင်းများကို စစ်ဆေးခြင်း
        local_key_path = "backup/google_key.json"
        render_key_path = "/etc/secrets/google_key.json"
        
        if os.path.exists(render_key_path):
            creds = Credentials.from_service_account_file(render_key_path, scopes=scopes)
        elif os.path.exists(local_key_path):
            creds = Credentials.from_service_account_file(local_key_path, scopes=scopes)
        else:
            st.error("❌ Google Cloud Key ဖိုင်ကို စနစ်ထဲတွင် ရှာမတွေ့ပါဗျာ။")
            return None
            
        client = gspread.authorize(creds)
        
        # 🎯 စာလုံးပေါင်း ကွက်တိမှန်ကန်သော Google Sheet URL အမှန် (I အစား l သို့ ပြင်ဆင်ပြီး)
        correct_url = "https://docs.google.com/spreadsheets/d/1gyRkba-zWKZymQup952pMuX0hTg-r3Jl7q9DtpTFjAg/edit?gid=1494517596#gid=1494517596"
        return client.open_by_url(correct_url)
        
    except Exception as e:
        st.error(f"❌ Google Sheet Connection Error: {str(e)}")
        return None

import requests

# 🎯 Imgur သို့ ပုံလှမ်းပို့မည့် စနစ် (Anonymous Public Upload)
def upload_to_imgur(file_bytes):
    try:
        # Imgur မူရင်း Anonymous Client ID (ဤအတိုင်း စမ်းသပ်နိုင်ပါသည်)
        client_id = "490646413a25b1a" 
        headers = {"Authorization": f"Client-ID {client_id}"}
        payload = {"image": file_bytes}
        
        response = requests.post("https://api.imgur.com/3/image", headers=headers, data=payload)
        res_data = response.json()
        
        if res_data.get("success"):
            return res_data["data"]["link"] # 🔗 Direct URL (e.g., https://i.imgur.com/AbCdEfG.png)
        else:
            print(f"❌ Imgur Upload Failed Response: {res_data}")
            return None
    except Exception as e:
        print(f"❌ Imgur Connection Error: {e}")
        return None

# 🎯 Supabase Database ကောင်း/မကောင်း Live စစ်ဆေးပေးမည့် စနစ်
def is_supabase_alive():
    if not ENABLE_SUPABASE:
        return False
    try:
        # Database ထဲသို့ ပေါ့ပေါ့ပါးပါး Query တစ်ခု လှမ်းပစ်ပြီး Status စစ်ခြင်း
        supabase.table("users").select("username").limit(1).execute()
        return True
    except Exception:
        return False

# ========================================================
# 🛡️ GOOGLE SHEETS REAL-TIME SYNC SYSTEM (COLUMN CORRECTED & LOGS SYNCED)
# ========================================================

# 🌟 ၁။ Data Add New ရောက်လာလျှင် Google Sheet ၌ အောက်ဆုံးတွင် တန်းထည့်မည့် စနစ်
def auto_sync_append_record(data_dict):
    try:
        # ကုဒ်ထဲမှ တိုက်ရိုက် ကီးများကို သုံး၍ ချိတ်ဆက်ခြင်း
        gc = gspread.service_account_from_dict(GOOGLE_SHEET_CREDS)
        sh = gc.open_by_url(GOOGLE_SPREADSHEET_URL)
        worksheet = sh.worksheet("blacklist_records")
        
        tz = pytz.timezone('Asia/Yangon')
        now_mm = datetime.now(tz).isoformat()
        
        row_value = [
            str(data_dict.get("id") or data_dict.get("blacklist_id") or ""), 
            str(data_dict.get("full_name", "")),                            
            str(data_dict.get("nrc_number", "")),                           
            str(data_dict.get("reason", "")),                               
            str(data_dict.get("blacklisted_by", "")),                       
            str(now_mm),                                                    
            str(data_dict.get("Remark1") or data_dict.get("company_name") or data_dict.get("remark1") or ""), 
            str(data_dict.get("Remark2") or data_dict.get("address") or data_dict.get("remark2") or ""),      
            str(data_dict.get("image_url") or "")                           
        ]
        
        worksheet.append_row(row_value, value_input_option="RAW")
        print("✨ Real-time ADD Sync to Google Sheet Success!")
    except Exception as e:
        print(f"⚠️ Google Sheet Add Failed: {str(e)}")

# 🌟 ၂။ Data Update လိုက်လျှင် Google Sheet ထဲရှိ သက်ဆိုင်ရာ Row ကို လိုက်ပြင်ပေးမည့် စနစ်
def auto_sync_update_record(record_id, updated_data_dict):
    try:
        gc = gspread.service_account_from_dict(GOOGLE_SHEET_CREDS)
        sh = gc.open_by_url(GOOGLE_SPREADSHEET_URL)
        worksheet = sh.worksheet("blacklist_records")
        
        id_list = worksheet.col_values(1) 
        str_id = str(record_id)
        
        if "id" not in updated_data_dict:
            updated_data_dict["id"] = str_id

        if str_id in id_list:
            row_index = id_list.index(str_id) + 1
            
            try:
                original_created_at = worksheet.cell(row_index, 6).value or ""
            except:
                original_created_at = ""
                
            row_value = [
                str_id,                                                         
                str(updated_data_dict.get("full_name", "")),                   
                str(updated_data_dict.get("nrc_number", "")),                  
                str(updated_data_dict.get("reason", "")),                       
                str(updated_data_dict.get("blacklisted_by") or st.session_state.get("user_info", {}).get("username", "")), 
                str(original_created_at),                                       
                str(updated_data_dict.get("Remark1") or updated_data_dict.get("company_name") or updated_data_dict.get("remark1") or ""), 
                str(updated_data_dict.get("Remark2") or updated_data_dict.get("address") or updated_data_dict.get("remark2") or ""),      
                str(updated_data_dict.get("image_url") or "")                   
            ]
            
            worksheet.update(range_name=f"A{row_index}:I{row_index}", values=[row_value], value_input_option="RAW")
            print(f"✨ Real-time UPDATE Sync to Google Sheet Row {row_index} Success!")
        else:
            auto_sync_append_record(updated_data_dict)
    except Exception as e:
        print(f"⚠️ Google Sheet Update Failed: {str(e)}")

# 🌟 ၃။ Dialog Function (Global Scope တွင် ထားရှိပါသည်)
@st.dialog("📸 NRC Photo View", width="small")
def popup_image_dialog(url, name, dlg_id):
    st.html("""
        <style>
            [data-testid="stDialog"] > div > div { padding: 1rem 0rem 1rem 0rem !important; }
            [data-testid="stDialog"] .stMarkdown { padding-left: 1.5rem !important; padding-right: 1.5rem !important; }
        </style>
    """)
    st.write(f"**Name:** {name}")
    st.image(url, use_container_width=True)
    st.divider()
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("Close", key=f"close_dlg_{dlg_id}", use_container_width=True):
            st.rerun()
			
# ========================================================
# 🔐 HYBRID AUTHENTICATION SYSTEM (SUPABASE ↔️ GOOGLE SHEET)
# ========================================================

def check_user_login(username_input, password_input):
    """
    အကောင့်မှန်/မမှန်အား Supabase (သို့မဟုတ်) Google Sheet Fallback စနစ်ဖြင့် စစ်ဆေးပေးသော ဖန်ရှင်
    """
    # 1. Supabase အသက်ရှင်နေပါက Database အတွင်းမှ အကောင့်စစ်ဆေးခြင်း
    if is_supabase_alive():
        try:
            res = supabase.table("users").select("*").eq("username", username_input.strip()).execute()
            if res.data:
                user = res.data[0]
                if user.get("password") == password_input.strip():
                    return user  # အကောင့်မှန်ပါက User Dict ပြန်ပေးခြင်း
        except Exception:
            pass  # Error တက်ပါက အောက်ခြေက Google Sheet Fallback စနစ်သို့ ဆင်းမည်

    # 2. ⚠️ Supabase ဒေါင်းနေပါက Google Sheet ၏ 'users' Tab မှ ဖတ်၍ Login စစ်ဆေးခြင်း
    if ENABLE_GOOGLE_SHEET:
        try:
            spreadsheet = get_google_sheet()
            if spreadsheet:
                users_worksheet = spreadsheet.worksheet("users")
                all_users = users_worksheet.get_all_records()
                
                for row in all_users:
                    if str(row.get("username")).strip() == username_input.strip():
                        if str(row.get("password")).strip() == password_input.strip():
                            return {
                                "username": str(row.get("username")),
                                "role": str(row.get("role") or "staff"),
                                "fallback_mode": True
                            }
        except Exception as e:
            print(f"❌ Google Sheet Login Read Error: {e}")
            
    return None


def login_form():
    """
    Streamlit GUI Login Form ပြသခြင်းနှင့် Dynamic Session စီမံခန့်ခွဲမှုစနစ်
    """
    st.title("🚫 KYC Information System")
    st.subheader("Login to access the system")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit_button = st.form_submit_button("Login")

    if submit_button:
        # 🎯 ကြိုတင်ကြေညာထားသော check_user_login ဖန်ရှင်ကို လှမ်းခေါ်ခြင်း
        user_data = check_user_login(username, password)
        
        if user_data:
            import uuid
            unique_session_id = str(uuid.uuid4())
            
            # Supabase Live ဖြစ်/မဖြစ် လက်ရှိအခြေအနေအား စစ်ဆေးခြင်း
            db_live = is_supabase_alive()
            
            # 🟢 [CASE A] SUPABASE LIVE ဖြစ်နေလျှင် - Multi-Browser Prevention မောင်းနှင်ခြင်း
            if db_live:
                try:
                    user_check = supabase.table("users").select("current_session_id").eq("username", username.strip()).execute()
                    
                    if user_check.data and user_check.data[0].get("current_session_id"):
                        old_session_id = user_check.data[0].get("current_session_id")
                        log_user_activity(username=username, action="Kicked Out (Multi-Browser Prevention)", status="Success", session_id=old_session_id)

                    # Session ID သစ်အား ဒေတာဘေ့စ်တွင် Update လုပ်ခြင်း
                    supabase.table("users").update({"current_session_id": unique_session_id}).eq("username", username.strip()).execute()
                except Exception as e:
                    print(f"Supabase Multi-Browser Update Error: {e}")
            
            # 🔴 [CASE B] SUPABASE OFFLINE ဖြစ်နေလျှင်
            else:
                print(f"ℹ️ Database Offline: Skipping Multi-Browser Check for [{username}]")

            # 🎯 Streamlit State ထဲသို့ User Info တင်ပေးခြင်း
            st.session_state["logged_in"] = True
            st.session_state["user_info"] = user_data  
            st.session_state["current_session_id"] = unique_session_id
            
            # Login အောင်မြင်ကြောင်း Audit Log ရေးမှတ်ခြင်း
            log_user_activity(username, action="Login", status="Success", session_id=unique_session_id)
            
            st.success("Login successful!")
            import time; time.sleep(1)
            st.rerun() 
        else:
            # အကောင့်ဝင်မှု မအောင်မြင်ပါက Fail Log မှတ်ခြင်း
            log_user_activity(username, action="Login", status="Fail")
            st.error("Username or Password is incorrect.")

def translate_numbers(text):
    mm_nums = "၀၁၂၃၄၅၆၇၈၉"
    en_nums = "0123456789"
    to_en = text.translate(str.maketrans(mm_nums, en_nums))
    to_mm = text.translate(str.maketrans(en_nums, mm_nums))
    return to_en, to_mm

def main_app():
    if "user_info" in st.session_state and st.session_state.get("logged_in") == True:
        username = st.session_state["user_info"]["username"]
        my_session_id = st.session_state.get("current_session_id")
        db_user = supabase.table("users").select("current_session_id").eq("username", username).execute()
        
        if db_user.data:
            live_session_id = db_user.data[0].get("current_session_id")
            if live_session_id and my_session_id:
                if my_session_id != live_session_id:
                    st.session_state["logged_in"] = False
                    st.session_state["user_info"] = None
                    st.session_state["current_session_id"] = None
                    st.error("⚠️ Your account has been accessed from another browser or location, so you have been logged out.")
                    import time; time.sleep(3)
                    st.rerun()

    user_role = st.session_state['user_info'].get('role', 'user')
    st.sidebar.write(f"Welcome, {st.session_state['user_info']['username']} ({user_role.upper()})")
    
    if st.sidebar.button("Logout"):
        if "current_session_id" in st.session_state:
            from datetime import datetime
            import pytz
            tz = pytz.timezone('Asia/Yangon')
            now_mm = datetime.now(tz).isoformat()
            current_username = st.session_state['user_info']['username']
            current_session_id = st.session_state["current_session_id"]
            log_user_activity(username=current_username, action="Logout", status="Success", session_id=current_session_id)
            supabase.table("users").update({"current_session_id": None}).eq("username", current_username).execute()
        
        st.session_state.clear()
        st.success("Logged out successfully!")
        st.rerun() 

    st.header("🚫 KYC Information Management")
    
    if user_role == 'admin':
        tab1, tab2, tab3, tab4 = st.tabs([
            "➕ Add New Record", 
            "📊 View Records", 
            "📜 User Logs", 
            "👥 User Management"
        ])
    elif user_role == 'super':
        tab1, tab2 = st.tabs(["➕ Add New Record", "📊 View Records"])
        tab3 = tab4 = None
    else:
        tab2, = st.tabs(["📊 View Records"])
        tab1 = tab3 = tab4 = None

# --- Tab 1: Add New Record (Admin/Super) ---
    if tab1:
        with tab1:
            st.subheader("Add Information to Blacklist")
            with st.form("entry_form", clear_on_submit=True):
                name = st.text_input("(Full Name)")
                nrc = st.text_input("(NRC/PB)")
                company = st.text_input("(Company Name)")
                address = st.text_area("(Address)")
                reason = st.text_area("(Reason)")
                uploaded_file = st.file_uploader("📸 (NRC Photo)", type=["png", "jpg", "jpeg"])
                submitted = st.form_submit_button("Save Data")
                
            if submitted:
                if name and reason:
                    photo_url = None
                    db_live = is_supabase_alive() # Supabase အခြေအနေအား စစ်ဆေးခြင်း
                    
                    # 📸 [IMAGE UPLOAD LOGIC]
                    if uploaded_file is not None:
                        file_bytes = uploaded_file.getvalue()
                        file_ext = uploaded_file.name.split(".")[-1]
                        
                        if db_live:
                            # 🟢 Mode A: Supabase အလုပ်လုပ်နေလျှင် Supabase Storage သို့ တင်ခြင်း
                            try:
                                clean_nrc = nrc.strip().replace("/", "_").replace("(", "_").replace(")", "_").replace(" ", "")
                                if not clean_nrc: clean_nrc = "unknown"
                                import time
                                storage_file_name = f"nrc_{clean_nrc}_{int(time.time())}.{file_ext}"
                                
                                supabase.storage.from_("blacklist-images").upload(
                                    path=storage_file_name, file=file_bytes, file_options={"content-type": f"image/{file_ext}"}
                                )
                                photo_url = supabase.storage.from_("blacklist-images").get_public_url(storage_file_name)
                            except Exception as e:
                                st.error(f"⚠️ Supabase Storage Upload Failed: {str(e)}")
                        else:
                            # 🔴 Mode B: Supabase ပျက်နေလျှင် Imgur API Fallback သို့ လမ်းကြောင်းလွှဲတင်ခြင်း
                            st.info("ℹ️ Database Offline: NRC ပုံအား Imgur Hosting သို့ လှမ်းပို့နေပါသည်...")
                            photo_url = upload_to_imgur(file_bytes)
                    
                    # ဒေတာဘေ့စ် Payload တည်ဆောက်ခြင်း
                    data = {
                        "full_name": name.strip(), 
                        "nrc_number": nrc.strip(), 
                        "Remark1": company.strip(),    
                        "Remark2": address.strip(), 
                        "reason": reason.strip(),
                        "blacklisted_by": st.session_state.get('user_info', {}).get('username', 'Unknown'), 
                        "image_url": photo_url
                    }
                    
                    # 💾 [DATA SAVE LOGIC]
                    response = None
                    if db_live:
                        # 🟢 Supabase Live ဖြစ်ပါက Database ထဲသို့ အရင်သွင်းခြင်း
                        response = supabase.table("blacklist_records").insert(data).execute()
                    else:
                        # 🔴 Supabase ပျက်နေပါက စက္ကန့်အလိုက် ယာယီ ID ထုတ်ပေးခြင်း
                        import time
                        class MockResponse:
                            data = [{"id": f"GS-{int(time.time())}"}]
                        response = MockResponse()
                        st.caption("ℹ️ Saved via Google Sheet Backup Mode")
                    
                    # 🌟 Real-time Add Sync to Google Sheet
                    try:
                        if response and response.data:
                            db_id = response.data[0].get("id") or response.data[0].get("blacklist_id")
                            data["id"] = db_id
                        
                        # Google Sheet သို့ ပုံမှန်အတိုင်း ဒေတာလှမ်းပို့ခြင်း (Column I တွင် ၎င်းရလာသော ပုံလင့်ခ် ရောက်သွားပါမည်)
                        auto_sync_append_record(data)
                    except Exception as sheet_err:
                        st.warning(f"⚠️ Google Sheet Sync Warning: {str(sheet_err)}")
                    
                    # Audit Trail Logs မှတ်တမ်းသွင်းခြင်း
                    current_admin = st.session_state.get("user_info", {}).get("username", "admin")
                    log_user_activity(username=current_admin, action=f"Add New Record ({data.get('full_name')})", status="Success")
                    
                    msg_container = st.empty()
                    msg_container.success(f"🎉 {data.get('full_name')} data saved successfully!")
                    import time; time.sleep(2); msg_container.empty(); st.rerun()
                else:
                    st.warning("Must provide at least Name and Reason to save the record.")

    # --- Tab 2: View & Edit Records (All Levels) ---
    if tab2:
        with tab2:
            st.subheader("📊 Blacklist Data")
            def reset_page(): st.session_state.current_page = 1
            
            search_col1, search_col2 = st.columns(2)
            with search_col1: name_search = st.text_input("🔍 Search by Name", placeholder="Name", on_change=reset_page)
            with search_col2: search_query = st.text_input("🔍 Search by NRC/PB", placeholder="NRC/PB", on_change=reset_page)
            
            records_data_list = []
            
            # 🎯 Local flag သတ်မှတ်ခြင်းဖြင့် UnboundLocalError နှင့် SyntaxError များအား လုံးဝကျော်လွှားခြင်း
            run_google_sheet_fallback = False
            
            # 🟢 [MODE 1] SUPABASE စနစ် ဖွင့်ထားလျှင် (Primary Database Mode)
            if ENABLE_SUPABASE:
                try:
                    query = supabase.table("blacklist_records").select("*")
                    if name_search: query = query.ilike("full_name", f"%{name_search}%")
                    if search_query:
                        q_en, q_mm = translate_numbers(search_query)
                        query = query.or_(f"nrc_number.ilike.%{q_en}%,nrc_number.ilike.%{q_mm}%")
                    
                    response = query.order("id", desc=False).execute()
                    records_data_list = response.data if response and response.data else []
                except Exception as e:
                    st.error(f"❌ Database Read Error: {str(e)}")
                    st.warning("⚠️ Supabase ဒေတာဖတ်မရသဖြင့် Google Sheet Fallback Mode သို့ အလိုအလျောက် ပြောင်းလဲနေပါသည်...")
                    # Supabase ပျက်ပါက Fallback စနစ်သို့ ကူးပြောင်းရန် flag လွှဲပေးခြင်း
                    run_google_sheet_fallback = True
            else:
                # ၎င်းပြင်ပ Configuration Switch ဖြင့် ပိတ်ထားပါကလည်း Fallback အလုပ်လုပ်စေရန်
                run_google_sheet_fallback = True
            
            # 🟢 [MODE 2] SUPABASE ပိတ်ထားလျှင် သို့မဟုတ် ပျက်စီးသွားလျှင် (Google Sheet Fallback Mode)
            if run_google_sheet_fallback:
                if ENABLE_GOOGLE_SHEET:
                    try:
                        spreadsheet = get_google_sheet()
                        if spreadsheet:
                            worksheet = spreadsheet.worksheet("blacklist_records")
                            # Sheet ထဲရှိ ဒေတာအားလုံးကို ဆွဲယူခြင်း
                            sheet_rows = worksheet.get_all_records()
                            
                            # Streamlit ကုဒ်အဟောင်းများနှင့် ကိုက်ညီစေရန် Key များကို စနစ်တကျ ပြန်လည်ညှိပေးခြင်း
                            raw_list = []
                            for row in sheet_rows:
                                raw_list.append({
                                    "id": str(row.get("id")),
                                    "full_name": str(row.get("full_name", "")),
                                    "nrc_number": str(row.get("nrc_number", "")),
                                    "reason": str(row.get("reason", "")),
                                    "blacklisted_by": str(row.get("blacklisted_by", "")),
                                    "Remark1": str(row.get("Remark1", "")),
                                    "Remark2": str(row.get("Remark2", "")),
                                    "image_url": str(row.get("image_url", ""))
                                })
                            
                            # 🔍 Google Sheet ဒေတာများပေါ်တွင် ရှာဖွေခြင်း (Search Filter Custom Logic)
                            for record in raw_list:
                                match = True
                                if name_search and name_search.lower() not in record["full_name"].lower():
                                    match = False
                                if search_query:
                                    q_en, q_mm = translate_numbers(search_query)
                                    if q_en.lower() not in record["nrc_number"].lower() and q_mm.lower() not in record["nrc_number"].lower():
                                        match = False
                                if match:
                                    records_data_list.append(record)
                                    
                            st.caption("ℹ️ Running on 🟢 Google Sheet Fallback Mode (Database Offline)")
                    except Exception as sheet_err:
                        st.error(f"❌ Google Sheet Read Error: {str(sheet_err)}")
                else:
                    st.info("⏸️ Connections နှစ်ခုစလုံးကို ပိတ်ထားသဖြင့် ဒေတာများအား မပြသနိုင်သေးပါ။")

            # ----------------------------------------------------
            # 📊 VIEW & PAGINATION LOGIC (ပြသခြင်း အပိုင်း)
            # ----------------------------------------------------
            if records_data_list and len(records_data_list) > 0:
                total_items = len(records_data_list)
                items_per_page = 10
                total_pages = max(1, (total_items + items_per_page - 1) // items_per_page)
                
                if 'current_page' not in st.session_state: st.session_state.current_page = 1
                if st.session_state.current_page > total_pages: st.session_state.current_page = 1

                page_col1, page_col2, page_col3 = st.columns([1, 2, 1])
                with page_col1:
                    if st.button("⬅️ Previous") and st.session_state.current_page > 1:
                        st.session_state.current_page -= 1; st.rerun()
                with page_col2: st.write(f"Page **{st.session_state.current_page}** of **{total_pages}**")
                with page_col3:
                    if st.button("Next ➡️") and st.session_state.current_page < total_pages:
                        st.session_state.current_page += 1; st.rerun()
                
                start_idx = (st.session_state.current_page - 1) * items_per_page
                end_idx = start_idx + items_per_page
                page_data = records_data_list[start_idx:end_idx]
                st.divider()
                
                for i, record in enumerate(page_data, start=start_idx + 1):
                    raw_nrc = str(record['nrc_number']).strip() if record['nrc_number'] else ""
                    prefix = "NRC" if raw_nrc and raw_nrc[0].isdigit() else "PB"
                    
                    with st.expander(f"{i} 👤 {record['full_name']} ({prefix}: {raw_nrc})"):
                        edit_key = f"edit_mode_{record['id']}"
                        if edit_key not in st.session_state: st.session_state[edit_key] = False
                        
                        if not st.session_state[edit_key]:
                            st.write(f"**Reason:** {record['reason']}")
                            st.write(f"**Listed by:** {record['blacklisted_by']}")
                            st.write(f"**Company:** {record['Remark1']}")
                            st.write(f"**Address:** {record['Remark2']}")
                            
                            # 📸 Image View Logic (လင့်ခ်ရှိလျှင် ပြသရန်)
                            if record.get("image_url") and record["image_url"] != "NULL" and record["image_url"].strip() != "":
                                if st.button("📸 View Image", key=f"btn_img_{record['id']}", width='stretch', type="secondary"):
                                    popup_image_dialog(record["image_url"], record.get("full_name", "Unknown"), record['id'])
                            else:
                                st.button("❌ No Image Available", key=f"btn_no_img_{record['id']}", width='stretch', disabled=True)

                            st.write("")

                            if user_role == 'admin':
                                col1, col2 = st.columns(2)
                                with col1:
                                    if st.button("📝 Edit", key=f"btn_edit_{record['id']}", width='stretch'):
                                        st.session_state[edit_key] = True; st.rerun()
                                with col2:
                                    if st.button("🗑️ Delete", key=f"btn_del_{record['id']}", width='stretch'):
                                        deleted_name = record.get('full_name', f"ID: {record['id']}")
                                        
                                        # 🗑️ Delete (Supabase Context)
                                        if ENABLE_SUPABASE:
                                            supabase.table("blacklist_records").delete().eq("id", record["id"]).execute()
                                        
                                        # 🗑️ Delete (Google Sheet Context)
                                        if ENABLE_GOOGLE_SHEET:
                                            try:
                                                spreadsheet = get_google_sheet()
                                                if spreadsheet:
                                                    worksheet = spreadsheet.worksheet("blacklist_records")
                                                    id_list = worksheet.col_values(1)
                                                    if str(record["id"]) in id_list:
                                                        r_idx = id_list.index(str(record["id"])) + 1
                                                        worksheet.delete_rows(r_idx)
                                            except Exception as sheet_del_err:
                                                print(f"Sheet Delete Warning: {sheet_del_err}")
                                                
                                        log_user_activity(username=st.session_state["user_info"]["username"], action=f"Delete Record ({deleted_name})", status="Success")
                                        st.success("Data Deleted Successfully!"); import time; time.sleep(1); st.rerun()
                            else:
                                st.caption("🔒 View Only Mode (Admin access required to Edit/Delete)")
                        else:
                            # 📝 [ EDIT FORM MODE ]
                            with st.form(key=f"form_edit_{record['id']}"):
                                new_name = st.text_input("Name", value=record['full_name'])
                                new_nrc = st.text_input("NRC", value=record['nrc_number'])
                                new_company = st.text_input("Company", value=record['Remark1'])
                                new_address = st.text_input("Address", value=record['Remark2'])
                                new_reason = st.text_area("Reason", value=record['reason'])
                                edit_uploaded_file = st.file_uploader("📸 Change NRC Photo", type=["png", "jpg", "jpeg"], key=f"file_edit_{record['id']}")
                                
                                f_col1, f_col2 = st.columns(2)
                                with f_col1: update_submitted = st.form_submit_button("✅ Update", width='stretch')
                                with f_col2: cancel_submitted = st.form_submit_button("❌ Cancel", width='stretch')
                                    
                            if update_submitted:
                                changes_list = []
                                if record.get('full_name', '').strip() != new_name.strip():
                                    changes_list.append(f"Name: '{record.get('full_name')}' ➡️ '{new_name.strip()}'")
                                if record.get('nrc_number', '').strip() != new_nrc.strip():
                                    changes_list.append(f"NRC: '{record.get('nrc_number')}' ➡️ '{new_nrc.strip()}'")
                                if record.get('Remark1', '').strip() != new_company.strip():
                                    changes_list.append(f"Company: '{record.get('Remark1')}' ➡️ '{new_company.strip()}'")
                                if record.get('Remark2', '').strip() != new_address.strip():
                                    changes_list.append(f"Address: '{record.get('Remark2')}' ➡️ '{new_address.strip()}'")
                                if record.get('reason', '').strip() != new_reason.strip():
                                    changes_list.append(f"Reason: '{record.get('reason')}' ➡️ '{new_reason.strip()}'")

                                final_photo_url = record.get("image_url")
                                if edit_uploaded_file is not None and ENABLE_SUPABASE:
                                    try:
                                        file_ext = edit_uploaded_file.name.split(".")[-1]
                                        clean_nrc = new_nrc.strip().replace("/", "_").replace("(", "_").replace(")", "_").replace(" ", "")
                                        import time
                                        storage_file_name = f"nrc_{clean_nrc}_{int(time.time())}.{file_ext}"
                                        supabase.storage.from_("blacklist-images").upload(path=storage_file_name, file=edit_uploaded_file.getvalue(), file_options={"content-type": f"image/{file_ext}"})
                                        final_photo_url = supabase.storage.from_("blacklist-images").get_public_url(storage_file_name)
                                        changes_list.append("📸 NRC Photo Updated")
                                    except Exception as e: st.error(f"⚠️ Error: {str(e)}")
                                
                                update_data = {
                                    "full_name": new_name.strip(), "nrc_number": new_nrc.strip(), "reason": new_reason.strip(),
                                    "Remark1": new_company.strip(), "Remark2": new_address.strip(), "image_url": final_photo_url
                                }
                                
                                current_id = record.get('id')
                                
                                # 🟢 Database Update (Supabase)
                                if ENABLE_SUPABASE:
                                    supabase.table("blacklist_records").update(update_data).eq("id", current_id).execute()
                                
                                # 🌟 Real-time Update Sync to Google Sheet
                                if ENABLE_GOOGLE_SHEET:
                                    try:
                                        auto_sync_update_record(current_id, update_data)
                                    except Exception as sheet_err:
                                        st.warning(f"⚠️ Google Sheet Update Sync Warning: {str(sheet_err)}")
                                
                                full_audit_action = f"Update Record ({new_name.strip()}) | ⚙️ Changes: {', '.join(changes_list)}" if changes_list else f"Update Record ({new_name.strip()}) | No data changed"
                                log_user_activity(username=st.session_state["user_info"]["username"], action=full_audit_action, status="Success")
                                st.session_state[edit_key] = False
                                st.success("Update Successfully!"); import time; time.sleep(1); st.rerun()
                                
                            if cancel_submitted: st.session_state[edit_key] = False; st.rerun()
            else:
                st.info("🔍 ရှာဖွေထားသော အချက်အလက် မရှိပါ။")

# --- Tab 3: User Access Logs (Admin Only) ---
    if tab3:
        with tab3:
            st.subheader("📜 User Access Logs (Audit Trail)")
            def to_local_time(iso_str):
                if not iso_str: return "N/A"
                try:
                    from datetime import datetime; import pytz
                    utc_dt = datetime.fromisoformat(iso_str.replace('Z', '+00:00'))
                    mm_tz = pytz.timezone('Asia/Yangon')
                    return utc_dt.astimezone(mm_tz).strftime('%Y-%m-%d %I:%M:%S %p')
                except Exception: return iso_str

            @st.fragment(run_every=10)
            def show_auto_refresh_logs():
                from datetime import datetime
                with st.form("logs_filter_form"):
                    st.write("🔍 **Filter User Logs**")
                    col1, col2 = st.columns(2)
                    with col1: search_username = st.text_input("Search by Username", placeholder="e.g., admin, 001")
                    with col2: filter_date = st.date_input("Select Date", value=None)
                    filter_submitted = st.form_submit_button("Refresh & Filter Logs")

                try:
                    log_query = supabase.table("user_logs").select("id", "username", "action", "status", "action_date_time", "session_id")
                    if search_username.strip(): log_query = log_query.ilike("username", f"%{search_username.strip()}%")
                    logs_response = log_query.order("id", desc=True).execute()

                    if logs_response.data:
                        formatted_logs = []
                        for log in logs_response.data:
                            raw_time = log.get('action_date_time')
                            action_time_local = to_local_time(raw_time)

                            if filter_date and raw_time:
                                try:
                                    log_date_str = datetime.fromisoformat(raw_time.replace('Z', '+00:00')).strftime('%Y-%m-%d')
                                    if log_date_str != str(filter_date): continue
                                except Exception: pass

                            formatted_logs.append({
                                "Log ID": log.get('id'), "Username": log.get('username'), "Action": log.get('action', 'N/A'),
                                "Status": log.get('status', 'N/A'), "Date & Time (MM)": action_time_local, "Session ID": log.get('session_id')
                            })
                        if formatted_logs:
                            st.dataframe(pd.DataFrame(formatted_logs), use_container_width=True, hide_index=True)
                            st.caption(f"🔄 Total Logs: {len(formatted_logs)} (Auto-Refresh every 10 seconds)")
                        else: st.info("No logs found for the given filter criteria.")
                    else: st.info("No Logs data found in database.")
                except Exception as e: st.error(f"❌ Error loading logs: {e}")
            show_auto_refresh_logs()

    # --- Tab 4: User Management Accounts (Admin Only) ---
    if tab4:
        with tab4:
            st.subheader("⚙️ User Account Management Setup")
            if "edit_user_mode" not in st.session_state:
                st.session_state["edit_user_mode"] = False
                st.session_state["edit_user_data"] = None

            @st.fragment(run_every=5)
            def manage_users_crud():
                st.cache_data.clear()
                users_res = supabase.table("users").select("*").order("username").execute()
                users_list = users_res.data if users_res.data else []
                
                if users_list:
                    view_data = []
                    for u in users_list:
                        session_val = u.get("current_session_id") or "None"
                        view_data.append({
                            "(Name)": u.get("name", "-"), "(Username)": u.get("username"),
                            "(Role)": str(u.get("role")).upper(), "(Current Session)": session_val
                        })
                    st.write("📊 user list")
                    st.dataframe(pd.DataFrame(view_data), use_container_width=True)
                else: st.info("no users found in the system.")
                
                st.divider()

                # 📝 ဝန်ထမ်းအကောင့်ပြင်ဆင်ခြင်း Form အပြည့်အစုံ
                if st.session_state["edit_user_mode"]:
                    st.write("📝 update selected account")
                    current_u = st.session_state["edit_user_data"]
                    
                    with st.form("edit_user_form"):
                        input_name = st.text_input("Name", value=current_u.get("name", ""))
                        st.text_input("Username (No Edit)", value=current_u.get("username"), disabled=True)
                        input_password = st.text_input("New Password", type="password", placeholder="New Password")
                        input_role = st.selectbox("Role", ["user", "super", "admin"], index=0 if current_u.get("role") == "user" else (1 if current_u.get("role") == "super" else 2))
                        
                        col_f1, col_f2 = st.columns(2)
                        with col_f1: save_edit = st.form_submit_button("💾 Save Updates")
                        with col_f2: cancel_edit = st.form_submit_button("❌ Cancel")

                        if save_edit:
                            update_payload = {"name": input_name, "role": input_role}
                            if input_password.strip(): update_payload["password"] = input_password

                            supabase.table("users").update(update_payload).eq("username", current_u.get("username")).execute()

                            user_changes = []
                            target_username = current_u.get('username', 'Unknown')
                            if current_u.get('name', '').strip() != input_name.strip():
                                user_changes.append(f"Name: '{current_u.get('name')}' ➡️ '{input_name.strip()}'")
                            if current_u.get('role', '').strip() != input_role.strip():
                                user_changes.append(f"Role: '{current_u.get('role')}' ➡️ '{input_role.strip()}'")
                            if input_password.strip(): user_changes.append("🔑 Password: 'Changed to New Password'")

                            account_audit_action = f"Update User ({target_username}) | ⚙️ Changes: {', '.join(user_changes)}" if user_changes else f"Update User ({target_username}) | No account data changed"
                            log_user_activity(username=st.session_state["user_info"]["username"], action=account_audit_action, status="Success")

                            st.success(f"✨ Username: {target_username} updated successfully!")
                            st.session_state["edit_user_mode"] = False
                            st.session_state["edit_user_data"] = None
                            st.rerun()

                        if cancel_edit:
                            st.session_state["edit_user_mode"] = False
                            st.session_state["edit_user_data"] = None
                            st.rerun()
                else:
                    # ➕ ဝန်ထမ်းအကောင့်အသစ်ဆောက်ခြင်း Form
                    st.write("Add New User")
                    with st.form("add_user_form", clear_on_submit=True):
                        new_name = st.text_input("Name")
                        new_username = st.text_input("Username")
                        new_password = st.text_input("Password", type="password")
                        new_role = st.selectbox("Define Role", ["user", "super", "admin"])
                        submit_add = st.form_submit_button("➕ Add New")

                        if submit_add:
                            if not new_username.strip() or not new_password.strip() or not new_name.strip():
                                st.error("⚠️ input complete information to create new account")
                            else:
                                check_exist = supabase.table("users").select("username").eq("username", new_username.strip()).execute()
                                if check_exist.data:
                                    log_user_activity(st.session_state["user_info"]["username"], action="Create User", status="Fail")
                                    st.error("⚠️ Username already exists.")
                                else:
                                    insert_payload = {"name": new_name.strip(), "username": new_username.strip(), "password": new_password.strip(), "role": new_role, "current_session_id": None}
                                    supabase.table("users").insert(insert_payload).execute()
                                    log_user_activity(st.session_state["user_info"]["username"], action=f"Create User ({new_username.strip()})", status="Success")
                                    st.success(f"🎉 New user added successfully: {new_name}"); st.rerun()

                st.divider()
                if users_list and not st.session_state["edit_user_mode"]:
                    st.write("🛠️ Select account for update or delete")
                    user_options = [f"{u.get('name')} ({u.get('username')})" for u in users_list]
                    selected_user_str = st.selectbox("Select an account", user_options)
                    selected_index = user_options.index(selected_user_str)
                    target_user_data = users_list[selected_index]

                    col_act1, col_act2 = st.columns(2)
                    with col_act1:
                        if st.button("📝 update selected account", use_container_width=True):
                            st.session_state["edit_user_mode"] = True
                            st.session_state["edit_user_data"] = target_user_data
                            st.rerun()
                    with col_act2:
                        if target_user_data.get("username") == "admin": st.warning("🔒 cannot delete 'admin' account")
                        else:
                            if st.button("🗑️ delete selected account", use_container_width=True, type="secondary"):
                                supabase.table("users").delete().eq("username", target_user_data.get("username")).execute()
                                log_user_activity(st.session_state["user_info"]["username"], action=f"Delete User ({target_user_data.get('username')})", status="Success")
                                st.success(f"🗑️ Username: {target_user_data.get('username')} deleted."); st.rerun()
            manage_users_crud()

def log_user_activity(username, action, status, session_id=None):
    import pytz
    from datetime import datetime
    import streamlit as st
    import time
    
    # 🎯 Streamlit Framework အောက်တွင် အမှားကင်းစေရန် အခြေအနေစစ်ဆေးမှုကို တိုက်ရိုက်ယူခြင်း
    # global variable ရှာမတွေ့ပါက ပုံမှန်အားဖြင့် True ဟု ယူဆခိုင်းထားပါသည်
    try:
        current_enable_supabase = globals().get('ENABLE_SUPABASE', True)
    except:
        current_enable_supabase = True

    try:
        current_enable_sheet = globals().get('ENABLE_GOOGLE_SHEET', True)
    except:
        current_enable_sheet = True
    
    tz = pytz.timezone('Asia/Yangon')
    now_mm = datetime.now(tz).isoformat()
    
    if not session_id:
        if "current_session_id" in st.session_state and st.session_state["current_session_id"]:
            session_id = st.session_state["current_session_id"]
        else:
            session_id = "ST-LIVE-SESSION"
            
    if not username:
        if "user_info" in st.session_state and st.session_state["user_info"]:
            username = st.session_state["user_info"].get("username", "system_user")
        else:
            username = "system_user"

    # A. Supabase Database ထဲသို့ Logs ရေးခြင်း
    if current_enable_supabase:
        try:
            global_supabase = globals().get('supabase')
            if global_supabase:
                global_supabase.table("user_logs").insert({
                    "username": str(username), 
                    "session_id": str(session_id), 
                    "action": str(action), 
                    "status": str(status), 
                    "action_date_time": now_mm
                }).execute()
        except Exception as e: 
            print(f"Supabase Log Error: {e}")

    # B. 🎯 Google Sheet သို့ ဒေတာသွင်းခြင်း (မဖြစ်မနေ မောင်းနှင်မည့် စနစ်)
    if current_enable_sheet:
        for attempt in range(3):
            try:
                global_sheet_fn = globals().get('get_google_sheet')
                if global_sheet_fn:
                    spreadsheet = global_sheet_fn()
                    if spreadsheet:
                        log_worksheet = spreadsheet.worksheet("user_logs")
                        
                        unique_id = str(int(time.time()))
                        log_row_value = [
                            unique_id, 
                            str(username), 
                            str(now_mm), 
                            str(session_id), 
                            str(action), 
                            str(status)
                        ]
                        
                        log_worksheet.append_row(log_row_value, value_input_option='USER_ENTERED')
                        print(f"🚀 [CLOUD SUCCESS] Sync to Google Sheet Success on attempt {attempt + 1}!")
                        break
                    else:
                        print("⚠️ Spreadsheet configuration returned None")
            except Exception as sheet_log_err:
                print(f"⚠️ Sheet Append Attempt {attempt + 1} Failed: {str(sheet_log_err)}")
                time.sleep(1)

def auto_cleanup_expired_logs():
    if "cleanup_done" not in st.session_state:
        try:
            from datetime import datetime, timedelta; import pytz
            tz = pytz.timezone('Asia/Yangon')
            time_limit_iso = (datetime.now(tz) - timedelta(hours=3)).isoformat()
            
            if ENABLE_SUPABASE:
                active_users = supabase.table("users").select("username", "current_session_id").not_.is_("current_session_id", "null").execute()
                if active_users.data:
                    for user in active_users.data:
                        # 🎯 descending=True မှ desc=True သို့ ပြင်ဆင်ထားပါသည်
                        last_log = supabase.table("user_logs").select("action_date_time").eq("session_id", user["current_session_id"]).order("id", desc=True).limit(1).execute()
                        if last_log.data and last_log.data[0]["action_date_time"] < time_limit_iso:
                            log_user_activity(username=user["username"], action="Session Expired", status="Success", session_id=user["current_session_id"])
                            supabase.table("users").update({"current_session_id": None}).eq("username", user["username"]).execute()
            st.session_state["cleanup_done"] = True
        except Exception as e: print(f"Cleanup Error: {e}")

# ====================================================
# 🚀 APP ENTRY POINT & RUNTIME LIFE CYCLE
# ====================================================
if "logged_in" not in st.session_state: st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    login_form()
else:
    auto_cleanup_expired_logs()
    main_app()