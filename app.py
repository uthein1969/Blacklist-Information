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
    st.title("🚫 Blacklist Information System")
    st.subheader("Login to access the system")

    # ၁။ Form UI ကို ဒေတာလက်ခံရန် သီးသန့်ဆောက်ခြင်း
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit_button = st.form_submit_button("Login")

    # 🌟 Submit Button နှိပ်လိုက်သည့် Logic
    if submit_button:
        user_data = check_login(username, password)
        if user_data:
            import uuid
            
            # ၁။ စနစ်တစ်ခုလုံးအတွက် Unique Session ID ထုတ်ယူခြင်း
            unique_session_id = str(uuid.uuid4())
            
            # ========================================================
            # 🌟 ပြင်ဆင်ချက် ၁ - Multi-Browser တားဆီးရန် အဟောင်းကို ကန်ထုတ် (Kick Out) သည့် Logic စနစ်သစ်
            # ========================================================
            # Users Table ထဲတွင် လက်ရှိ ၎င်း Username ဖြင့် Active ဖြစ်နေသော Browser ရှိမရှိ အရင်စစ်ဆေးခြင်း
            user_check = supabase.table("users").select("current_session_id").eq("username", username).execute()
            
            if user_check.data and user_check.data[0].get("current_session_id"):
                old_session_id = user_check.data[0].get("current_session_id")
                
                # 💡 logout_time ကို လိုက်ပြင်မည့်အစား... အခြား Browser ကန်ထုတ်ခံရကြောင်း Row အသစ် (INSERT) သီးသန့် ကွက်တိမှတ်ပေးလိုက်ခြင်း
                log_user_activity(
                    username=username,
                    action="Kicked Out (Multi-Browser Prevention)",
                    status="Success",
                    session_id=old_session_id
                )

            # 🔗 ၂။ Supabase `users` table အား UPDATE သွားလုပ်ခြင်း (Session သစ်လဲခြင်း)
            supabase.table("users").update({"current_session_id": unique_session_id}).eq("username", username).execute()
            
            # ၃။ Streamlit Session State များထဲတွင် စနစ်တကျ တစ်သားတည်း သိမ်းဆည်းခြင်း
            st.session_state["logged_in"] = True
            st.session_state["user_info"] = user_data[0]
            st.session_state["current_session_id"] = unique_session_id
            
            # 🔗 ၄။ user_logs table ထဲသို့ ဗိသုကာသစ်အတိုင်း အချိန်ရော Action ပါ တစ်ခါတည်း INSERT သွင်းခြင်း
            # (မူရင်း log_data နှင့် insert() လိုင်းဟောင်းကြီးအား လုံးဝ ဖြုတ်ပစ်လိုက်ပါပြီဗျာ)
            log_user_activity(username, action="Login", status="Success", session_id=unique_session_id)
            
            # 🌟 Screen အဟောင်းကို လုံးဝ Flush ဖြစ်သွားအောင် Force Rerun လုပ်ခြင်း
            st.success("Login successful!")
            st.rerun() 
        else:
            # ၅။ Login Fail ဖြစ်လျှင်လည်း No Active Session ဖြင့် ကွက်တိမှတ်ပေးခြင်း
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
        
        # 🌟 ပြင်ဆင်ချက် ၁ - user_info ရဲ့အထဲကမဟုတ်ဘဲ Login ဝင်စဉ်က မှတ်ခဲ့သော ပင်မ Local Session ID အစစ်ကို ဆွဲယူခြင်း
        my_session_id = st.session_state.get("current_session_id")
        
        # Database ထဲက လက်ရှိ Live ဖြစ်နေတဲ့ Session ID ကို လှမ်းစစ်ခြင်း
        db_user = supabase.table("users").select("current_session_id").eq("username", username).execute()
        
        if db_user.data:
            live_session_id = db_user.data[0].get("current_session_id")
            
            # 🌟 ပြင်ဆင်ချက် ၂ - Local ID ရော Database ID ပါ နှစ်ခုစလုံး ရှိနေမှသာ ကန်ထုတ်ရန် ယှဉ်စစ်ခြင်း (Login စက္ကန့်တွင် ငြိမတက်စေရန်)
            if live_session_id and my_session_id:
                if my_session_id != live_session_id:
                    # အကယ်၍ အခြား Browser တစ်ခုခုကနေ ဝင်လိုက်လို့ ID ချိန်းသွားခဲ့ရင် အလိုအလျောက် ကန်ထုတ်မည်
                    st.session_state["logged_in"] = False
                    st.session_state["user_info"] = None
                    st.session_state["current_session_id"] = None
                    st.error("⚠️ Your account has been accessed from another browser or location, so you have been logged out.")
                    import time; time.sleep(3)
                    st.rerun()

    # ရရှိလာသော user_info ထဲမှ user_role ကို ရယူခြင်း (မပါရှိပါက default အနေဖြင့် 'user' ဟု ယူပါမည်)
    user_role = st.session_state['user_info'].get('role', 'user')
    
    st.sidebar.write(f"Welcome, {st.session_state['user_info']['username']} ({user_role.upper()})")
    if st.sidebar.button("Logout"):
        # 🌟 LOGOUT TIME အား UPDATE လုပ်ခြင်း
        if "current_session_id" in st.session_state:
            from datetime import datetime
            import pytz
            
            # --- Logout ခလုတ်နှိပ်သည့်နေရာရှိ အမှန်ကန်ဆုံးနှင့် အလုံခြုံဆုံး Logic ---
            
            # မြန်မာစံတော်ချိန်ဖြင့် ထွက်သည့် အချိန်ကို ရယူခြင်း
            tz = pytz.timezone('Asia/Yangon')
            now_mm = datetime.now(tz).isoformat()
            
            current_username = st.session_state['user_info']['username']
            current_session_id = st.session_state["current_session_id"]
            
            # 🌟 ဖြေရှင်းချက် - အဟောင်းတွေကို Overwrite မဖြစ်စေရန် 
            # log_user_activity ဖန်ရှင်ကို သုံးပြီး Logout Event အတွက် Row အသစ်သီးသန့် (INSERT) သွင်းပေးလိုက်ခြင်း ဖြစ်ပါတယ်ဗျာ
            log_user_activity(
                username=current_username,
                action="Logout",
                status="Success",
                session_id=current_session_id
            )
            
            # ၎င်းနောက်မှ Users Table ထဲက Session ID ကို NULL ချပစ်ခြင်း (မူရင်းအတိုင်း)
            supabase.table("users").update({"current_session_id": None}).eq("username", current_username).execute()
        
        # စက်ထဲက Memory အားလုံးကို အပြီးသတ် ဖျက်ထုတ်ပြီး Page ကို Rerun လုပ်ခြင်း
        st.session_state.clear()
        st.success("Logged out successfully!")
        st.rerun() 

    st.header("🚫 Blacklist Information Management")
    
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
            
            # Form UI တည်ဆောက်ခြင်း
            with st.form("entry_form", clear_on_submit=True):
                name = st.text_input("(Full Name)")
                nrc = st.text_input("(NRC/PB)")
                company = st.text_input("(Company Name)")
                address = st.text_area("(Address)")
                reason = st.text_area("(Reason)")
                
                # 📸 ပုံဖိုင်လက်ခံရန် File Uploader
                uploaded_file = st.file_uploader("📸 (NRC Photo)", type=["png", "jpg", "jpeg"])
                
                submitted = st.form_submit_button("Save Data")
                
            # --- Form Submit လုပ်ပြီးနောက် လုပ်ဆောင်မည့် Logic အပိုင်း (Form အပြင်ဘက်) ---
            if submitted:
                if name and reason:
                    photo_url = None  # မူလအစတွင် ဓာတ်ပုံလင့်ခ်အား ဗလာအဖြစ် ထားရှိခြင်း
                    
                    # 🌟 အကယ်၍ အသုံးပြုသူက ပုံရွေးချယ် တင်ခဲ့လျှင်
                    if uploaded_file is not None:
                        try:
                            # ဖိုင်အမျိုးအစား extension အား စစ်ထုတ်ခြင်း (png, jpg)
                            file_ext = uploaded_file.name.split(".")[-1]
                            
                            # ဖိုင်အမည် တူညီမှုမရှိစေရန် သန့်စင်ပြီး စနစ်တကျ အမည်ပေးခြင်း
                            clean_nrc = nrc.strip().replace("/", "_").replace("(", "_").replace(")", "_").replace(" ", "")
                            if not clean_nrc:  # အကယ်၍ NRC မထည့်ခဲ့ပါက random သုံးမည်
                                clean_nrc = "unknown"
                            
                            # 🌟 ပြင်ဆင်ချက် ၁ - time.time() ရှေ့တွင် import time ကို ကပ်လျက် ထည့်သွင်းခြင်း
                            import time
                            unique_timestamp = int(time.time())
                            storage_file_name = f"nrc_{clean_nrc}_{unique_timestamp}.{file_ext}"
                            
                            # ဖိုင်၏ ဒေတာဗိုက်စ်များအား ဖတ်ယူခြင်း
                            file_data = uploaded_file.getvalue()
                            
                            # Supabase Storage ("blacklist-images") ထဲသို့ ပုံလှမ်းတင်ခြင်း
                            supabase.storage.from_("blacklist-images").upload(
                                path=storage_file_name,
                                file=file_data,
                                file_options={"content-type": f"image/{file_ext}"}
                            )
                            
                            # တင်ပြီးသွားသော ပုံ၏ အများပြည်သူကြည့်ရှုနိုင်မည့် Public URL လင့်ခ်အား ပြန်လည်ရယူခြင်း
                            photo_url = supabase.storage.from_("blacklist-images").get_public_url(storage_file_name)
                            
                        except Exception as e:
                            st.error(f"⚠️ Error uploading image to storage: {str(e)}")
                    
                    # 🌟 ဒေတာဘေ့စ်ထဲသို့ သွားရောက်သိမ်းဆည်းမည့် Payload ဒေတာအစုအဝေး
                    data = {
                        "full_name": name.strip(),
                        "nrc_number": nrc.strip(),
                        "Remark1": company.strip(),    
                        "Remark2": address.strip(),    
                        "reason": reason.strip(),
                        "blacklisted_by": st.session_state['user_info']['username'],
                        "image_url": photo_url  # 📸 ပုံရှိလျှင် URL လင့်ခ်၊ မရှိလျှင် None (NULL) အဖြစ် တွဲသိမ်းမည်
                    }
                    
                    # Database Table ထဲသို့ Insert လုပ်ခြင်း
                    response = supabase.table("blacklist_records").insert(data).execute()
                    
                    # ========================================================
                    # 🌟 ပြင်ဆင်ချက် ၁ - data (Payload) ထဲက full_name ကို ကွက်တိ ဆွဲထုတ်၍ Log မှတ်ခြင်း
                    # ========================================================
                    current_admin = st.session_state["user_info"]["username"]
                    log_user_activity(
                        username=current_admin, 
                        # 💡 blacklist_payload အစား အပေါ်က သုံးထားတဲ့ data ကို ပြောင်းလဲအသုံးပြုလိုက်ပါတယ်ဗျာ
                        action=f"Add New Record ({data.get('full_name', 'Unknown')})", 
                        status="Success"
                    )
                    
                    # ========================================================
                    # 🌟 ပြင်ဆင်ချက် ၂ - အလှပြမည့် ကုဒ်များ အလုပ်လုပ်စေရန် အပေါ်က st.rerun() အပိုကို ဖြုတ်လိုက်ပါသည်
                    # ========================================================
                    
                    # အောင်မြင်ကြောင်း မက်ဆေ့ခ်ျအား စက္ကန့်ပိုင်းပြသပြီး မျက်နှာပြင်အား အော်တို Refresh လုပ်ခြင်း
                    msg_container = st.empty()
                    # data ထဲက full_name ကို တိုက်ရိုက်ယူသုံးပြီး ပြသခြင်း
                    msg_container.success(f"🎉 {data.get('full_name', 'Record')} data saved successfully with image!")
                    
                    # 🌟 time.sleep(2) အတွက် အတင်းအကျပ် import time လုပ်ခြင်း
                    import time
                    time.sleep(2)
                    
                    msg_container.empty()
                    st.rerun()  # 💡 အားလုံး ပြီးမှသာ အောက်ဆုံးတွင် တစ်ခါတည်း အပြီးသတ် Rerun လုပ်ခိုင်းပါသည်
                    
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
            
            # 🌟 ဤလိုင်းအောက်ရှိ ကုဒ်အားလုံးကို ညာဘက်သို့ Space (၄) ချက်စီ ညီညာစွာ တွန်းရွှေ့ပေးလိုက်ပါပြီဗျာ
        for i, record in enumerate(page_data, start=start_idx + 1):
            raw_nrc = str(record['nrc_number']).strip() if record['nrc_number'] else ""
            prefix = "NRC" if raw_nrc and raw_nrc[0].isdigit() else "PB"
            
            with st.expander(f"{i} 👤 {record['full_name']} ({prefix}: {raw_nrc})"):
                edit_key = f"edit_mode_{record['id']}"
                if edit_key not in st.session_state:
                    st.session_state[edit_key] = False
                
                # --- Dialog Function (ပုံနှစ်ခါမပွားဘဲ ဘောင်နှင့် ကွက်တိဖြစ်စေမည့် အမှန်ကန်ဆုံးဗားရှင်း) ---
                @st.dialog("📸 NRC Photo View", width="small")
                def popup_image_dialog(url, name, dlg_id):
                    st.html("""
                        <style>
                            [data-testid="stDialog"] > div > div {
                                padding: 1rem 0rem 1rem 0rem !important;
                            }
                            /* စာသားလေး ဘေးဘောင်နှင့် ကပ်မနေစေရန် */
                            [data-testid="stDialog"] .stMarkdown {
                                padding-left: 1.5rem !important;
                                padding-right: 1.5rem !important;
                            }
                        </style>
                    """)
                    
                    st.write(f"**Name:** {name}")
                    
                    # 🌟 ပြင်ဆင်ချက် ၁ - ဤနေရာတွင် container အကျယ်အတိုင်း ကွက်တိပြရန် st.image (တစ်လိုင်းတည်းသာ) ထားရှိပါသည်
                    st.image(url, use_container_width=True)

                    st.divider()
                    
                    # 🌟 ပြင်ဆင်ချက် ၂ - အောက်က ပုံအပိုကြီးကို ဖြုတ်လိုက်ပြီး Close ခလုတ်လေးကိုပဲ စမတ်ကျကျ အလယ်တည့်တည့် ညှိလိုက်ပါတယ်ဗျာ
                    col1, col2, col3 = st.columns([1, 2, 1])
                    with col2:
                        if st.button("Close", key=f"close_dlg_{dlg_id}", use_container_width=True):
                            st.rerun()
                            
                    st.write("") # အောက်ခြေ အနည်းငယ် လှပစေရန် Space ခံခြင်း

                # --- Edit Mode မဟုတ်လျှင် (ပုံမှန်ပြသရန်) ---
                if not st.session_state[edit_key]:
                    st.write(f"**Reason:** {record['reason']}")
                    st.write(f"**Listed by:** {record['blacklisted_by']}")
                    st.write(f"**Company:** {record['Remark1']}")
                    st.write(f"**Address:** {record['Remark2']}")
                    
                    if record.get("image_url"):
                        if st.button("📸 View Image", key=f"btn_img_{record['id']}", use_container_width=True, type="secondary"):
                            popup_image_dialog(record["image_url"], record.get("full_name", "Unknown"), record['id'])
                    else:
                        st.button("❌ No Image Available", key=f"btn_no_img_{record['id']}", use_container_width=True, disabled=True)

                    st.write("") 

                    # --- Admin Logic ---
                    if user_role == 'admin':
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("📝 Edit", key=f"btn_edit_{record['id']}", use_container_width=True):
                                st.session_state[edit_key] = True
                                st.rerun()
                        with col2:
                            if st.button("🗑️ Delete", key=f"btn_del_{record['id']}", use_container_width=True):
                                # 🌟 ဖြေရှင်းချက် - ဒေတာမဖျက်ခင် ၎င်း record ထဲတွင် ရှိပြီးသား full_name ကို တိုက်ရိုက်ဆွဲထုတ်ယူခြင်း
                                deleted_name = record.get('full_name', f"ID: {record['id']}")
                                
                                # ၁။ ဒေတာဘေ့စ်ထဲမှ Blacklist Record အား အပြီးသတ်ဖျက်ခြင်း
                                supabase.table("blacklist_records").delete().eq("id", record["id"]).execute()

                                # ၂။ Audit Log ထဲသို့ Full Name ဖြင့် ကွက်တိ မှတ်တမ်းတင်ခြင်း
                                current_admin = st.session_state["user_info"]["username"]
                                log_user_activity(
                                    username=current_admin, 
                                    action=f"Delete Record ({deleted_name})",  # 💡 ဤနေရာတွင် နာမည်အတိုင်း တိုက်ရိုက်လှပစွာ ပေါ်လာပါမည်
                                    status="Success"
                                )
                                
                                st.success("Data Deleted Successfully!")
                                import time; time.sleep(1)
                                st.rerun()
                    else:
                        st.caption("🔒 View Only Mode (Admin access required to Edit/Delete)")
                
                # ========================================================
                # Edit Mode ဖြစ်နေလျှင် (Form ပြရန် - Admin သီးသန့်)
                # ========================================================
                else:
                    # ၁။ Form UI တည်ဆောက်ခြင်း (ဒေတာများနှင့် File Uploader သီးသန့်ပြသမည်)
                    with st.form(key=f"form_edit_{record['id']}"):
                        new_name = st.text_input("Name", value=record['full_name'])
                        new_nrc = st.text_input("NRC", value=record['nrc_number'])
                        new_company = st.text_input("Company", value=record['Remark1'])
                        new_address = st.text_input("Address", value=record['Remark2'])
                        new_reason = st.text_area("Reason", value=record['reason'])
                        
                        # 📸 ဓာတ်ပုံအသစ်လဲရန် File Uploader
                        edit_uploaded_file = st.file_uploader("📸 Change NRC Photo (ပုံအသစ်လဲလိုပါက ရွေးချယ်ပါ)", type=["png", "jpg", "jpeg"], key=f"file_edit_{record['id']}")
                        
                        f_col1, f_col2 = st.columns(2)
                        with f_col1:
                            update_submitted = st.form_submit_button("✅ Update", use_container_width=True, key=f"sub_upd_{record['id']}")
                        with f_col2:
                            cancel_submitted = st.form_submit_button("❌ Cancel", use_container_width=True, key=f"sub_can_{record['id']}")
                            
                    # 🌟 ခလုတ်များ၏ လုပ်ဆောင်ချက် (Logic) ကို Form ၏ အပြင်ဘက်တွင် လုပ်ဆောင်ခြင်း
                    if update_submitted:
                        
                        # ========================================================
                        # 🌟 ဖြေရှင်းချက် - တကယ် ပြောင်းလဲသွားသည့် ကွက်လပ် (Fields) များကိုသာ ရှာဖွေစစ်ထုတ်ခြင်း
                        # ========================================================
                        changes_list = []
                        
                        # ၁။ Name စစ်ဆေးခြင်း
                        if record.get('full_name', '').strip() != new_name.strip():
                            changes_list.append(f"Name: '{record.get('full_name')}' ➡️ '{new_name.strip()}'")
                            
                        # ၂။ NRC စစ်ဆေးခြင်း
                        if record.get('nrc_number', '').strip() != new_nrc.strip():
                            changes_list.append(f"NRC: '{record.get('nrc_number')}' ➡️ '{new_nrc.strip()}'")
                            
                        # ၃။ Company (Remark1) စစ်ဆေးခြင်း
                        if record.get('Remark1', '').strip() != new_company.strip():
                            changes_list.append(f"Company: '{record.get('Remark1')}' ➡️ '{new_company.strip()}'")
                            
                        # ၄။ Address (Remark2) စစ်ဆေးခြင်း
                        if record.get('Remark2', '').strip() != new_address.strip():
                            changes_list.append(f"Address: '{record.get('Remark2')}' ➡️ '{new_address.strip()}'")
                            
                        # ၅။ Reason စစ်ဆေးခြင်း
                        if record.get('reason', '').strip() != new_reason.strip():
                            changes_list.append(f"Reason: '{record.get('reason')}' ➡️ '{new_reason.strip()}'")
                            
                        # ၆။ ဓာတ်ပုံအသစ် တင်မတင် စစ်ဆေးခြင်း
                        if edit_uploaded_file is not None:
                            changes_list.append("📸 NRC Photo: 'Updated New Image'")

                        # မူလအစတွင် ဒေတာဘေ့စ်ထဲရှိ ပုံဟောင်း URL လင့်ခ်အတိုင်း ထားရှိမည်
                        final_photo_url = record.get("image_url")
                        
                        # အကယ်၍ အသုံးပြုသူက ပုံအသစ် ရွေးချယ်တင်လိုက်လျှင်
                        if edit_uploaded_file is not None:
                            try:
                                file_ext = edit_uploaded_file.name.split(".")[-1]
                                clean_nrc = new_nrc.strip().replace("/", "_").replace("(", "_").replace(")", "_").replace(" ", "")
                                if not clean_nrc:
                                    clean_nrc = "unknown"
                                    
                                import time
                                unique_timestamp = int(time.time())
                                storage_file_name = f"nrc_{clean_nrc}_{unique_timestamp}.{file_ext}"
                                file_data = edit_uploaded_file.getvalue()
                                
                                # Supabase Storage သို့ ပုံအသစ်အား Upload တင်ခြင်း
                                supabase.storage.from_("blacklist-images").upload(
                                    path=storage_file_name,
                                    file=file_data,
                                    file_options={"content-type": f"image/{file_ext}"}
                                )
                                
                                # ပုံအသစ်၏ Public URL လင့်ခ်ကို ရယူခြင်း
                                final_photo_url = supabase.storage.from_("blacklist-images").get_public_url(storage_file_name)
                                
                            except Exception as e:
                                st.error(f"⚠️ Error uploading new image: {str(e)}")
                                
                        # ဒေတာဘေ့စ်ထဲတွင် အချက်အလက်နှင့် ပုံလင့်ခ်အသစ်အား Update လုပ်ခြင်း
                        update_data = {
                            "full_name": new_name.strip(), 
                            "nrc_number": new_nrc.strip(), 
                            "reason": new_reason.strip(), 
                            "Remark1": new_company.strip(), 
                            "Remark2": new_address.strip(),
                            "image_url": final_photo_url
                        }
                        
                        supabase.table("blacklist_records").update(update_data).eq("id", record["id"]).execute()

                        # ========================================================
                        # 🌟 ပြောင်းလဲမှု (Changes) ရှိမှသာ စာသားဆောက်၍ Audit Log မှတ်သားခြင်း
                        # ========================================================
                        if changes_list:
                            # တကယ်ပြင်လိုက်တဲ့ အချက်အလက်တွေကိုပဲ Comma (,) ခံပြီး လှလှပပ ပြပေးမှာပါဗျာ
                            full_audit_action = f"Update Record ({new_name.strip()}) | ⚙️ Changes: {', '.join(changes_list)}"
                        else:
                            # ဘာမှမပြင်ဘဲ ခလုတ်နှိပ်သွားလျှင် No data changed ဟုသာ မှတ်ပါမည်
                            full_audit_action = f"Update Record ({new_name.strip()}) | No data changed"
                        
                        current_admin = st.session_state["user_info"]["username"]
                        log_user_activity(
                            username=current_admin, 
                            action=full_audit_action, 
                            status="Success"
                        )

                        st.session_state[edit_key] = False
                        st.success("Update Successfully with Image!")
                        import time; time.sleep(1)
                        st.rerun()
                        
                    if cancel_submitted:
                        st.session_state[edit_key] = False
                        st.rerun()
    if tab3:
        with tab3:
            st.subheader("📜 User Access Logs (Audit Trail)")
            
            # 🌟 ၁။ ISO Time မှ မြန်မာစံတော်ချိန်သို့ ပြောင်းလဲပေးမည့် ပင်မ Helper Function
            def to_local_time(iso_str):
                if not iso_str:
                    return "N/A"
                try:
                    from datetime import datetime
                    import pytz
                    utc_dt = datetime.fromisoformat(iso_str.replace('Z', '+00:00'))
                    mm_tz = pytz.timezone('Asia/Yangon')
                    return utc_dt.astimezone(mm_tz).strftime('%Y-%m-%d %I:%M:%S %p')
                except Exception:
                    return iso_str

            # 🌟 ၂။ Streamlit Fragment ဖြင့် ၁၀ စက္ကန့်တစ်ခါ ဇယားကိုသာ သီးသန့် Auto-Refresh လုပ်မည့်စနစ်
            @st.fragment(run_every=10)
            def show_auto_refresh_logs():
                import pandas as pd
                from datetime import datetime
                
                # --- FILTER FORM UI ---
                with st.form("logs_filter_form"):
                    st.write("🔍 **Filter User Logs**")
                    col1, col2 = st.columns(2)
                    with col1:
                        search_username = st.text_input("Search by Username", placeholder="e.g., admin, 001")
                    with col2:
                        filter_date = st.date_input("Select Date", value=None)
                
                    filter_submitted = st.form_submit_button("Refresh & Filter Logs")

                # --- SUPABASE QUERY (ဗိသုကာသစ်အတိုင်း Column များကို တောင်းဆိုခြင်း) ---
                try:
                    log_query = supabase.table("user_logs").select(
                        "id", "username", "action", "status", "action_date_time", "session_id"
                    )
                    
                    # Username Filter ပါက ထည့်သွင်းစစ်ထုတ်ခြင်း
                    if search_username.strip():
                        log_query = log_query.ilike("username", f"%{search_username.strip()}%")
                    
                    # ID အလိုက် အသစ်ဆုံးကို အပေါ်ကပြရန်
                    logs_response = log_query.order("id", desc=True).execute()

                    if logs_response.data:
                        formatted_logs = []
                        
                        for log in logs_response.data:
                            raw_time = log.get('action_date_time')
                            action_time_local = to_local_time(raw_time)

                            # Date Filter ပါက action_date_time အပေါ် အခြေခံ၍ စစ်ထုတ်ခြင်း
                            if filter_date and raw_time:
                                try:
                                    log_date_str = datetime.fromisoformat(raw_time.replace('Z', '+00:00')).strftime('%Y-%m-%d')
                                    if log_date_str != str(filter_date):
                                        continue  # ရက်စွဲမကိုက်ညီပါက ကျော်သွားမည်
                                except Exception:
                                    pass

                            # ဇယားအသစ်ဒီဇိုင်းအတွက် ဒေတာများအား စနစ်တကျ စုစည်းခြင်း
                            formatted_logs.append({
                                "Log ID": log.get('id'),
                                "Username": log.get('username'),
                                "Action": log.get('action', 'N/A'),
                                "Status": log.get('status', 'N/A'),
                                "Date & Time (MM)": action_time_local,
                                "Session ID": log.get('session_id')
                            })

                        # --- DATAFRAME UI DISPLAY ---
                        if formatted_logs:
                            df_logs = pd.DataFrame(formatted_logs)
                            st.dataframe(df_logs, use_container_width=True, hide_index=True)
                            st.caption(f"🔄 Total Logs: {len(df_logs)} (Auto-Refresh every 10 seconds)")
                        else:
                            st.info("No logs found for the given filter criteria.")
                    else:
                        st.info("No Logs data found in database.")
                        
                except Exception as e:
                    st.error(f"❌ Error loading logs: {e}")

            # 🌟 ၃။ တည်ဆောက်ထားသော Fragment Function အား ဤနေရာမှ စတင်ပတ်မောင်းနှင်ခြင်း
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

            # 🌟 ၅ စက္ကန့်တိုင်း အော်တို Auto-Refresh လုပ်ပေးမည့် ပင်မ Fragment Module
            @st.fragment(run_every=5)
            def manage_users_crud():
                # ========================================================
                # 1. READ & DISPLAY USERS (အသုံးပြုသူများစာရင်း ပြသခြင်း)
                # ========================================================
                st.cache_data.clear()
                users_res = supabase.table("users").select("*").order("username").execute()
                users_list = users_res.data if users_res.data else []
                
                if users_list:
                    import pandas as pd
                    view_data = []
                    for u in users_list:
                        session_val = u.get("current_session_id")
                        if session_val is None or session_val == "":
                            session_val = "None"
                            
                        view_data.append({
                            "(Name)": u.get("name", "-"),
                            "(Username)": u.get("username"),
                            "(Role)": str(u.get("role")).upper(),
                            "(Current Session)": session_val
                        })
                    df_users = pd.DataFrame(view_data)
                    st.write("📊 user list")
                    st.dataframe(df_users, use_container_width=True)
                else:
                    st.info("no users found in the system.")
                
                st.divider()

                # ========================================================
                # 2. CREATE (Add New) & UPDATE (Edit) FORM UI
                # ========================================================
                # 🌟 ပြင်ဆင်ချက် - ဤ Form များကိုပါ ဒေတာပြောင်းလဲလျှင် ချက်ချင်းသိစေရန် Fragment အတွင်းသို့ သွတ်သွင်းလိုက်ပါသည်
                if st.session_state["edit_user_mode"]:
                    st.write("📝 update selected account")
                    current_u = st.session_state["edit_user_data"]
                    
                    with st.form("edit_user_form"):
                        input_name = st.text_input("Name", value=current_u.get("name", ""))
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
                            if input_password.strip():
                                update_payload["password"] = input_password

                            supabase.table("users").update(update_payload).eq("username", current_u.get("username")).execute()

                            # 🌟 ၃။ ဝန်ထမ်းအကောင့်အား ပြင်ဆင်မှု အောင်မြင်ကြောင်း မှတ်ရန်
                            current_admin = st.session_state["user_info"]["username"]
                            log_user_activity(current_admin, action=f"Update User ({current_u.get('username')})", status="Success")

                            st.success(f"✨ Username: {current_u.get('username')} updated successfully!")
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
                                st.error("⚠️ input complete information to create new account")
                            else:
                                check_exist = supabase.table("users").select("username").eq("username", new_username.strip()).execute()
                                if check_exist.data:
                                    log_user_activity(st.session_state["user_info"]["username"], action="Create User", status="Fail")
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
                                    
                                    # 🌟 အကောင့်သစ် ဆောက်တာ အောင်မြင်သွားကြောင်း မှတ်ရန်
                                    current_admin = st.session_state["user_info"]["username"]
                                    log_user_activity(current_admin, action=f"Create User ({new_username.strip()})", status="Success")
                                    
                                    st.success(f"🎉 New user added successfully: {new_name} ({new_username})")
                                    st.rerun()

                st.divider()
                
                # ========================================================
                # 3. EDIT & DELETE ACTION BUTTONS (ပြင်ဆင်ရန်နှင့် ဖျက်ရန် ခလုတ်များ)
                # ========================================================
                # 🌟 ပြင်ဆင်ချက် - users_list အား တိုက်ရိုက်သိရှိနိုင်ရန် ဤနေရာသို့ နေရာရွှေ့ပေးလိုက်ပါသည်
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
                        if target_user_data.get("username") == "admin":
                            st.warning("🔒 cannot delete 'admin' account")
                        else:
                            if st.button("🗑️ delete selected account", use_container_width=True, type="secondary"):
                                supabase.table("users").delete().eq("username", target_user_data.get("username")).execute()

                                # 🌟 ၄။ ဝန်ထမ်းအကောင့်အား ဖျက်သိမ်းမှု အောင်မြင်ကြောင်း မှတ်ရန်
                                current_admin = st.session_state["user_info"]["username"]
                                log_user_activity(current_admin, action=f"Delete User ({target_user_data.get('username')})", status="Success")

                                st.success(f"🗑️ Username: {target_user_data.get('username')} deleted successfully.")
                                st.rerun()

            # ========================================================
            # 🌟 အရေးကြီးဆုံးအချက် - ဤနေရာတွင် Function အား လှမ်းခေါ်ခြင်း
            # ========================================================
            manage_users_crud()

# 🌟 Column တစ်ခုတည်းဖြင့် အချိန်ကို သန့်ရှင်းစွာမှတ်ပေးမည့် Event-based Log Function
def log_user_activity(username, action, status, session_id=None):
    try:
        import pytz
        from datetime import datetime
        
        # မြန်မာစံတော်ချိန် လက်ရှိ Timestamp အား တိကျစွာ ရယူခြင်း
        tz = pytz.timezone('Asia/Yangon')
        now_mm = datetime.now(tz).isoformat()
        
        if not session_id:
            session_id = st.session_state.get("current_session_id", "No Active Session")
            
        log_payload = {
            "username": username,
            "session_id": session_id,
            "action": action,
            "status": status,
            "action_date_time": now_mm  # 🌟 ဘယ်အလုပ်မဆို ဤ Column တစ်ခုတည်း၌သာ အချိန်ကွက်တိမှတ်ပါမည်
        }
        supabase.table("user_logs").insert(log_payload).execute()
    except Exception as e:
        print(f"Log Error: {e}")

# --- App Entry Point ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

# ====================================================
# 🌟 LOGOUT မလုပ်ဘဲ Close (X) လုပ်သွားသူများကို လိုက်မှတ်ပေးမည့် စနစ်သစ်
# ====================================================
def auto_cleanup_expired_logs():
    # Session State ကို သုံးပြီး တစ်ခေါက်ပဲ Run စေရန် Lock ခတ်ခြင်း
    if "cleanup_done" not in st.session_state:
        try:
            from datetime import datetime, timedelta
            import pytz
            
            tz = pytz.timezone('Asia/Yangon')
            # ၃ နာရီထက် ကျော်လွန်နေသော အချိန်ကန့်သတ်ချက် သတ်မှတ်ခြင်း
            time_limit = datetime.now(tz) - timedelta(hours=3)
            time_limit_iso = time_limit.isoformat()
            
            # 🌟 ၁။ ၃ နာရီအတွင်း ဘာ Action မှမရှိတော့တဲ့ လတ်တလော Active ဖြစ်နေဆဲ Users များကို ရှာခြင်း
            # users table ထဲတွင် current_session_id ရှိနေပြီး user_logs ထဲတွင် ၃ နာရီကျော် ဒေတာငြိမ်နေသူများကို စစ်ထုတ်ပါမည်
            active_users = supabase.table("users").select("username", "current_session_id").not_.is_("current_session_id", "null").execute()
            
            if active_users.data:
                for user in active_users.data:
                    username = user["username"]
                    session_id = user["current_session_id"]
                    
                    # ၎င်း Session ၏ နောက်ဆုံးလှုပ်ရှားမှုအချိန်ကို ရှာခြင်း
                    last_log = supabase.table("user_logs") \
                        .select("action_date_time") \
                        .eq("session_id", session_id) \
                        .order("id", descending=True) \
                        .limit(1) \
                        .execute()
                        
                    if last_log.data:
                        last_action_time = last_log.data[0]["action_date_time"]
                        
                        # 🌟 ၂။ အကယ်၍ နောက်ဆုံးလှုပ်ရှားခဲ့သည့်အချိန်သည် ၃ နာရီထက် ကျော်လွန်နောက်ကျနေပါက
                        if last_action_time < time_limit_iso:
                            
                            # (က) user_logs table ထဲသို့ Browser ပိတ်သွားကြောင်း Row အသစ် (INSERT) သီးသန့်မှတ်ခြင်း
                            log_user_activity(
                                username=username,
                                action="Session Expired (Tab Closed / Inactive)",
                                status="Success",
                                session_id=session_id
                            )
                            
                            # (ခ) Users Table ထဲက ပိတ်မိနေသော Session ID အား NULL ချ၍ ကန်ထုတ်ခြင်း
                            supabase.table("users").update({"current_session_id": None}).eq("username", username).execute()
            
            # သန့်ရှင်းရေးလုပ်ပြီးကြောင်း အမှတ်အသားပြုခြင်း
            st.session_state["cleanup_done"] = True
        except Exception as e:
            print(f"Cleanup Error: {e}")
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
