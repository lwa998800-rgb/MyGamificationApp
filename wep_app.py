import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
import matplotlib.pyplot as plt

st.set_page_config(page_title="Gamified Life - Apple Edition v14.5", page_icon="🎮", layout="wide")

DATA_FILE = "my_habits_data.csv"
DAILY_STATS_FILE = "my_daily_stats.csv"
CONFIG_FILE = "my_config_v4.json"

default_config = {
    "wallet": 0, "xp": 0, "vault_cash": 0.0, 
    "budget_amount": 0.0, "budget_days": 7, "daily_limit": 0.0, "spent_today": 0.0,
    "points_today": 0, "goals": [],
    "last_login": datetime.now().strftime("%Y-%m-%d"), 
    "buttons": [
        {"name": "مذاكرة Data Science", "type": "task", "points": 10, "cash": 0.0, "req_xp": 0, "linked_goal": ""},
        {"name": "تحضير V60", "type": "reward", "points": 10, "cash": 0.0, "req_xp": 0, "linked_goal": ""},
        {"name": "عشاء مطعم 🍔", "type": "premium", "points": 0, "cash": 30.0, "req_xp": 1000, "linked_goal": ""}
    ]
}

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                cfg = json.load(f)
            for k, v in default_config.items():
                if k not in cfg: cfg[k] = v
            return cfg
        except:
            return default_config
    return default_config

if 'config' not in st.session_state:
    st.session_state['config'] = load_config()

config = st.session_state['config']

def save_config():
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=4)

def get_level_info():
    level = (config["xp"] // 1000) + 1
    xp_in_current_level = config["xp"] % 1000
    progress = xp_in_current_level / 1000.0
    return level, progress, xp_in_current_level

def record_daily_stat(daily_surplus=0.0):
    today_str = datetime.now().strftime("%Y-%m-%d")
    pts_today = config.get("points_today", 0)
    new_row = pd.DataFrame({'Date': [today_str], 'Daily_Surplus': [daily_surplus], 'Points_Today': [pts_today]})
    
    if not os.path.exists(DAILY_STATS_FILE) or os.stat(DAILY_STATS_FILE).st_size == 0:
        new_row.to_csv(DAILY_STATS_FILE, index=False)
    else:
        try:
            df = pd.read_csv(DAILY_STATS_FILE)
            if 'Points_Today' not in df.columns: df['Points_Today'] = 0
            if today_str in df['Date'].values:
                df.loc[df['Date'] == today_str, 'Daily_Surplus'] = daily_surplus
                df.loc[df['Date'] == today_str, 'Points_Today'] = pts_today
                df.to_csv(DAILY_STATS_FILE, index=False)
            else:
                new_row.to_csv(DAILY_STATS_FILE, mode='a', header=False, index=False)
        except:
            new_row.to_csv(DAILY_STATS_FILE, index=False)

today_date = datetime.now().date()
try:
    last_date = datetime.strptime(config["last_login"], "%Y-%m-%d").date()
except:
    last_date = today_date
days_passed = (today_date - last_date).days

if days_passed > 0:
    current_surplus = max(0, config["daily_limit"] - config["spent_today"])
    config["vault_cash"] += current_surplus
    if days_passed > 1:
        config["vault_cash"] += (config["daily_limit"] * (days_passed - 1))
    config["spent_today"] = 0.0
    config["points_today"] = 0
    config["wallet"] = 0 
    config["last_login"] = today_date.strftime("%Y-%m-%d")
    save_config()

def log_action(name, points_change, cash_change):
    config["wallet"] += points_change
    if points_change > 0: 
        config["xp"] += points_change
        config["points_today"] += points_change
    config["vault_cash"] += cash_change 
    save_config()
    
    surplus_val = max(0, config["daily_limit"] - config["spent_today"])
    record_daily_stat(surplus_val)
    
    new_row = pd.DataFrame({
        'Date': [datetime.now().strftime("%Y-%m-%d %H:%M:%S")], 
        'Action': [name], 'Points_Change': [points_change], 'Cash_Change': [cash_change], 
        'Wallet': [config["wallet"]], 'Vault': [config["vault_cash"]]
    })
    
    if not os.path.exists(DATA_FILE) or os.stat(DATA_FILE).st_size == 0:
        new_row.to_csv(DATA_FILE, index=False)
    else:
        try:
            new_row.to_csv(DATA_FILE, mode='a', header=False, index=False)
        except:
            new_row.to_csv(DATA_FILE, index=False)

st.title("Gamified Life - Apple Edition v14.5 🎮")
level, progress, xp_current = get_level_info()
rem_today = max(0, config['daily_limit'] - config['spent_today'])

c1, c2, c3, c4 = st.columns(4)
c1.metric("المستوى 🌟", f"Lvl {level}")
c2.metric("كوينز اليوم 🪙", config["wallet"])
c3.metric("الخزنة 💵", f"{config['vault_cash']:.1f} ريال")
c4.metric("ميزانية اليوم", f"{rem_today:.1f} ريال")

st.progress(progress, text=f"XP: {config['xp']} (متبقي {1000 - xp_current} للفل القادم)")
st.divider()

t_tasks, t_store, t_vip, t_goals, t_history, t_stats, t_settings, t_add = st.tabs([
    "✅ المهام", "🛒 المتجر", "💎 VIP", "🎯 الأهداف", "📋 السجل", "📊 التحليلات", "⚙️ الإعدادات", "➕ إضافة جديد"
])

with t_tasks:
    st.subheader("المهام اليومية")
    for idx, btn in enumerate([b for b in config["buttons"] if b["type"] == "task"]):
        col_text, col_btn, col_del = st.columns([4, 1, 1])
        linked = f" [🎯 {btn['linked_goal']}]" if btn.get('linked_goal') else ""
        col_text.write(f"**{btn['name']}** | +{btn['points']} 🪙{linked}")
        if col_btn.button("إنجاز", key=f"t_exec_{idx}", type="primary"):
            log_action(btn["name"], btn["points"], 0.0)
            linked_goal = btn.get("linked_goal", "")
            if linked_goal:
                for goal in config["goals"]:
                    if goal["name"] == linked_goal:
                        goal["current"] += btn["points"]
                        break
                save_config()
            st.toast(f"أسطورة! كسبت {btn['points']} كوينز", icon="💪")
            st.rerun()
        if col_del.button("🗑️ حذف", key=f"t_del_{idx}"):
            config["buttons"] = [b for b in config["buttons"] if b["name"] != btn["name"]]
            save_config()
            st.rerun()

with t_store:
    st.subheader("متجر المكافآت اليومية")
    cols = st.columns(3)
    rewards = [b for b in config["buttons"] if b["type"] == "reward"]
    for idx, btn in enumerate(rewards):
        with cols[idx % 3]:
            with st.container(border=True):
                st.write(f"**{btn['name']}**")
                st.caption(f"🪙 {btn['points']} | 💵 {btn['cash']} ريال")
                if st.button("شراء الآن", key=f"r_buy_{idx}"):
                    if config["wallet"] >= btn["points"] and config["vault_cash"] >= btn["cash"]:
                        log_action(btn["name"], -btn["points"], -btn["cash"])
                        st.toast("تمت عملية الشراء!", icon="✅")
                        st.rerun()
                    else:
                        st.error("رصيدك لا يكفي!")
                if st.button("🗑️ حذف", key=f"r_del_{idx}"):
                    config["buttons"] = [b for b in config["buttons"] if b["name"] != btn["name"]]
                    save_config()
                    st.rerun()

with t_vip:
    st.subheader("متجر الـ VIP الفاخر")
    cols = st.columns(3)
    vips = [b for b in config["buttons"] if b["type"] == "premium"]
    for idx, btn in enumerate(vips):
        locked = config["xp"] < btn["req_xp"]
        with cols[idx % 3]:
            with st.container(border=True):
                icon = "🔒" if locked else "🔓"
                st.write(f"**{icon} {btn['name']}**")
                st.caption(f"💵 {btn['cash']} ريال | ✨ يتطلب {btn['req_xp']} XP")
                if st.button("شراء VIP", key=f"v_buy_{idx}", disabled=locked):
                    if config["vault_cash"] >= btn["cash"]:
                        log_action(btn["name"], 0, -btn["cash"])
                        st.toast("عملية VIP ناجحة!", icon="🎉")
                        st.rerun()
                    else:
                        st.error("الكاش بالخزنة لا يكفي!")
                if st.button("🗑️ حذف", key=f"v_del_{idx}"):
                    config["buttons"] = [b for b in config["buttons"] if b["name"] != btn["name"]]
                    save_config()
                    st.rerun()

with t_goals:
    st.subheader("الأهداف الكبرى وتتبعها")
    for idx, goal in enumerate(config.get("goals", [])):
        with st.container(border=True):
            st.write(f"**{goal['name']}**")
            p_val = min(1.0, goal["current"] / goal["target"])
            st.progress(p_val, text=f"{goal['current']} / {goal['target']} XP")
            c_add, c_del = st.columns([1, 1])
            add_amt = c_add.number_input(f"إضافة إنجاز لـ {goal['name']}", min_value=1, step=10, key=f"g_add_{idx}")
            if c_add.button("تأكيد الإضافة", key=f"g_btn_{idx}"):
                goal["current"] += add_amt
                save_config()
                st.success("تمت الإضافة!")
                st.rerun()
            if c_del.button("🗑️ حذف الهدف", key=f"g_del_{idx}"):
                config["goals"].pop(idx)
                save_config()
                st.rerun()
    
    st.divider()
    st.write("### إضافة هدف جديد")
    new_g_name = st.text_input("اسم الهدف الجديد")
    new_g_target = st.number_input("الهدف المطلوب (XP)", min_value=100, step=500)
    if st.button("إنشاء الهدف"):
        if new_g_name:
            config["goals"].append({"name": new_g_name, "current": 0, "target": new_g_target})
            save_config()
            st.success("تم إضافة الهدف!")
            st.rerun()

with t_history:
    st.subheader("سجل العمليات والتحكم")
    if os.path.exists(DATA_FILE) and os.stat(DATA_FILE).st_size > 0:
        try:
            df_hist = pd.read_csv(DATA_FILE)
            for i, row in df_hist.iterrows():
                col_h1, col_h2 = st.columns([5, 1])
                info_txt = f"{row.get('Date', '')} | {row.get('Action', '')} | كوينز: {row.get('Points_Change', 0)} | كاش: {row.get('Cash_Change', 0)}"
                col_h1.write(info_txt)
                if col_h2.button("🗑️ حذف", key=f"hist_del_{i}"):
                    p_c = row.get('Points_Change', 0)
                    c_c = row.get('Cash_Change', 0)
                    config["wallet"] = max(0, config["wallet"] - int(p_c))
                    if int(p_c) > 0:
                        config["xp"] = max(0, config["xp"] - int(p_c))
                        config["points_today"] = max(0, config["points_today"] - int(p_c))
                    config["vault_cash"] -= float(c_c)
                    save_config()
                    df_hist = df_hist.drop(i).reset_index(drop=True)
                    df_hist.to_csv(DATA_FILE, index=False)
                    st.success("تم حذف العملية واستعادة القيم!")
                    st.rerun()
        except:
            st.write("السجل فارغ أو تالف.")
    else:
        st.write("لا توجد عمليات مسجلة حتى الآن.")

with t_stats:
    st.subheader("تحليلات الأداء بمرور الأيام")
    if os.path.exists(DAILY_STATS_FILE) and os.stat(DAILY_STATS_FILE).st_size > 0:
        try:
            df_stats = pd.read_csv(DAILY_STATS_FILE)
            if not df_stats.empty:
                fig, ax = plt.subplots(figsize=(8, 4), facecolor='#1c1c1e')
                ax.set_facecolor('#000000')
                surplus_col = 'Daily_Surplus' if 'Daily_Surplus' in df_stats.columns else 'Vault'
                ax.plot(df_stats['Date'], df_stats[surplus_col], marker='s', color='#32d74b', linewidth=2.5, label='الفائض المترحّل (ريال)')
                ax.set_title("متابعة التوفير اليومي", color='white')
                ax.tick_params(colors='white')
                ax.legend(facecolor='#1c1c1e', labelcolor='white')
                ax.grid(True, color='#2c2c2e')
                st.pyplot(fig)

                fig2, ax2 = plt.subplots(figsize=(8, 4), facecolor='#1c1c1e')
                ax2.set_facecolor('#000000')
                pts_col = 'Points_Today' if 'Points_Today' in df_stats.columns else 'Wallet'
                ax2.plot(df_stats['Date'], df_stats[pts_col], marker='o', color='#ff9f0a', linewidth=2.5, label='الكوينز المكتسبة')
                ax2.set_title("معدل اكتساب الكوينز اليومي", color='white')
                ax2.tick_params(colors='white')
                ax2.legend(facecolor='#1c1c1e', labelcolor='white')
                ax2.grid(True, color='#2c2c2e')
                st.pyplot(fig2)
        except:
            st.write("بيانات التحليلات غير كافية حالياً.")
    else:
        st.write("لا توجد إحصائيات يومية مسجلة.")

with t_settings:
    st.subheader("إدارة الخزنة والميزانية")
    new_vault = st.number_input("تعيين رصيد الخزنة يدوياً", value=float(config.get("vault_cash", 0.0)))
    if st.button("تحديث الخزنة"):
        config["vault_cash"] = new_vault
        save_config()
        st.success("تم تحديث رصيد الخزنة!")
        st.rerun()

    st.divider()
    b_amt = st.number_input("المبلغ الإجمالي للميزانية", value=float(config.get("budget_amount", 0.0)))
    b_days = st.number_input("عدد الأيام", value=int(config.get("budget_days", 7)), min_value=1)
    if st.button("حفظ وتوزيع الميزانية"):
        config["budget_amount"] = b_amt
        config["budget_days"] = b_days
        config["daily_limit"] = b_amt / b_days
        save_config()
        st.success("تم توزيع الميزانية بنجاح!")
        st.rerun()

    st.divider()
    exp_val = st.number_input("خصم مصروف يومي", min_value=0.0, step=5.0)
    if st.button("خصم من ميزانية اليوم"):
        config["spent_today"] += exp_val
        save_config()
        record_daily_stat(max(0, config["daily_limit"] - config["spent_today"]))
        st.success("تم تسجيل المصروف!")
        st.rerun()

with t_add:
    st.subheader("إضافة عنصر جديد (مهمة / مكافأة / VIP)")
    b_type_sel = st.selectbox("نوع العنصر", ["مهمة (task)", "مكافأة يومية (reward)", "مكافأة كبرى (premium)"])
    type_mapped = "task" if "مهمة" in b_type_sel else ("reward" if "مكافأة يومية" in b_type_sel else "premium")
    
    add_name = st.text_input("اسم العنصر")
    add_pts = st.number_input("الكوينز 🪙", min_value=0, step=5)
    add_cash = st.number_input("الكاش 💵", min_value=0.0, step=5.0)
    add_req_xp = st.number_input("الـ XP المطلوب (خاص بالـ VIP)", min_value=0, step=100)
    
    goal_names_opt = ["بدون ربط"] + [g["name"] for g in config.get("goals", [])]
    sel_linked_goal = st.selectbox("الربط التلقائي بهدف (اختياري)", goal_names_opt)
    
    if st.button("حفظ وإضافة العنصر"):
        if add_name:
            linked_val = sel_linked_goal if sel_linked_goal != "بدون ربط" else ""
            config["buttons"].append({
                "name": add_name, "type": type_mapped,
                "points": int(add_pts), "cash": float(add_cash),
                "req_xp": int(add_req_xp), "linked_goal": linked_val
            })
            save_config()
            st.success("تمت الإضافة بنجاح! انتقل للتبويب الخاص به لرؤيته.")
            st.rerun()