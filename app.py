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
                
                st.success("Login successful!")
                st.rerun() 
            else:
                st.error("Username or Password is incorrect.")

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
                st.error("⚠️ Your account has been accessed from another browser or location, so you have been logged out.")
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
        tab1, tab2, tab3, tab4 = st.tabs(["➕ Add New Record", "📊 View Records", "📜 User Logs", "👥 User Management"])
    else:
        # User ဖြစ်ပါက View Records တစ်ခုတည်းကိုသာ Single Tab အနေဖြင့် ပြပါမည်
        tab2, = st.tabs(["📊 View Records"])
        tab1 = None
        tab3 = None # User အတွက် logs tab ကို ပိတ်ထားပါမယ်
        tab4 = None # User အတွက် user management tab ကို ပိတ်ထားပါမယ်

    # --- Tab 1: Add New Record (Admin Only) ---
    if tab1:
        with tab1:
            st.subheader("Add Information to Blacklist")
            with st.form("entry_form", clear_on_submit=True):
                name = st.text_input("(Full Name)")
                nrc = st.text_input("(NRC)")
                company = st.text_input("(Company Name)")
                address = st.text_area("(Address)")
                reason = st.text_area("(Reason)")
                
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
                        msg_container.success(f"{name} data saved successfully!")
                        time.sleep(3)
                        msg_container.empty()
                    else:
                        st.warning("Must provide at least Name and Reason to save the record.")

    # --- Tab 2: View Records (Both Admin and User) ---
    with tab2:
        st.subheader("📊 Blacklist Data")
        
        def reset_page():
            st.session_state.current_page = 1

        # Search UI
        search_col1, search_col2 = st.columns(2)
        with search_col1:
            name_search = st.text_input("🔍 Search by Name", placeholder="Name", on_change=reset_page)
        with search_col2:
            search_query = st.text_input("🔍 Search by NRC/PB", placeholder="NRC/PB", on_change=reset_page)
        
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
                                    st.success("Data Deleted Successfully!")
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
                                    st.success("Update Successfully")
                                    import time
                                    time.sleep(1)
                                    st.rerun()
                            with f_col2:
                                if st.form_submit_button("❌ Cancel"):
                                    st.session_state[edit_key] = False
                                    st.rerun()
        else:
            st.write("No Record")
    if tab3:
        with tab3:
            st.subheader("📜 User Access Logs (Audit Trail)")
            
            @st.fragment(run_every=10)
            def show_auto_refresh_logs():
                # 🌟 ပြင်ဆင်ချက် - အောက်က ကုဒ်တွေအားလုံးကို ရှေ့က Space (၄) ချက်စီ ပိုတွန်းပြီး Function ထဲ သွတ်သွင်းပေးလိုက်ပါတယ်ဗျာ
                with st.form("logs_filter_form"):
                    st.write("🔍 **Filter User Logs**")
                    col1, col2 = st.columns(2)
                    with col1:
                        search_username = st.text_input("Search by Username", placeholder="e.g., admin, 001")
                    with col2:
                        # ရက်စွဲအလိုက် စစ်ထုတ်ချင်လျှင် သုံးရန်
                        filter_date = st.date_input("Select Date", value=None)
                
                    filter_submitted = st.form_submit_button("Refresh & Filter Logs")

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
                                return "Active Now"
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
                            "(Username)": log['username'],
                            "(Login Time)": login_local,
                            "(Logout Time)": logout_local,
                            "Session ID": log['session_id']
                        })

                    if formatted_logs:
                        df_logs = pd.DataFrame(formatted_logs)
                        st.dataframe(df_logs, use_container_width=True, hide_index=True)
                        st.caption(f"🔄 total logs: {len(df_logs)} (Auto-Refresh every 10 seconds)")
                    else:
                        st.info("no logs found for the given filter criteria.")
                else:
                    st.write("no Logs data found.")

            # 🌟 အရေးကြီးဆုံးအချက် - တည်ဆောက်ထားသော auto refresh function အား အောက်ဆုံးမှ ပြန်လည် ခေါ်ယူပတ်မောင်းခြင်း
            show_auto_refresh_logs()

    # ----------------------------------------------------
    # ⚙️ Tab 4: User Setup & Management (Admin Only)
    # ----------------------------------------------------
    if tab4:
        with tab4:
            st.subheader("⚙️ User Account Management Setup")
            st.write("Account Setup & management")
            
            # --- State Management for Edit Mode ---
            if "edit_user_mode" not in st.session_state:
                st.session_state["edit_user_mode"] = False
                st.session_state["edit_user_data"] = None

            @st.fragment
            def manage_users_crud():
                # ========================================================
                # 1. READ & DISPLAY USERS (အသုံးပြုသူများစာရင်း ပြသခြင်း)
                # ========================================================
                users_res = supabase.table("users").select("*").order("username").execute()
                users_list = users_res.data if users_res.data else []
                
                # ပြသရန်အတွက် DataFrame ပုံစံပြောင်းခြင်း
                if users_list:
                    import pandas as pd
                    view_data = []
                    for u in users_list:
                        view_data.append({
                            "(Name)": u.get("name", "-"),
                            "(Username)": u.get("username"),
                            "(Role)": str(u.get("role")).upper(),
                            "(Current Session)": u.get("current_session_id", "No Active Session")
                        })
                    df_users = pd.DataFrame(view_data)
                    st.write("📊 user list")
                    st.dataframe(df_users, use_container_width=True)
                else:
                    st.info("no users found in the system. Please add new users using the form below.")
                
                st.divider()

                # ========================================================
                # 2. CREATE (Add New) & UPDATE (Edit) FORM UI
                # ========================================================
                if st.session_state["edit_user_mode"]:
                    st.write("📝 update selected account")
                    current_u = st.session_state["edit_user_data"]
                    
                    with st.form("edit_user_form"):
                        input_name = st.text_input("Name", value=current_u.get("name", ""))
                        # Username ကို ပြင်ခွင့်မပြုဘဲ Lock ချထားပါမည် (Primary Key သဘောမို့လို့ပါ)
                        st.text_input("Username (No Edit)", value=current_u.get("username"), disabled=True)
                        input_password = st.text_input("New Password", type="password", placeholder="New Password")
                        input_role = st.selectbox("Role", ["user", "admin"], index=0 if current_u.get("role") == "user" else 1)
                        
                        col_f1, col_f2 = st.columns(2)
                        with col_f1:
                            save_edit = st.form_submit_button("💾 Save Updates")
                        with col_f2:
                            cancel_edit = st.form_submit_button("❌ Cancel")

                    if save_edit:
                        update_payload = {
                            "name": input_name,
                            "role": input_role
                        }
                        # Password ဖြည့်ခဲ့မှသာ Update လုပ်မည်
                        if input_password.strip():
                            update_payload["password"] = input_password # 💡 ပိုမိုကောင်းမွန်လိုပါက Hash လုပ်နိုင်ပါသည်

                        supabase.table("users").update(update_payload).eq("username", current_u.get("username")).execute()
                        st.success(f"✨ Username: {current_u.get('username')} id updated successfully!")
                        st.session_state["edit_user_mode"] = False
                        st.session_state["edit_user_data"] = None
                        st.rerun()

                    if cancel_edit:
                        st.session_state["edit_user_mode"] = False
                        st.session_state["edit_user_data"] = None
                        st.rerun()

                else:
                    # ADD NEW USER FORM
                    st.write("Add New User")
                    with st.form("add_user_form", clear_on_submit=True):
                        new_name = st.text_input("Name", placeholder="Name")
                        new_username = st.text_input("Username", placeholder="username")
                        new_password = st.text_input("Password", type="password", placeholder="password")
                        new_role = st.selectbox("Define Role", ["user", "admin"])
                        
                        submit_add = st.form_submit_button("➕ Add New")

                    if submit_add:
                        if not new_username.strip() or not new_password.strip() or not new_name.strip():
                            st.error("⚠️ input complete informations to create new account")
                        else:
                            # Username ထပ်နေခြင်း ရှိ/မရှိ ကြိုစစ်ခြင်း
                            check_exist = supabase.table("users").select("username").eq("username", new_username.strip()).execute()
                            if check_exist.data:
                                st.error("⚠️ Username already exists. Please choose a different username.")
                            else:
                                insert_payload = {
                                    "name": new_name.strip(),
                                    "username": new_username.strip(),
                                    "password": new_password.strip(),
                                    "role": new_role,
                                    "current_session_id": None
                                }
                                supabase.table("users").insert(insert_payload).execute()
                                st.success(f"🎉 New user added successfully: {new_name} ({new_username})")
                                st.rerun()

                st.divider()

                # ========================================================
                # 3. EDIT & DELETE ACTION BUTTONS (ပြင်ဆင်ရန်နှင့် ဖျက်ရန် ခလုတ်များ)
                # ========================================================
                if users_list and not st.session_state["edit_user_mode"]:
                    st.write("🛠️ Select account for update or delete")
                    
                    # ကွင်းစနစ်ဖြင့် ရွေးချယ်ခိုင်းခြင်း
                    user_options = [f"{u.get('name')} ({u.get('username')})" for u in users_list]
                    selected_user_str = st.selectbox("Select an account", user_options)
                    
                    # ရွေးလိုက်တဲ့ အကောင့်ရဲ့ index ကို ပြန်ရှာခြင်း
                    selected_index = user_options.index(selected_user_str)
                    target_user_data = users_list[selected_index]

                    col_act1, col_act2 = st.columns(2)
                    
                    with col_act1:
                        if st.button("📝 update selected account", use_container_width=True):
                            st.session_state["edit_user_mode"] = True
                            st.session_state["edit_user_data"] = target_user_data
                            st.rerun()
                            
                    with col_act2:
                        # လုံခြုံရေးအရ admin အကောင့်ကို အလွယ်တကူ အမှားအယွင်း ဖျက်မိခြင်းမှ ကာကွယ်ရန်
                        if target_user_data.get("username") == "admin":
                            st.warning("🔒 cannot delete 'admin' account")
                        else:
                            if st.button("🗑️ delete selected account", use_container_width=True, type="secondary"):
                                # ဒေတာဘေ့စ်မှ ဖျက်ထုတ်ခြင်း
                                supabase.table("users").delete().eq("username", target_user_data.get("username")).execute()
                                st.success(f"🗑️ Username: {target_user_data.get('username')} deleted successfully.")
                                st.rerun()

            # --- မော်ဂျူးအား လှမ်းခေါ်ခြင်း ---
            manage_users_crud()

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
