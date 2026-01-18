import streamlit as st
import pandas as pd
from io import BytesIO
from solver import SchoolScheduler

st.title("國高中智慧排課系統")

# --- 功能 1: 建立一個範例資料的 DataFrame ---
def get_example_data():
    return pd.DataFrame([
        {'class': '101', 'teacher': '王大明', 'subject': '國文', 'hours': 4},
        {'class': '101', 'teacher': '李英文', 'subject': '英文', 'hours': 4},
        {'class': '101', 'teacher': '陳數學', 'subject': '數學', 'hours': 4},
        {'class': '102', 'teacher': '王大明', 'subject': '國文', 'hours': 4},
        {'class': '102', 'teacher': '林物理', 'subject': '物理', 'hours': 3},
    ])

# --- 功能 2: 下載範例 CSV 按鈕 ---
example_df = get_example_data()
csv = example_df.to_csv(index=False).encode('utf-8-sig')

st.download_button(
    label="📥 下載 CSV 格式範本",
    data=csv,
    file_name='example_course_request.csv',
    mime='text/csv',
    help="請下載此範本，填入您的課程需求後再上傳"
)

st.markdown("---") # 分隔線

# --- 主功能: 選擇資料來源 ---
col1, col2 = st.columns([1, 1])

with col1:
    uploaded_file = st.file_uploader("上傳您的開課需求 (CSV)", type="csv")

with col2:
    use_demo = st.button("🧪 沒有檔案？使用測試資料試跑")

# --- 邏輯判斷 ---
df = None

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.info(f"已載入上傳檔案，共 {len(df)} 筆課程需求")
elif use_demo:
    df = get_example_data()
    st.info("已載入系統內建測試資料")

# --- 開始排課 ---
if df is not None:
    st.subheader("目前開課需求預覽")
    st.dataframe(df.head())

    if st.button("🚀 開始自動排課"):
        with st.spinner('AI 正在努力排課中，請稍候...'):
            # 轉換資料格式
            courses_data = df.to_dict('records')
            
            # 呼叫 Solver
            scheduler = SchoolScheduler(courses_data)
            result_df = scheduler.solve()
            
            if result_df is not None:
                st.success("✅ 排課成功！")
                st.dataframe(result_df)
                
                # 下載結果
                res_csv = result_df.to_csv(index=False).encode('utf-8-sig')
                st.download_button(
                    label="📥 下載排好的課表",
                    data=res_csv,
                    file_name='final_schedule.csv',
                    mime='text/csv'
                )
            else:
                st.error("❌ 無解！可能是限制太嚴格或課程太多衝堂。")
else:
    st.write("請上傳 CSV 檔案或點擊測試按鈕來開始。")