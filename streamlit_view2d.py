import streamlit as st
import json
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Polygon
from matplotlib import rcParams
import numpy as np

# 设置 Matplotlib 默认字体
rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans', 'Liberation Sans', 'sans-serif']
rcParams['axes.unicode_minus'] = False

# 初始化 Streamlit 页面
st.set_page_config(page_title="Hatch Viewer", layout="wide")
st.title("Hatch Viewer")

def generate_arc_points(center, radius, start_angle, end_angle, num_points=50):
    start_angle = start_angle % 360
    end_angle = end_angle % 360
    if end_angle < start_angle:
        end_angle += 360
    
    if radius < 1:
        num_points = max(num_points, 100)
    
    start_rad = np.radians(start_angle)
    end_rad = np.radians(end_angle)
    angles = np.linspace(start_rad, end_rad, num_points)
    
    x = center[0] + radius * np.cos(angles)
    y = center[1] + radius * np.sin(angles)
    
    return list(zip(x, y))

def process_hatch_loops(loops):
    all_loops = []
    for loop in loops:
        vertices = []
        for edge in loop:
            if edge["type"] == "edgeLineSeg2d":
                vertices.append(tuple(edge["start"]))
            elif edge["type"] == "edgeCircArc2d":
                arc_points = generate_arc_points(
                    edge["center"],
                    edge["radius"],
                    edge["startAngle"],
                    edge["endAngle"],
                    num_points=20
                )
                vertices.extend(arc_points)
        
        if vertices and vertices[0] != vertices[-1]:
            vertices.append(vertices[0])
        
        if len(vertices) >= 3:
            all_loops.append(vertices)
    return all_loops

def draw_hatch(ax, hatch_data):
    if "loops" in hatch_data:
        all_loops = process_hatch_loops(hatch_data["loops"])
        for vertices in all_loops:
            polygon = Polygon(
                vertices,
                closed=True,
                facecolor='none',
                edgecolor='red',
                hatch='///',
                alpha=0.5,
                linewidth=1
            )
            ax.add_patch(polygon)

# 上传 JSON 文件
uploaded_file = st.file_uploader("上传 JSON 文件", type=["json"])

if uploaded_file is not None:
    try:
        # 读取 JSON 数据
        data = json.load(uploaded_file)
        
        # 创建图形
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # 如果是单个 hatch 对象
        if isinstance(data, dict) and "loops" in data:
            draw_hatch(ax, data)
        # 如果是 hatch 对象列表
        elif isinstance(data, list):
            for hatch in data:
                if isinstance(hatch, dict) and "loops" in hatch:
                    draw_hatch(ax, hatch)
        
        ax.set_aspect('equal', adjustable='datalim')
        ax.grid(True, linestyle='--', alpha=0.5)
        ax.set_title("Hatch 视图")
        
        # 显示图形
        st.pyplot(fig)
        
        # 导出功能
        if st.sidebar.button("导出数据"):
            st.sidebar.download_button(
                label="下载 JSON 文件",
                data=json.dumps(data, ensure_ascii=False, indent=4),
                file_name="hatch_data.json"
            )
            
    except Exception as e:
        st.error(f"处理数据时出错: {str(e)}")
