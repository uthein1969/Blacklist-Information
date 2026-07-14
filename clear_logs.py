import os
from supabase import create_client

# 🎯 မူရင်း Supabase Credentials များ
# --- Supabase Configuration ---
SUPABASE_URL = "https://batsowuihgwhxbboucpy.supabase.co"
SUPABASE_KEY = "sb_publishable_OBTOI4EioNVufb5akpDOwA_75EmAcWr"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def clear_all_user_logs():
    try:
        print("⏳ Clean Data from Supabase user_logs")
        # .neq("id", 0) ဟု သတ်မှတ်ခြင်းဖြင့် ID 0 မဟုတ်သော row အားလုံး (အားလုံး) ကို ဖျက်ခိုင်းခြင်းဖြစ်ပါသည်
        response = supabase.table("user_logs").delete().neq("id", 0).execute()
        print("✨ Supabase user_logs Clean Successfully")
    except Exception as e:
        print(f"❌ ဖျက်ဆီးမှု မအောင်မြင်ပါ: {str(e)}")

if __name__ == "__main__":
    clear_all_user_logs()