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
    filtered_data = []

   # 遍历每个球场
    for course in df['球场名称'].unique():
        course_data = df[df['球场名称'] == course]
    
    # 检查 court 列
        if 'court' in course_data.columns:
            for _, row in course_data.iterrows():
                if isinstance(row['court'], str):
                    elements = row['court'].split('; ')
                    for element in elements:
                        if '[' in element:
                            filtered_data.append({
                                '球场名称': course,
                                '球洞': 'court',
                                '内容': element
                            })

        # 检查每个球洞的列
        for hole in range(1, 19):
            hole_col = str(hole)
            if hole_col in course_data.columns:
                for _, row in course_data.iterrows():
                    if isinstance(row[hole_col], str):
                        elements = row[hole_col].split('; ')
                        for element in elements:
                            if any(keyword in element for keyword in ['court', 'fairway', 'course', 'midline', 'green']) and '[' in element:
                                filtered_data.append({
                                    '球场名称': course,
                                    '球洞': hole_col,
                                    '内容': element
                                })

    # 将过滤后的结果转换为 DataFrame
    filtered_df = pd.DataFrame(filtered_data)

    # 显示过滤后的数据
    if not filtered_df.empty:
        st.subheader('包含 `[]` 的轨迹点数据 (court, fairway, course, midline, green)')
        st.dataframe(filtered_df)
    else:
        st.write('没有包含 `[]` 的轨迹点数据 (court, fairway, course, midline, green)')
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
