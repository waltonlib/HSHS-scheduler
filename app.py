import streamlit as st
import pandas as pd
from solver import SchoolScheduler

st.set_page_config(page_title="智慧排課系統", layout="wide")
st.title("🏫 國高中智慧排課系統 (模擬測試版)")

# --- 核心：模擬資料產生器 ---
def get_simulation_data():
    """
    生成 10 個班級、10 位老師，以及指定的課程結構。
    使用輪替演算法自動分配老師，確保每位老師每週時數約為 26 堂 (符合需求總和)。
    """
    # 1. 定義 10 個班級
    classes = [f"{i}班" for i in range(101, 111)] # 101班 ~ 110班
    
    # 2. 定義 10 位老師
    teachers = [f"Teacher_{char}" for char in "ABCDEFGHIJ"] # Teacher_A ~ Teacher_J
    
    # 3. 定義科目與每週節數 (總計 26 節)
    subjects_config = [
        ('國文', 4), ('英文', 4), ('數學', 4),
        ('理化', 3), ('自然', 3),
        ('公民', 2), ('地理', 2), ('歷史', 2),
        ('生活科技', 1), ('資訊科技', 1)
    ]
    
    data = []
    
    # 4. 自動生成課程並分配老師
    # 我們使用 (班級索引 + 科目索引) % 老師數量 的演算法
    # 這樣可以確保老師被均勻錯開，不會發生 Teacher_A 同時要教 10 個班的國文
    num_teachers = len(teachers)
    
    for class_idx, class_name in enumerate(classes):
        for subj_idx, (subj_name, hours) in enumerate(subjects_config):
            
            # 輪替分配老師
            teacher_idx = (class_idx + subj_idx) % num_teachers
            teacher_name = teachers[teacher_idx]
            
            data.append({
                'class': class_name,
                'teacher': teacher_name,
                'subject': subj_name,
                'hours': hours
            })
            
    return pd.DataFrame(data)

# --- 側邊欄 ---
with st.sidebar:
    st.header("⚙️ 設定")
    st.info("目前模擬模式：\n10 個班級 / 10 位老師\n每班每週 26 節課")

# --- 主畫面邏輯 ---
st.subheader("1. 資料來源")
col1, col2 = st.columns([1, 1])

with col1:
    uploaded_file = st.file_uploader("上傳 CSV (若無則使用右側模擬)", type="csv")

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

# --- 排課執行區 ---
if df is not None:
    with st.expander("查看詳細開課需求 (Raw Data)"):
        st.dataframe(df)

    st.markdown("---")
    st.subheader("2. 執行排課")
    
    # 讓使用者可以調整每天節數，因為 26 堂課如果只排 5 節/天 (25節) 會排不下
    periods_per_day = st.slider("每天排幾節課？", min_value=5, max_value=8, value=7)
    
    if st.button("🚀 開始運算 (Solver)"):
        with st.spinner('正在進行矩陣運算，這可能需要幾秒鐘...'):
            # 轉換資料格式
            courses_data = df.to_dict('records')
            
            # 呼叫核心演算法
            # 注意：這裡 days=5 是預設值，若您要排六天需修改 solver
            scheduler = SchoolScheduler(courses_data, periods=periods_per_day) 
            result_df = scheduler.solve()
            
            if result_df is not None:
                st.balloons()
                st.success("✅ 排課成功！找到最佳解。")
                
                # 顯示結果
                st.subheader("📅 排課結果")
                st.dataframe(result_df, use_container_width=True)
                
                # 下載按鈕
                csv = result_df.to_csv(index=False).encode('utf-8-sig')
                st.download_button(
                    label="📥 下載完整課表 (CSV)",
                    data=csv,
                    file_name='simulated_schedule_10x10.csv',
                    mime='text/csv'
                )
            else:
                st.error("❌ 無解 (Infeasible)。\n\n原因可能是：\n1. 總節數超過一週可用時間 (例如每週26節，但每天只開5節)。\n2. 老師時數過度集中導致衝突。")

else:
    st.warning("請先上傳檔案或勾選模擬資料。")