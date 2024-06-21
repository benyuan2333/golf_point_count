import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# 设置页面配置
st.set_page_config(
    page_title="高尔夫球场轨迹点数据分析",
    page_icon=":wave:",
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
        st.subheader(f'球场: {selected_course}')
        
        # 筛选出该球场的数据
        course_data = df[df['球场名称'] == selected_course].copy()
        
        # 绘制每个球洞的轨迹点数量
        for hole in range(1, 19):
            hole_col = str(hole)
            
            # 提取每个球洞的问题备注并统计点数
            if hole_col in course_data.columns:
                course_data.loc[:, hole_col + '_count'] = course_data[hole_col].apply(
                    lambda x: {y.split(': ')[0]: int(y.split(': ')[1].split('个')[0]) for y in x.split('; ') if y} if isinstance(x, str) else {})
                
                # 显示超过100个轨迹点的元素
                hole_problems = course_data[hole_col + '_count'].iloc[0]
                if hole_problems:
                    st.write(f'球洞 {hole} 超出轨迹点要求的元素:')
                    for element, count in hole_problems.items():
                        if count > 100:
                            st.write(f'{element}: {count}个轨迹点')
                else:
                    st.write(f'球洞 {hole} 没有超过轨迹点要求的元素')
else:
    st.warning("请上传一个Excel文件")
