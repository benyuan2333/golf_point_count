import streamlit as st
import json
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Circle
from matplotlib import rcParams
import numpy as np

# 设置 Matplotlib 默认字体
rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans', 'Liberation Sans', 'sans-serif']
rcParams['axes.unicode_minus'] = False  # 正常显示负号

# 初始化 Streamlit 页面
st.set_page_config(page_title="2D CAD Viewer", layout="wide")
st.title("2D CAD Viewer")

# 上传 JSON 文件
uploaded_file = st.file_uploader("上传 JSON 文件", type=["json"])

def generate_arc_points(center, radius, start_angle, end_angle, num_points=100):
    """生成圆弧的点"""
    angles = np.linspace(np.radians(start_angle), np.radians(end_angle), num_points)
    x = center[0] + radius * np.cos(angles)
    y = center[1] + radius * np.sin(angles)
    return list(zip(x, y))

def generate_ellipse_arc_points(center, major_axis, major_radius, minor_radius, start_angle, end_angle, num_points=100):
    """生成椭圆弧的点"""
    major_axis = np.array(major_axis) / np.linalg.norm(major_axis)
    minor_axis = [-major_axis[1], major_axis[0]]  # 主轴的垂直方向为副轴
    angles = np.linspace(np.radians(start_angle), np.radians(end_angle), num_points)
    x = center[0] + major_radius * np.cos(angles) * major_axis[0] + minor_radius * np.sin(angles) * minor_axis[0]
    y = center[1] + major_radius * np.cos(angles) * major_axis[1] + minor_radius * np.sin(angles) * minor_axis[1]
    return list(zip(x, y))

def is_polygon_closed(vertices):
    """检查多边形是否闭合"""
    if len(vertices) > 1:
        return vertices[0] == vertices[-1]
    return False

if uploaded_file is not None:
    # 解析 JSON 文件
    data = json.load(uploaded_file)
    st.sidebar.header("绘图信息")

    # 获取绘图层级信息
    drawing = data[0].get("drawing", {})
    views = drawing.get("views", [])

    if views:
        # 显示视图列表
        view_names = [f"视图 {i+1} ({view.get('viewType', '未知类型')})" for i, view in enumerate(views)]
        selected_view_idx = st.sidebar.selectbox("选择视图", range(len(view_names)), format_func=lambda x: view_names[x])
        view = views[selected_view_idx]

        # 显示实体类型和总数
        entities = view.get("entities", [])
        st.sidebar.write(f"实体总数: {len(entities)}")

        # 筛选实体类型
        entity_types = list(set(entity["type"] for entity in entities))
        selected_types = st.sidebar.multiselect("选择要显示的实体类型", entity_types, default=entity_types)

        # 过滤实体
        filtered_entities = [entity for entity in entities if entity["type"] in selected_types]

        # 设置绘图参数
        fig, ax = plt.subplots(figsize=(12, 12))
        for entity in filtered_entities:
            if entity["type"] == "line":
                start = entity["start"]
                end = entity["end"]
                ax.plot([start[0], end[0]], [start[1], end[1]], color="blue", alpha=0.7)

            elif entity["type"] == "circle":
                center = entity["center"]
                radius = entity["radius"]
                circle = Circle(center, radius, edgecolor="red", fill=False, linewidth=1.5)
                ax.add_patch(circle)

            elif entity["type"] == "hatch":
                loops = entity.get("loops", [])
                for loop_idx, loop in enumerate(loops):
                    vertices = []
                    for edge in loop:
                        if edge["type"] == "edgeLineSeg2d":
                            vertices.append(edge["start"])
                            vertices.append(edge["end"])
                        elif edge["type"] == "edgeCircArc2d":
                            arc_points = generate_arc_points(edge["center"], edge["radius"], edge["startAngle"], edge["endAngle"])
                            vertices.extend(arc_points)
                        elif edge["type"] == "edgeEllipArc2d":
                            ellipse_points = generate_ellipse_arc_points(
                                edge["center"], edge["majorAxis"], edge["majorRadius"],
                                edge["minorRadius"], edge["startAngle"], edge["endAngle"]
                            )
                            vertices.extend(ellipse_points)
                    if vertices:
                        # 确保多边形顶点闭合
                        if not is_polygon_closed(vertices):
                            vertices.append(vertices[0])
                        polygon = Polygon(vertices, closed=True, edgecolor='red', facecolor='lightcoral', hatch='//', alpha=0.7)
                        ax.add_patch(polygon)
                    else:
                        st.sidebar.warning(f"Loop {loop_idx} in hatch entity 无有效顶点")

        ax.set_aspect('equal', adjustable='datalim')
        ax.grid(True, linestyle='--', alpha=0.5)
        ax.set_title(f"视图 {selected_view_idx + 1} - {view.get('viewType', '未知类型')}")
        ax.relim()
        ax.autoscale_view()

        # 显示图形
        st.pyplot(fig)

        # 高级功能: 导出过滤后的实体
        if st.sidebar.button("导出过滤后的实体为 JSON"):
            export_data = {"filtered_entities": filtered_entities}
            st.sidebar.download_button(
                label="下载 JSON 文件",
                data=json.dumps(export_data, ensure_ascii=False, indent=4),
                file_name="filtered_entities.json"
            )
    else:
        st.error("未找到任何视图数据！")
