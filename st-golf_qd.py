import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
from folium.plugins import MarkerCluster

st.set_page_config(layout="wide")

# 上传表格
uploaded_file = st.file_uploader("上传表格", type=["csv", "json"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)

    course_names = df['文件名称'].str.replace('.json', '', regex=False).unique()

    if 'selected_course_index' not in st.session_state:
        st.session_state['selected_course_index'] = 1

    if 'selected_course' not in st.session_state:
        st.session_state['selected_course'] = course_names[0]

    def update_course_index():
        st.session_state['selected_course_index'] = course_names.tolist().index(st.session_state['selected_course']) + 1

    def update_course_name():
        st.session_state['selected_course'] = course_names[st.session_state['selected_course_index'] - 1]

    col1, col2 = st.columns(2)

    with col1:
        st.selectbox(
            "选择球场",
            course_names,
            key='selected_course',
            on_change=update_course_index
        )

    with col2:
        st.number_input(
            "球场序号",
            min_value=1,
            max_value=len(course_names),
            step=1,
            key='selected_course_index',
            on_change=update_course_name
        )

    final_selected_course = st.session_state['selected_course']

    course_data = df[df['文件名称'].str.replace('.json', '', regex=False) == final_selected_course]

    center_coords = course_data.iloc[0]['中心经纬度'].split(',')
    center_lat = float(center_coords[1])
    center_lon = float(center_coords[0])

    m = folium.Map(location=[center_lat, center_lon], zoom_start=15, tiles=None)
    folium.TileLayer(
        tiles='http://{s}.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
        attr='Google',
        name='Google Satellite',
        max_zoom=20,
        subdomains=['mt0', 'mt1', 'mt2', 'mt3']
    ).add_to(m)

    marker_cluster = MarkerCluster().add_to(m)

    # 显示佳明球洞点
    for i, row in course_data.iterrows():
        actual_coords = list(map(float, row['佳明经纬度'].split(',')))
        folium.Marker(
            location=[actual_coords[1], actual_coords[0]],
            popup=f"球洞: {row['顺序出错球洞']}<br>类型: 佳明<br>距离: {row['距离(米)']} 米",
            icon=folium.DivIcon(html=f"""<div style="display: flex;justify-content: center;align-items: center;font-family: Arial;color: white;background-color: green;border-radius: 50%;width: 25px;height: 25px;font-size: 12px;font-weight: bold;">{row['顺序出错球洞']}</div>""")
        ).add_to(marker_cluster)

    # 显示实际球洞点
    for i, row in course_data.iterrows():
        error_coords = list(map(float, row['实际经纬度'].split(',')))
        folium.Marker(
            location=[error_coords[1], error_coords[0]],
            popup=f"球洞: {row['顺序出错球洞']}<br>类型: 实际<br>距离: {row['距离(米)']} 米",
            icon=folium.DivIcon(html=f"""<div style="display: flex;justify-content: center;align-items: center;font-family: Arial;color: white;background-color: red;border-radius: 50%;width: 25px; height: 25px;font-size: 12px;font-weight: bold;">{row['顺序出错球洞']}</div>""")
        ).add_to(marker_cluster)

    folium_static(m, width=1380, height=850)
