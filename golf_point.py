import streamlit as st
import pandas as pd

# 设置页面配置
st.set_page_config(
    page_title="高尔夫球场轨迹点数据分析",
    page_icon=":golf:",
    layout="wide",  
)

# 设置页面标题
st.title('高尔夫球场轨迹点数据分析')

# 文件上传器
uploaded_file = st.file_uploader("上传Excel文件", type=["xlsx"])

if uploaded_file is not None:
    # 读取上传的Excel文件
    df = pd.read_excel(uploaded_file)
    
    # 显示原始数据表格
    st.subheader('原始数据')
    st.dataframe(df)
    
    # 提取球场名称
    courses = df['球场名称'].unique()
    
    # 创建一个单选框用于选择单个球场
    selected_course = st.selectbox('选择球场', courses)
    
    if selected_course:
        course_data = df[df["球场名称"] == selected_course].iloc[0]
        st.subheader(f"{selected_course} 超过阈值的元素列表")
        for hole in range(1, 19):
            if course_data[str(hole)]:
                st.markdown(f"**Hole {hole}:** {course_data[str(hole)]}")
else:
    st.warning("请上传一个Excel文件")
