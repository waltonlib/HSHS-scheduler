import streamlit as st
import pandas as pd
from solver import SchoolScheduler # 匯入剛剛的 solver

st.title("國高中智慧排課系統")

# 1. 下載範例 CSV 讓使用者參考
# (這裡可以放一個下載按鈕)

# 2. 上傳檔案
uploaded_file = st.file_uploader("上傳開課需求 (CSV)", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.dataframe(df.head()) # 預覽資料

    if st.button("開始自動排課"):
        # 轉換 dataframe 為 solver 吃的 list of dict 格式
        courses_data = df.to_dict('records')
        
        # 呼叫核心
        scheduler = SchoolScheduler(courses_data)
        result_df = scheduler.solve()
        
        if result_df is not None:
            st.success("排課成功！")
            st.dataframe(result_df)
            # 下載結果按鈕
            csv = result_df.to_csv(index=False).encode('utf-8-sig')
            st.download_button("下載課表 CSV", csv, "schedule_result.csv")
        else:
            st.error("無解，請放寬限制條件。")