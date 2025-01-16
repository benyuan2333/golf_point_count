import streamlit as st
import json
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Polygon, Arc, Ellipse
from matplotlib import rcParams
import numpy as np

# 设置 Matplotlib 默认字体
rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans', 'Liberation Sans', 'sans-serif']
rcParams['axes.unicode_minus'] = False

# 初始化 Streamlit 页面
st.set_page_config(page_title="2D CAD Viewer", layout="wide")
st.title("2D CAD Viewer")

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

def process_hatch_loops(hatch_entity):
    all_loops = []
    for loop in hatch_entity.get("loops", []):
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

def draw_hatch(ax, hatch_entity):
    all_loops = process_hatch_loops(hatch_entity)
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
        data = json.load(uploaded_file)
        views = data.get("views", [])
        
        if views:
            # 视图选择
            selected_view_idx = st.sidebar.selectbox(
                "选择视图",
                range(len(views)),
                format_func=lambda x: f"视图 {x + 1} - {views[x].get('viewType', '未知类型')}"
            )
            
            view = views[selected_view_idx]
            entities = view.get("entities", [])
            
            # 实体类型过滤
            entity_types = list(set(entity["type"] for entity in entities))
            selected_types = st.sidebar.multiselect(
                "选择实体类型",
                entity_types,
                default=entity_types
            )
            
            # 过滤实体
            filtered_entities = [
                entity for entity in entities
                if entity["type"] in selected_types
            ]
            
            # 创建图形
            fig, ax = plt.subplots(figsize=(12, 8))
            
            # 绘制实体
            for entity in filtered_entities:
                try:
                    if entity["type"] == "hatch":
                        draw_hatch(ax, entity)
                    elif entity["type"] == "circle":
                        center = entity["start"]
                        radius = entity.get("radius", 1)
                        circle = Circle(center, radius, edgecolor="red", fill=False, linewidth=1.5)
                        ax.add_patch(circle)
                except Exception:
                    continue

            # 提取并标注基准点信息
            datum_entities = [
                entity for entity in entities if entity["type"] == "mLeader" and 
                "DATUM_TARGET" in entity.get("userData", {}).get("businessInfo", [])
            ]
            for datum in datum_entities:
                leader_points = datum.get("leaderPoints", [])
                if leader_points:
                    start_position = leader_points[0]
                    text_content = datum.get("textOption", {}).get("textContent", "未知")
                    ax.scatter(start_position[0], start_position[1], color="red", label="基准点起点", zorder=6)
                    ax.text(start_position[0], start_position[1], f"{text_content}", color="red", fontsize=12, zorder=6)

            ax.set_aspect('equal', adjustable='datalim')
            ax.grid(True, linestyle='--', alpha=0.5)
            ax.set_title(f"视图 {selected_view_idx + 1} - {view.get('viewType', '未知类型')}")

            st.pyplot(fig)

            if st.sidebar.button("导出过滤后的实体为 JSON"):
                export_data = {"filtered_entities": filtered_entities}
                st.sidebar.download_button(
                    label="下载 JSON 文件",
                    data=json.dumps(export_data, ensure_ascii=False, indent=4),
                    file_name="filtered_entities.json"
                )
        else:
            st.error("未找到任何视图数据！")
    except Exception as e:
        st.error(f"处理数据时出错: {str(e)}")
