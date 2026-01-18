import streamlit as st
import pandas as pd
from solver import SchoolScheduler  # 確保 solver.py 必須在同一個資料夾內

# --- 頁面基本設定 ---
st.set_page_config(
    page_title="智慧排課系統",
    page_icon="🏫",
    layout="wide"
)

st.title("🏫 國高中智慧排課系統 (完整版)")

# ==========================================
# 1. 核心邏輯：模擬資料產生器
# ==========================================
def get_simulation_data():
    """
    生成 10 個班級、10 位老師，以及指定的課程結構。
    使用輪替演算法自動分配老師，確保每位老師每週時數約為 26 堂。
    """
    # 定義 10 個班級 (101~110)
    classes = [f"{i}班" for i in range(101, 111)]
    
    # 定義 10 位老師 (A~J)
    teachers = [f"Teacher_{char}" for char in "ABCDEFGHIJ"]
    
    # 定義科目與每週節數 (總計 26 節)
    subjects_config = [
        ('國文', 4), ('英文', 4), ('數學', 4),
        ('理化', 3), ('自然', 3),
        ('公民', 2), ('地理', 2), ('歷史', 2),
        ('生活科技', 1), ('資訊科技', 1)
    ]
    
    data = []
    num_teachers = len(teachers)
    
    for class_idx, class_name in enumerate(classes):
        for subj_idx, (subj_name, hours) in enumerate(subjects_config):
            # 演算法：(班級ID + 科目ID) % 老師總數
            # 確保老師被均勻錯開，避免同一位老師在同一時段要教多個班
            teacher_idx = (class_idx + subj_idx) % num_teachers
            teacher_name = teachers[teacher_idx]
            
            data.append({
                'class': class_name,
                'teacher': teacher_name,
                'subject': subj_name,
                'hours': hours
            })
            
    return pd.DataFrame(data)

# ==========================================
# 2. 側邊欄設定
# ==========================================
with st.sidebar:
    st.header("⚙️ 參數設定")
    periods_per_day = st.slider("每天總節數", min_value=5, max_value=9, value=7, help="若課程總數為26節，建議至少設為7節以免空間不足")
    st.info("💡 模擬模式預設為：\n10 個班級 / 10 位老師\n每班每週 26 節課")

# ==========================================
# 3. 資料來源選擇
# ==========================================
st.subheader("1. 資料來源")
col1, col2 = st.columns([1, 1])

with col1:
    uploaded_file = st.file_uploader("上傳 CSV 需求表", type="csv")

with col2:
    use_simulation = st.checkbox("✅ 使用「10班10師」模擬資料", value=True)

# 決定使用哪份資料
df = None
if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.success(f"已讀取上傳檔案，共 {len(df)} 筆需求")
elif use_simulation:
    df = get_simulation_data()
    st.info(f"已生成模擬資料，共 {len(df)} 筆需求 (10班 x 10科)")

# ==========================================
# 4. 排課執行區
# ==========================================
if df is not None:
    with st.expander("查看原始開課需求清單 (Raw Data)"):
        st.dataframe(df)

    st.markdown("---")
    st.subheader("2. 執行排課")
    
    if st.button("🚀 開始運算 (Run Solver)", type="primary"):
        with st.spinner('AI 正在進行矩陣運算，請稍候...'):
            # 準備資料
            courses_data = df.to_dict('records')
            
            # 初始化 Solver (傳入每天節數設定)
            scheduler = SchoolScheduler(courses_data, periods=periods_per_day) 
            
            # 開始計算
            result_df = scheduler.solve()
            
            # --- 處理運算結果 ---
            if result_df is not None:
                st.session_state['result_df'] = result_df # 存入 Session State 防止重整後消失
                st.balloons()
                st.success("✅ 排課成功！已找到最佳解。")
            else:
                st.error("❌ 無解 (Infeasible)。請檢查是否老師時數過度集中或總節數不足。")

# ==========================================
# 5. 結果顯示與查詢 (讀取 Session State)
# ==========================================
if 'result_df' in st.session_state:
    result_df = st.session_state['result_df']
    
    # 下載區
    st.markdown("### 📥 下載結果")
    csv = result_df.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label="下載完整課表 (CSV)",
        data=csv,
        file_name='final_schedule.csv',
        mime='text/csv'
    )
    
    st.markdown("---")
    
    # --- 查詢功能 (Pivot View) ---
    st.subheader("🔍 課表查詢 (週課表檢視)")
    
    q_col1, q_col2 = st.columns([1, 3])
    
    with q_col1:
        query_type = st.radio("查詢模式", ["依班級查課表", "依老師查課表"])
    
    with q_col2:
        target = None
        if query_type == "依班級查課表":
            class_list = sorted(result_df['班級'].unique())
            target = st.selectbox("請選擇班級", class_list)
            filtered_df = result_df[result_df['班級'] == target]
        else:
            teacher_list = sorted(result_df['老師'].unique())
            target = st.selectbox("請選擇老師", teacher_list)
            filtered_df = result_df[result_df['老師'] == target]

    # 顯示週課表
    if target:
        st.write(f"### 📋 {target} 的課表")
        
        # 製作 Pivot Table (列=節次, 欄=星期)
        pivot_df = filtered_df.pivot(index='節次', columns='星期', values='科目')
        
        # 定義排序邏輯 (確保週一排在週二前面，而不是按筆劃)
        days_order = ['週一', '週二', '週三', '週四', '週五']
        periods_order = [f'第 {i} 節' for i in range(1, periods_per_day + 1)]
        
        # 重新索引 (Reindex) 以確保顯示順序正確，並填補空值
        # 這裡用 set 交集防止模擬資料天數跟設定不一致報錯
        valid_days = [d for d in days_order if d in result_df['星期'].unique()]
        valid_periods = [p for p in periods_order if p in result_df['節次'].unique()]
        
        pivot_df = pivot_df.reindex(index=valid_periods, columns=valid_days)
        
        # 顯示表格 (使用 st.dataframe 可以互動，st.table 比較像靜態報表)
        st.table(pivot_df.fillna("")) # 空堂顯示空白