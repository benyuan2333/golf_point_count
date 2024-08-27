import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
from folium.plugins import MarkerCluster

# 设置Streamlit为wide布局
st.set_page_config(layout="wide")

# 上传表格
uploaded_file = st.file_uploader("上传表格", type=["csv", "json"])

if uploaded_file is not None:
    # 读取表格数据
    df = pd.read_csv(uploaded_file)

    # 获取球场名称列表
    course_names = df['文件名称'].str.replace('.json', '', regex=False).unique()

    # 如果不存在 session_state 则初始化
    if 'selected_course_index' not in st.session_state:
        st.session_state['selected_course_index'] = 1

    if 'selected_course' not in st.session_state:
        st.session_state['selected_course'] = course_names[0]

    def update_course_index():
        st.session_state['selected_course_index'] = course_names.tolist().index(st.session_state['selected_course']) + 1

    def update_course_name():
        st.session_state['selected_course'] = course_names[st.session_state['selected_course_index'] - 1]

    # 创建两列布局
    col1, col2 = st.columns(2)

    with col1:
        # 选择球场，设置on_change回调函数
        st.selectbox(
            "选择球场",
            course_names,
            index=st.session_state['selected_course_index'] - 1,
            key='selected_course',
            on_change=update_course_index
        )

    with col2:
        # 使用st.number_input切换球场，设置on_change回调函数
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

    # 提取中心点经纬度
    center_coords = course_data.iloc[0]['中心经纬度'].split(',')
    center_lat = float(center_coords[1])
    center_lon = float(center_coords[0])

    # 创建地图，并使用谷歌卫星图层
    m = folium.Map(location=[center_lat, center_lon], zoom_start=15, tiles=None)
    folium.TileLayer(
        tiles='http://{s}.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
        attr='Google',
        name='Google Satellite',
        max_zoom=20,
        subdomains=['mt0', 'mt1', 'mt2', 'mt3']
    ).add_to(m)

    # 创建MarkerCluster用于管理标记点
    marker_cluster = MarkerCluster().add_to(m)

# 显示佳明球洞点
for i, row in course_data.iterrows():
    actual_coords = list(map(float, row['佳明经纬度'].split(',')))
    folium.Marker(
        location=[actual_coords[1], actual_coords[0]],
        popup=f"佳明",
        icon=folium.DivIcon(html=f"""<div style="display: flex;justify-content: center;align-items: center;font-family: Arial;color: white;background-color: green;border-radius: 50%;width: 25px;height: 25px;font-size: 12px;font-weight: bold;">{row['顺序出错球洞']}</div>""")
    ).add_to(marker_cluster)

# 显示实际球洞点
for i, row in course_data.iterrows():
    error_coords = list(map(float, row['实际经纬度'].split(',')))
    folium.Marker(
        location=[error_coords[1], error_coords[0]],
        popup=f"实际",
        icon=folium.DivIcon(html=f"""<div style="display: flex;justify-content: center;align-items: center;font-family: Arial;color: white;background-color: red;border-radius: 50%;width: 25px; height: 25px;font-size: 12px;font-weight: bold;">{row['顺序出错球洞']}</div>""")
    ).add_to(marker_cluster)

    # 显示地图
    folium_static(m, width=1380, height=850)