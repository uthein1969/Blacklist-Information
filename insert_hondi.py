import pandas as pd
from supabase import create_client, Client
from rich import print

# 🔑 ၁။ Supabase Configuration
SUPABASE_URL = "https://batsowuihgwhxbboucpy.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJhdHNvd3VpaGd3aHhiYm91Y3B5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzc5ODE5NjEsImV4cCI6MjA5MzU1Nzk2MX0.d5xED3dXBSRePfPi8IXjFk5YiVWGpg1AusVzTS21as8"

print("⏳ Supabase Database နှင့် ချိတ်ဆက်နေပါသည်...")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

try:
    # 🔍 ၂။ Supabase ထဲတွင် ရှိပြီးသား ဒေတာဟောင်းများကို လှမ်းဖတ်ခြင်း
    print("🔍 Supabase ရှိ ဒေတာဟောင်းများနှင့် တိုက်စစ်ရန် ဖတ်ရှုနေပါသည်...")
    existing_data = supabase.table("blacklist_records").select("full_name, nrc_number").execute()
    
    # ရှိပြီးသား (နာမည် + NRC) အတွဲများကို မှတ်သားထားခြင်း
    existing_set = set()
    if existing_data.data:
        for row in existing_data.data:
            # စာလုံးအကြီးအသေးနှင့် Space ကြောင့် လွဲချော်မှုမရှိစေရန် clean လုပ်၍ သိမ်းဆည်းခြင်း
            name_clean = str(row.get('full_name', '')).strip().lower()
            nrc_clean = str(row.get('nrc_number', '')).strip().lower()
            existing_set.add((name_clean, nrc_clean))

    # 📁 ၃။ CSV ဖိုင်ကို ဖတ်ရှုခြင်း
    csv_file_path = "HonDi Black List.csv"
    print(f"📖 CSV ဖိုင်အား ဖတ်ရှုနေပါသည်: {csv_file_path}")
    df = pd.read_csv(csv_file_path)
    csv_records = df[['full_name', 'nrc_number', 'reason']].to_dict(orient='records')
    
    # 🎯 ၄။ နာမည်ရော NRC ပါ တူနေတာတွေ့ရင် ဖယ်ထုတ်ပြီး အသစ်များကိုသာ စစ်ထုတ်ယူခြင်း
    records_to_insert = []
    duplicate_count = 0
    
    for record in csv_records:
        csv_name = str(record['full_name']).strip().lower()
        csv_nrc = str(record['nrc_number']).strip().lower()
        
        # နာမည်နှင့် NRC နှစ်ခုလုံး တူနေပါက ထပ်နေသည်ဟု သတ်မှတ်မည်
        if (csv_name, csv_nrc) in existing_set:
            duplicate_count += 1
        else:
            records_to_insert.append(record)
            
    print(f"📋 CSV ထဲရှိ ဒေတာစုစုပေါင်း: {len(csv_records)} ကြောင်း")
    print(f"⚠️ ရှိပြီးသားဖြစ်၍ ချန်ထားခဲ့မည့် (ထပ်နေသော) ဒေတာ: {duplicate_count} ကြောင်း")
    print(f"✨ အသစ်စက်စက် ထည့်သွင်းမည့် ဒေတာ: {len(records_to_insert)} ကြောင်း")
    
    # 🚀 ၅။ အသစ်များရှိမှသာ Supabase ထဲသို့ Bulk Insert လုပ်ခြင်း
    if records_to_insert:
        print("📤 Supabase သို့ ဒေတာအသစ်များ အစုလိုက် (Bulk Insert) ပေးပို့နေပါသည်...")
        response = supabase.table("blacklist_records").insert(records_to_insert).execute()
        print(f"🎉 အောင်မြင်ပါပြီဗျာ! ဒေတာအသစ် {len(records_to_insert)} ကြောင်းကို ထည့်သွင်းပြီးပါပြီ။")
    else:
        print("✅ ထည့်သွင်းရန် ဒေတာအသစ်မရှိပါ။ ဒေတာအားလုံးသည် Database ထဲတွင် ရှိပြီးသားဖြစ်ပါသည်ဗျာ။")

except Exception as e:
    print(f"❌ အမှားအယွင်း ဖြစ်ပွားခဲ့ပါသည်: {str(e)}")