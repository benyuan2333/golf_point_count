import streamlit as st
import pandas as pd
import folium
import requests
from streamlit_folium import folium_static
from folium.plugins import MarkerCluster
import math

st.set_page_config(layout="wide")

# 上传表格
uploaded_file = st.file_uploader("上传表格", type=["csv"])

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
        max_zoom=30,
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

# 将半圆格式的经纬度转换为度数格式
def semi_circle_to_degrees(semi_circle_value):
    return semi_circle_value * (180 / (2**31))

# 计算两点之间的距离（米）
def calculate_distance(lat1, lon1, lat2, lon2):
    radius = 6371000  # 地球半径，单位：米
    
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    
    distance = radius * c
    return distance

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
def fetch_course_ids(course_name, course_name_en, longitude, latitude):
    longitude = longitude[:9]
    latitude = latitude[:9]
    url = f"https://omt.garmin.com/CourseViewData/Boundaries/{longitude},{latitude},32/Courses?courseName={course_name}&pageSize=10&page=1&filterDualGreen=false&filter3dOnly=false"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        try:
            data = response.json()
            matched_courses = [course for course in data.get('Courses', [])
                               if course.get('Name') == course_name or course.get('Name') == course_name_en]  # 完全匹配名称的球场

            if matched_courses:
                closest_course = None
                min_distance = float('inf')
                
                for course in matched_courses:
                    course_lat = semi_circle_to_degrees(course['Latitude'])
                    course_lon = semi_circle_to_degrees(course['Longitude'])
                    
                    distance = calculate_distance(float(center_lat), float(center_lon), course_lat, course_lon)
                    
                    if distance < min_distance:
                        min_distance = distance
                        closest_course = course

                # 返回最近的完全匹配球场
                st.success(f"Found closest matching course: {closest_course['Name']}, GlobalLayoutId: {closest_course['GlobalLayoutId']}, BuildId: {closest_course['BuildId']}")
                return closest_course['GlobalLayoutId'], closest_course['BuildId']
            else:
                st.error(f"未找到完全匹配的球场: {course_name} 或 {course_name_en}")
        except requests.JSONDecodeError as e:
            st.error(f"JSON Decode Error: {e}")
    else:
        st.error(f"Request failed with status code {response.status_code}")
    return None, None


# 获取并显示球场图片
def display_course_images():
    name = course_data.iloc[0]['球场名称']
    name_en = course_data.iloc[0]['球场英文名称']
    global_layout_id, build_id = fetch_course_ids(name, name_en, str(center_lon).replace(".", ""), str(center_lat).replace(".", ""))

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
