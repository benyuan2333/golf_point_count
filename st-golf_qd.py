import streamlit as st
import pandas as pd
import folium
import requests
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

headers = {
    'Accept': 'application/json; charset=utf-8',
    'Authorization': 'Basic ODAwM2UwZWZhMGFlNGM3NGE4N2MxYTZlMDQ1ZTdkNjU6TDNAZGVyYm9hcmRQcjBkIQ==',
}

# 获取球场详情函数
def fetch_course_details(global_layout_id, build_id):
    api_url = f"https://omt.garmin.com/CourseViewData/course-layouts/{global_layout_id}/releases/{build_id}?precision=24&languageCode=zh_CHS"
    response = requests.get(api_url, headers=headers)
    if response.status_code == 200:
        try:
            return response.json()
        except requests.JSONDecodeError as e:
            st.error(f"JSON Decode Error: {e}")
            return None
    else:
        st.error(f"Request failed with status code {response.status_code}")
        return None

# 根据经纬度获取球场的globalLayoutId和buildId
def fetch_course_ids(course_name, longitude, latitude):
    longitude = longitude[:9]
    latitude = latitude[:9]
    url = f"https://omt.garmin.com/CourseViewData/Boundaries/{longitude},{latitude},32/Courses?courseName={course_name}&pageSize=1&page=1&filterDualGreen=false&filter3dOnly=false"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        try:
            data = response.json()
            for course in data.get('Courses', []):
                st.success(f"Found course: {course_name}, GlobalLayoutId: {course['GlobalLayoutId']}, BuildId: {course['BuildId']}")
                return course['GlobalLayoutId'], course['BuildId']

        except requests.JSONDecodeError as e:
            st.error(f"JSON Decode Error: {e}")
    else:
        st.error(f"Request failed with status code {response.status_code}")
    return None, None

# 获取并显示球场图片
def display_course_images():
    name = course_data.iloc[0]['球场名称']
    global_layout_id, build_id = fetch_course_ids(name, str(center_lon).replace(".", ""), str(center_lat).replace(".", ""))
    if global_layout_id and build_id:
        course_details = fetch_course_details(global_layout_id, build_id)
        if course_details:
            image_urls = []
            hole_numbers = []
            for hole in course_details.get('Holes', []):
                image_url = hole.get('ImageUrlHighDef')
                hole_number = hole.get('Number')  
                if image_url and hole_number:
                    image_urls.append(image_url)
                    hole_numbers.append(hole_number)
            
            # 每行显示6个图片
            num_images_per_row = 6
            num_rows = (len(image_urls) + num_images_per_row - 1) // num_images_per_row 

            for row in range(num_rows):
                cols = st.columns(num_images_per_row)
                for col, image_url, hole_number in zip(cols, image_urls[row*num_images_per_row:(row+1)*num_images_per_row], hole_numbers[row*num_images_per_row:(row+1)*num_images_per_row]):
                    with col:
                        st.image(image_url, caption=f"Hole {hole_number}", width=300)

if st.button("获取并显示球场图片"):
    display_course_images()
