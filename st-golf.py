import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="高尔夫球场轨迹点数据分析",
    page_icon=":golf:",
    layout="wide",
)

st.title('高尔夫球场轨迹点数据分析')

uploaded_file = st.file_uploader("上传Excel文件", type=["xlsx"])

if uploaded_file is not None:

    df = pd.read_excel(uploaded_file)

    st.subheader('原始数据')
    st.dataframe(df)
    filtered_data = []

    for index, row in df.iterrows():
        course_name = row['球场名称']

        for column in df.columns:
            if '球道边界' in column or '球场外轮廓' in column or '果岭' in column or '击球路线' in column:
                elements = str(row[column]).split('; ')
                
                for element in elements:
                    if ':' in element:
                        parts = element.split(': ')
                        feature_name = parts[0].strip()
                        
                        if feature_name in ['球道边界', '球场外轮廓', '果岭', '击球路线']:
                            try:
                                value = int(parts[1].strip())
                                if value > 1:
                                    filtered_data.append({
                                        '球场名称': course_name,
                                        '球洞': '',
                                        '要素名称': feature_name,
                                        '数值': value
                                    })
                            except ValueError:
                                continue

        for hole in range(1, 19):
            hole_col = str(hole)

            if hole_col in df.columns:
                elements = str(row[hole_col]).split('; ')
                
                for element in elements:
                    if ':' in element:
                        parts = element.split(': ')
                        feature_name = parts[0].strip()
                        
                        if feature_name in ['球道边界', '球场外轮廓', '果岭', '击球路线']:
                            try:
                                value = int(parts[1].strip())
                                if value > 1:
                                    filtered_data.append({
                                        '球场名称': course_name,
                                        '球洞': hole_col,
                                        '要素名称': feature_name,
                                        '数值': value
                                    })
                            except ValueError:
                                continue

    filtered_df = pd.DataFrame(filtered_data)

    total_elements = df.iloc[-1]['球场要素总数量']
    st.write(f"全部球场总要素数量为：{total_elements}")

    if not filtered_df.empty:
        st.subheader('球场要素超过阈值（忽略双果岭）')
        st.dataframe(filtered_df)
    else:
        st.write('暂未发现球场要素超过阈值')
