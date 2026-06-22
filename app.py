import streamlit as st
from supabase import create_client, Client
import time

# --- Supabase Configuration ---
SUPABASE_URL = "https://batsowuihgwhxbboucpy.supabase.co"
SUPABASE_KEY = "sb_publishable_OBTOI4EioNVufb5akpDOwA_75EmAcWr"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def check_login(username, password):
    # 'users' table ထဲမှာ username နဲ့ password ကို စစ်ဆေးခြင်း
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
                import uuid

                # 🌟 ထူးခြားတဲ့ Session ID တစ်ခု ထုတ်ခြင်း
                new_session_id = str(uuid.uuid4())
                from datetime import datetime
                import pytz
                tz = pytz.timezone('Asia/Yangon')
                now_mm = datetime.now(tz).isoformat()

                # ယခင်ပိတ်မိနေသော user_logs ဒေတာများကို ကန်ထုတ်ခံရသည့်အမှတ်အသားဖြင့် အလိုအလျောက် ပိတ်ပစ်ခြင်း
                supabase.table("user_logs").update({
                    "logout_time": now_mm,
                    "session_id": f"Kicked Out (Multi-Browser) - {now_mm}"
                }).eq("username", username).is_("logout_time", "null").execute()

                # Supabase `users` table ထဲမှာ လက်ရှိ Session ID ကို လှမ်းပြီး Lock ခတ်လိုက်ခြင်း
                supabase.table("users").update({"current_session_id": new_session_id}).eq("username", username).execute()
                
                # Streamlit Session State ထဲတွင်ပါ သိမ်းဆည်းခြင်း
                st.session_state["logged_in"] = True
                st.session_state["user_info"] = user_data[0]
                st.session_state["user_info"]["current_session_id"] = new_session_id # ID အသစ်အား ထည့်သွင်းခြင်း
                
                # (လူကြီးမင်း၏ မူရင်း user_logs ထည့်သည့် ကုဒ်များကို ဤနေရာတွင် ဆက်ထားပါ...)
                current_session = str(uuid.uuid4())
                st.session_state["current_session_id"] = current_session
                log_data = {"username": username, "session_id": current_session}
                supabase.table("user_logs").insert(log_data).execute()
                
                st.success("Login အောင်မြင်ပါတယ်!")
                st.rerun() 
            else:
                st.error("Username သို့မဟုတ် Password မှားယွင်းနေပါသည်။")

def translate_numbers(text):
    mm_nums = "၀၁၂၃၄၅၆၇၈၉"
    en_nums = "0123456789"
    to_en = text.translate(str.maketrans(mm_nums, en_nums))
    to_mm = text.translate(str.maketrans(en_nums, mm_nums))
    return to_en, to_mm

def main_app():
    
    if "user_info" in st.session_state:
        username = st.session_state["user_info"]["username"]
        my_session_id = st.session_state["user_info"].get("current_session_id")
        
        # Database ထဲက လက်ရှိ Live ဖြစ်နေတဲ့ Session ID ကို လှမ်းစစ်ခြင်း
        db_user = supabase.table("users").select("current_session_id").eq("username", username).execute()
        
        if db_user.data:
            live_session_id = db_user.data[0].get("current_session_id")
            
            # အကယ်၍ အခြား Browser တစ်ခုခုကနေ ဝင်လိုက်လို့ ID ချိန်းသွားခဲ့ရင် အလိုအလျောက် ကန်ထုတ်မည်
            if live_session_id and my_session_id != live_session_id:
                st.session_state["logged_in"] = False
                st.session_state["user_info"] = None
                st.error("⚠️ သင့်အကောင့်အား အခြား Browser သို့မဟုတ် အခြားနေရာတစ်ခုမှ ဝင်ရောက်သွားပါသဖြင့် စနစ်မှ အလိုအလျောက် ထွက်ရှိပါသည်ု")
                import time
                time.sleep(3)
                st.rerun()

    # ရရှိလာသော user_info ထဲမှ user_role ကို ရယူခြင်း (မပါရှိပါက default အနေဖြင့် 'user' ဟု ယူပါမည်)
    user_role = st.session_state['user_info'].get('role', 'user')
    
    st.sidebar.write(f"Welcome, {st.session_state['user_info']['username']} ({user_role.upper()})")
    if st.sidebar.button("Logout"):
        # 🌟 LOGOUT TIME အား UPDATE လုပ်ခြင်း
        if "current_session_id" in st.session_state:
            from datetime import datetime
            import pytz
            
            # မြန်မာစံတော်ချိန်ဖြင့် ထွက်သည့် အချိန်ကို ရယူခြင်း
            tz = pytz.timezone('Asia/Yangon')
            now_mm = datetime.now(tz).isoformat()
            
            # Supabase ထဲက သက်ဆိုင်ရာ session_id မှာ logout_time ကို လှမ်းထည့်ခြင်း
            supabase.table("user_logs").update({"logout_time": now_mm}).eq("session_id", st.session_state["current_session_id"]).execute()
        
        # Session ရှင်းထုတ်ပြီး ထွက်ခိုင်းခြင်း
        st.session_state["logged_in"] = False
        st.session_state["current_session_id"] = None
        st.rerun()

    st.header("🚫 Black List Information Management")
    
    # --- Role ပေါ်မူတည်၍ Tabs Rights ခွဲခြားခြင်း ---
    if user_role == 'admin':
        # Admin ဖြစ်ပါက ဒေတာသွင်းခြင်း နှင့် ဒေတာကြည့်ခြင်း Tab ၂ ခုစလုံး ပြပါမည်
        tab1, tab2, tab3 = st.tabs(["➕ Add New Record", "📊 View Records", "📜 User Logs"])
    else:
        # User ဖြစ်ပါက View Records တစ်ခုတည်းကိုသာ Single Tab အနေဖြင့် ပြပါမည်
        tab2, = st.tabs(["📊 View Records"])
        tab1 = None
        tab3 = None # User အတွက် logs tab ကို ပိတ်ထားပါမယ်

    # --- Tab 1: Add New Record (Admin Only) ---
    if tab1:
        with tab1:
            st.subheader("Add Information to Blacklist")
            with st.form("entry_form", clear_on_submit=True):
                name = st.text_input("အမည် (Full Name)")
                nrc = st.text_input("မှတ်ပုံတင်အမှတ် (NRC)")
                company = st.text_input("ကုမ္ပဏီအမည် (Company Name)")
                address = st.text_area("နေရပ်လိပ်စာ (Address)")
                reason = st.text_area("အကြောင်းရင်း (Reason)")
                
                submitted = st.form_submit_button("Save Data")
                
                if submitted:
                    if name and reason:
                        data = {
                            "full_name": name,
                            "nrc_number": nrc,
                            "Remark1": company,    
                            "Remark2": address,    
                            "reason": reason,
                            "blacklisted_by": st.session_state['user_info']['username']
                        }
                        response = supabase.table("blacklist_records").insert(data).execute()
                        
                        msg_container = st.empty()
                        msg_container.success(f"{name} ၏ အချက်အလက်ကို သိမ်းဆည်းပြီးပါပြီ။")
                        time.sleep(3)
                        msg_container.empty()
                    else:
                        st.warning("အမည်နှင့် အကြောင်းရင်းကို မဖြစ်မနေ ထည့်ပေးပါ။")

    # --- Tab 2: View Records (Both Admin and User) ---
    with tab2:
        st.subheader("📊 Blacklist Data")
        
        def reset_page():
            st.session_state.current_page = 1

        # Search UI
        search_col1, search_col2 = st.columns(2)
        with search_col1:
            name_search = st.text_input("🔍 Search by Name", placeholder="အမည်ရိုက်ထည့်ပါ", on_change=reset_page)
        with search_col2:
            search_query = st.text_input("🔍 Search by NRC/PB", placeholder="နံပါတ်ဖြင့်ရှာရန်", on_change=reset_page)
        
        # Database Query
        query = supabase.table("blacklist_records").select("*")
        if name_search:
            query = query.ilike("full_name", f"%{name_search}%")
        if search_query:
            q_en, q_mm = translate_numbers(search_query)
            query = query.or_(f"nrc_number.ilike.%{q_en}%,nrc_number.ilike.%{q_mm}%")
        
        records = query.order("id", desc=False).execute()

        # Pagination Logic
        if records.data:
            total_items = len(records.data)
            items_per_page = 10
            total_pages = max(1, (total_items + items_per_page - 1) // items_per_page)
            
            if 'current_page' not in st.session_state:
                st.session_state.current_page = 1

            if st.session_state.current_page > total_pages:
                st.session_state.current_page = 1

            page_col1, page_col2, page_col3 = st.columns([1, 2, 1])
            with page_col1:
                if st.button("⬅️ Previous") and st.session_state.current_page > 1:
                    st.session_state.current_page -= 1
                    st.rerun()

            with page_col2:
                st.write(f"Page **{st.session_state.current_page}** of **{total_pages}**")

            with page_col3:
                if st.button("Next ➡️") and st.session_state.current_page < total_pages:
                    st.session_state.current_page += 1
                    st.rerun()
            
            start_idx = (st.session_state.current_page - 1) * items_per_page
            end_idx = start_idx + items_per_page
            page_data = records.data[start_idx:end_idx]

            st.divider()
            
            for i, record in enumerate(page_data, start=start_idx + 1):
                raw_nrc = str(record['nrc_number']).strip() if record['nrc_number'] else ""
                prefix = "NRC" if raw_nrc and raw_nrc[0].isdigit() else "PB"
                
                with st.expander(f"{i} 👤 {record['full_name']} ({prefix}: {raw_nrc})"):
                    edit_key = f"edit_mode_{record['id']}"
                    if edit_key not in st.session_state:
                        st.session_state[edit_key] = False
                    
                    # Edit Mode မဟုတ်လျှင် (ပုံမှန်ပြသရန်)
                    if not st.session_state[edit_key]:
                        st.write(f"**Reason:** {record['reason']}")
                        st.write(f"**Listed by:** {record['blacklisted_by']}")
                        st.write(f"**Company:** {record['Remark1']}")
                        st.write(f"**Address:** {record['Remark2']}")
                        
                        # --- Right Control: Admin ဖြစ်မှသာ Edit/Delete ခလုတ်များကို ပြသမည် ---
                        if user_role == 'admin':
                            col1, col2 = st.columns(2)
                            with col1:
                                if st.button("📝 Edit", key=f"btn_edit_{record['id']}"):
                                    st.session_state[edit_key] = True
                                    st.rerun()
                            with col2:
                                if st.button("🗑️ Delete", key=f"btn_del_{record['id']}"):
                                    supabase.table("blacklist_records").delete().eq("id", record["id"]).execute()
                                    st.success("Data ဖျက်ပြီးပါပြီ။")
                                    time.sleep(1)
                                    st.rerun()
                        else:
                            # User များအတွက် View Only အနေဖြင့်သာ ရှိနေကြောင်း အချက်ပြစာသားလေး ပြသနိုင်သည်
                            st.caption("🔒 View Only Mode (Admin access required to Edit/Delete)")
                    
                    # Edit Mode ဖြစ်နေလျှင် (Form ပြရန် - Admin သီးသန့်)
                    else:
                        with st.form(key=f"form_edit_{record['id']}"):
                            new_name = st.text_input("Name", value=record['full_name'])
                            new_nrc = st.text_input("NRC", value=record['nrc_number'])
                            new_company = st.text_input("Company", value=record['Remark1'])
                            new_address = st.text_input("Address", value=record['Remark2'])
                            new_reason = st.text_area("Reason", value=record['reason'])
                            
                            f_col1, f_col2 = st.columns(2)
                            with f_col1:
                                if st.form_submit_button("✅ Update"):
                                    update_data = {
                                        "full_name": new_name, 
                                        "nrc_number": new_nrc, 
                                        "reason": new_reason, 
                                        "Remark1": new_company, 
                                        "Remark2": new_address 
                                    }
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
    # 🌟 Tab 3: User Logs Management (Admin Only)
    # ----------------------------------------------------
    if tab3:
        with tab3:
            st.subheader("📜 User Access Logs (Audit Trail)")
            @st.fragment(run_every=10)
            def show_auto_refresh_logs():
            # --- Logs ရှာဖွေရန် Form UI ---
            with st.form("logs_filter_form"):
                st.write("🔍 **Filter User Logs**")
                col1, col2 = st.columns(2)
                with col1:
                    search_username = st.text_input("Username ဖြင့် ရှာရန်", placeholder="ဥပမာ - admin, 001")
                with col2:
                    # ရက်စွဲအလိုက် စစ်ထုတ်ချင်လျှင် သုံးရန်
                    filter_date = st.date_input("ရက်စွဲရွေးချယ်ရန်", value=None)
                
                filter_submitted = st.form_submit_button("Logs ရှာဖွေမည်")

            # --- Supabase Query for Logs ---
            log_query = supabase.table("user_logs").select("*")
            
            if search_username:
                log_query = log_query.ilike("username", f"%{search_username}%")
            
            # Query အား id အလိုက် အသစ်ဆုံးကို အပေါ်ကပြရန် (desc=True)
            logs_response = log_query.order("id", desc=True).execute()

            if logs_response.data:
                import pandas as pd
                from datetime import datetime
                import pytz

                # ဒေတာများကို သပ်သပ်ရပ်ရပ် ပြသနိုင်ရန် List အသစ်တစ်ခု တည်ဆောက်ခြင်း
                formatted_logs = []
                
                for log in logs_response.data:
                    # UTC Time မှ မြန်မာစံတော်ချိန်သို့ ပြောင်းလဲပြသရန် Function
                    def to_local_time(iso_str):
                        if not iso_str:
                            return "Active Now (မထွက်သေးပါ)"
                        # UTC time အား ဖတ်ပြီး မြန်မာစံတော်ချိန် ပြောင်းခြင်း
                        utc_dt = datetime.fromisoformat(iso_str.replace('Z', '+00:00'))
                        mm_tz = pytz.timezone('Asia/Yangon')
                        return utc_dt.astimezone(mm_tz).strftime('%Y-%m-%d %I:%M:%S %p')

                    login_local = to_local_time(log['login_time'])
                    logout_local = to_local_time(log['logout_time'])

                    # ရက်စွဲ Filter ပါဝင်ပါက စစ်ထုတ်ခြင်း
                    if filter_date:
                        log_date_str = datetime.fromisoformat(log['login_time'].replace('Z', '+00:00')).strftime('%Y-%m-%d')
                        if log_date_str != str(filter_date):
                            continue # ရက်စွဲမတူပါက ကျော်သွားမည်

                    formatted_logs.append({
                        "Log ID": log['id'],
                        "အသုံးပြုသူ (Username)": log['username'],
                        "စနစ်ထဲဝင်ချိန် (Login Time)": login_local,
                        "စနစ်မှထွက်ချိန် (Logout Time)": logout_local,
                        "Session ID": log['session_id']
                    })

                if formatted_logs:
                    # Pandas Dataframe ပြောင်းပြီး သပ်ရပ်လှပသော ဇယားဖြင့် ပြသခြင်း
                    df_logs = pd.DataFrame(formatted_logs)
                    
                    # ဇယားကို စာမျက်နှာအပြည့် လှလှပပ ထုတ်ပြခြင်း
                    st.dataframe(
                        df_logs, 
                        use_container_width=True,
                        hide_index=True
                    )
                    
                    st.caption(f"📊 စုစုပေါင်းမှတ်တမ်း {len(df_logs)} ခု တွေ့ရှိရပါသည်။")
                else:
                    st.info("ရွေးချယ်ထားသော ရက်စွဲတွင် မှတ်တမ်းမရှိပါ။")
            else:
                st.write("Logs မှတ်တမ်းများ မရှိသေးပါ။")
        show_auto_refresh_logs()

# --- App Entry Point ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

# ====================================================
# 🌟 LOGOUT မလုပ်ဘဲ Close (X) လုပ်သွားသူများကို လိုက်ပြင်ပေးမည့် စနစ်
# ====================================================
def auto_cleanup_expired_logs():
    # Session State ကို သုံးပြီး တစ်နေ့တာအတွင်း (သို့မဟုတ်) တစ်ခေါက်ပဲ Run စေရန် Lock ခတ်ခြင်း
    if "cleanup_done" not in st.session_state:
        try:
            from datetime import datetime, timedelta
            import pytz
            
            tz = pytz.timezone('Asia/Yangon')
            time_limit = datetime.now(tz) - timedelta(hours=3)
            time_limit_iso = time_limit.isoformat()
            
            # Logout မရှိဘဲ ပိတ်မိနေသည့် session များကို ရှာခြင်း
            expired_sessions = supabase.table("user_logs") \
                .select("id") \
                .is_("logout_time", "null") \
                .lt("login_time", time_limit_iso) \
                .execute()
                
            # တွေ့ရှိပါက "Tab Closed (X)" အဖြစ် ပြောင်းလဲခြင်း
            if expired_sessions.data:
                now_mm = datetime.now(tz).isoformat()
                for session in expired_sessions.data:
                    supabase.table("user_logs").update({
                        "logout_time": now_mm,
                        "session_id": f"Tab Closed (X) - {now_mm}"
                    }).eq("id", session["id"]).execute()
            
            # သန့်ရှင်းရေးလုပ်ပြီးကြောင်း အမှတ်အသားပြုခြင်း
            st.session_state["cleanup_done"] = True
        except Exception as e:
            pass

# --- App Entry Point ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

# 🌟 Form တွေ ထပ်မနေစေရန်အတွက် ရှင်းလင်းသော ဖွဲ့စည်းမှု Logic
if not st.session_state["logged_in"]:
    login_form()
else:
    # Login ဝင်ပြီးမှသာ နောက်ကွယ်က သန့်ရှင်းရေးလုပ်ငန်းကို လုပ်ဆောင်ပြီး Main App ကို ပြသမည်
    auto_cleanup_expired_logs()
    main_app()
