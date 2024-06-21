import os
import shutil
import zipfile
import pandas as pd
import streamlit as st
import shapefile
import matplotlib.pyplot as plt

def count_points_in_shapefile(shapefile_path):
    try:
        sf = shapefile.Reader(shapefile_path)
        point_count = sum(len(shape.points) for shape in sf.shapes())
        return point_count
    except shapefile.ShapefileException as e:
        st.error(f"处理文件 {shapefile_path} 时出现错误：{e}")
        return 0
    except Exception as e:
        st.error(f"处理文件 {shapefile_path} 时出现未知错误：{e}")
        return 0

def process_hole(hole_number, hole_folder_path, course_data, point_threshold):
    for file_name in os.listdir(hole_folder_path):
        if file_name.endswith(".shp"):
            shapefile_path = os.path.join(hole_folder_path, file_name)
            point_count = count_points_in_shapefile(shapefile_path)
            feature_name = os.path.splitext(file_name)[0]
            if point_count > point_threshold:
                course_data[f"{hole_number}"] += f"{feature_name}: {point_count}; "

def process_court_file(course_path, course_data, point_threshold):
    court_shapefile_path = os.path.join(course_path, "court.shp")
    if os.path.exists(court_shapefile_path):
        point_count = count_points_in_shapefile(court_shapefile_path)
        if point_count > point_threshold:
            course_data["court"] += f"court: {point_count}"

def process_golf_course(course_path, course_name, point_threshold, progress_bar, progress_text, course_index, total_courses):
    course_data = {
        "球场名称": course_name,
        "court": "",
        "1": "",
        "2": "",
        "3": "",
        "4": "",
        "5": "",
        "6": "",
        "7": "",
        "8": "",
        "9": "",
        "10": "",
        "11": "",
        "12": "",
        "13": "",
        "14": "",
        "15": "",
        "16": "",
        "17": "",
        "18": "",
    }

    process_court_file(course_path, course_data, point_threshold)

    for hole_number in range(1, 19):
        hole_folder_name = str(hole_number)
        hole_folder_path = os.path.join(course_path, hole_folder_name)
        if os.path.isdir(hole_folder_path):
            process_hole(hole_number, hole_folder_path, course_data, point_threshold)

    progress = (course_index + 1) / total_courses
    progress_bar.progress(progress)
    progress_text.text(f"Processing course {course_index + 1}/{total_courses}")

    return course_data

def process_multiple_courses(input_directory, point_threshold):
    courses_data = []
    course_dirs = [name for name in os.listdir(input_directory) if os.path.isdir(os.path.join(input_directory, name))]
    total_courses = len(course_dirs)

    progress_bar = st.progress(0)
    progress_text = st.empty()

    for i, course_name in enumerate(course_dirs):
        course_path = os.path.join(input_directory, course_name)
        course_data = process_golf_course(course_path, course_name, point_threshold, progress_bar, progress_text, i, total_courses)
        courses_data.append(course_data)

    progress_text.text("Processing complete!")
    return pd.DataFrame(courses_data)

def save_uploaded_file(uploaded_file):
    with open(uploaded_file.name, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return uploaded_file.name

def clear_temp_directory(path):
    try:
        if os.path.exists(path):
            shutil.rmtree(path)
    except Exception as e:
        st.error(f"清理临时文件夹时出现错误：{e}")

def extract_zip_file(zip_file_path, extract_to):
    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
        total_files = len(zip_ref.infolist())
        progress_bar = st.progress(0)
        progress_text = st.empty()

        for i, file in enumerate(zip_ref.infolist()):
            file.filename = file.filename.encode('utf-8').decode('utf-8')
            zip_ref.extract(file, extract_to)
            progress_bar.progress((i + 1) / total_files)
            progress_text.text(f"Extracting file {i + 1}/{total_files}")

def generate_excel(df):
    output_path = "golf_courses_data.xlsx"
    df.to_excel(output_path, index=False)
    return output_path

def plot_features(course_data, course_name):
    hole_numbers = [str(i) for i in range(1, 19)]
    feature_counts = {hole: [] for hole in hole_numbers}

    for hole in hole_numbers:
        features = course_data[hole].split("; ")
        for feature in features:
            if feature:
                feature_name, count = feature.split(": ")
                feature_counts[hole].append((feature_name, int(count)))

    plt.figure(figsize=(15, 10))
    for hole, features in feature_counts.items():
        if features:
            feature_names, counts = zip(*features)
            plt.bar([f"{hole}-{name}" for name in feature_names], counts)

    plt.xticks(rotation=90)
    plt.title(f"Feature Point Counts for {course_name}")
    plt.xlabel("Features")
    plt.ylabel("Point Count")
    st.pyplot(plt)

# Streamlit 部分
st.set_page_config(page_title="高尔夫球场轨迹点数据分析", page_icon=":golf:", layout="wide")

st.title('高尔夫球场轨迹点数据分析')

# 初始化 session state 中的 processed_data
if 'processed_data' not in st.session_state:
    st.session_state.processed_data = None

# 上传文件部分
uploaded_file = st.file_uploader("上传球场数据 ZIP 文件", type=["zip"], accept_multiple_files=False)
if uploaded_file:
    zip_file_path = save_uploaded_file(uploaded_file)

    clear_temp_directory("temp_unzipped")

    extract_zip_file(zip_file_path, "temp_unzipped")

    st.success("文件上传并解压成功！")

    point_threshold = st.number_input("输入轨迹点数量阈值", min_value=1, value=100)

    input_directory = "temp_unzipped"
    df = process_multiple_courses(input_directory, point_threshold)
    st.session_state.processed_data = df

if st.session_state.processed_data is not None:
    df = st.session_state.processed_data
    st.subheader('原始数据')
    st.dataframe(df)

    excel_file = generate_excel(df)
    with open(excel_file, "rb") as f:
        st.download_button("下载 Excel 文件", f, file_name="golf_courses_data.xlsx")

    course_names = df["球场名称"].tolist()
    selected_course = st.selectbox("选择球场", course_names)

    if selected_course:
        course_data = df[df["球场名称"] == selected_course].iloc[0]
        st.subheader(f"{selected_course} 超过阈值的元素列表")
        for hole in range(1, 19):
            if course_data[str(hole)]:
                st.markdown(f"**Hole {hole}:** {course_data[str(hole)]}")