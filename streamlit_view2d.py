import streamlit as st
import json
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Polygon, Arc, Ellipse
from matplotlib import rcParams
import numpy as np
import math

# 设置 Matplotlib 默认字体（无需特定中文字体）
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
    angles = np.linspace(np.radians(start_angle), np.radians(end_angle), num_points)
    # 计算椭圆旋转角度
    phi = math.atan2(major_axis[1], major_axis[0])
    
    x = center[0] + major_radius * np.cos(angles) * np.cos(phi) - minor_radius * np.sin(angles) * np.sin(phi)
    y = center[1] + major_radius * np.cos(angles) * np.sin(phi) + minor_radius * np.sin(angles) * np.cos(phi)
    return list(zip(x, y))

if uploaded_file is not None:
    # 解析 JSON 文件
    data = json.load(uploaded_file)
    st.sidebar.header("绘图信息")

    # 显示绘图层级信息
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
            try:
                if entity["type"] == "line":
                    start = entity["start"]
                    end = entity["end"]
                    ax.plot(
                        [start[0], end[0]],
                        [start[1], end[1]],
                        label=f'Line {entity.get("userData", {}).get("uuid", "")}',
                        color="blue",
                        alpha=0.7
                    )

                # 处理 hatch 实体
                elif entity["type"] == "hatch":
                    loops = entity.get("loops", [])
                    for loop in loops:
                        vertices = []
                        for edge in loop:
                            if edge["type"] == "edgeLineSeg2d":
                                vertices.append(edge["start"])
                                vertices.append(edge["end"])
                            elif edge["type"] == "edgeCircArc2d":
                                center = edge.get("center")
                                radius = edge.get("radius")
                                start_angle = edge.get("startAngle")
                                end_angle = edge.get("endAngle")
                                if None in (center, radius, start_angle, end_angle):
                                    st.warning("圆弧实体缺少必要字段，跳过此边。")
                                    continue
                                arc_points = generate_arc_points(center, radius, start_angle, end_angle)
                                vertices.extend(arc_points)
                            elif edge["type"] == "edgeEllipArc2d":
                                center = edge.get("center")
                                major_axis = edge.get("majorAxis")
                                major_radius = edge.get("majorRadius")
                                minor_radius = edge.get("minorRadius")
                                start_angle = edge.get("startAngle")
                                end_angle = edge.get("endAngle")
                                if None in (center, major_axis, major_radius, minor_radius, start_angle, end_angle):
                                    st.warning("椭圆弧实体缺少必要字段，跳过此边。")
                                    continue
                                ellipse_points = generate_ellipse_arc_points(center, major_axis, major_radius, minor_radius, start_angle, end_angle)
                                vertices.extend(ellipse_points)
                        if vertices:
                            # 创建多边形并填充红色斜线
                            polygon = Polygon(
                                vertices,
                                closed=True,
                                edgecolor='red',  # 边框颜色
                                facecolor='lightcoral',  # 填充颜色
                                hatch='////',  # 增加斜线密度
                                alpha=0.7,  # 透明度
                                linewidth=0.5  # 斜线粗细
                            )
                            ax.add_patch(polygon)

                # 处理圆弧实体
                elif entity["type"] == "arc":
                    center = entity["center"]
                    radius = entity["radius"]
                    start_angle = entity["startAngle"]
                    end_angle = entity["endAngle"]
                    arc = Arc(
                        center,
                        2*radius,
                        2*radius,
                        angle=0,
                        theta1=start_angle,
                        theta2=end_angle,
                        edgecolor="green",
                        linewidth=1.5,
                        zorder=5
                    )
                    ax.add_patch(arc)

                # 处理椭圆弧实体
                elif entity["type"] == "ellipse":
                    center = entity["center"]
                    major_axis = entity["majorAxis"]
                    major_radius = entity["majorRadius"]
                    minor_radius = entity["minorRadius"]
                    start_angle = entity["startAngle"]
                    end_angle = entity["endAngle"]
                    # 计算旋转角度（度）
                    phi = math.degrees(math.atan2(major_axis[1], major_axis[0]))
                    ellipse = Ellipse(
                        center,
                        width=2*major_radius,
                        height=2*minor_radius,
                        angle=phi,
                        edgecolor="purple",
                        linewidth=1.5,
                        zorder=5,
                        fill=False
                    )
                    ax.add_patch(ellipse)
                    # 绘制椭圆弧部分
                    angles = np.linspace(np.radians(start_angle), np.radians(end_angle), 100)
                    x = center[0] + major_radius * np.cos(angles) * np.cos(math.radians(phi)) - minor_radius * np.sin(angles) * np.sin(math.radians(phi))
                    y = center[1] + major_radius * np.cos(angles) * np.sin(math.radians(phi)) + minor_radius * np.sin(angles) * np.cos(math.radians(phi))
                    ax.plot(x, y, color="purple", linewidth=1.5, zorder=6)

                # 处理圆形实体
                elif entity["type"] == "circle":
                    center = entity["center"]
                    radius = entity.get("radius", 1)
                    circle = Circle(center, radius, edgecolor="red", fill=False, linewidth=1.5, zorder=5)
                    ax.add_patch(circle)

                # 处理基准点 (mLeader)
                elif entity["type"] == "mLeader":
                    user_data = entity.get("userData", {})
                    business_info = user_data.get("businessInfo", [])
                    if "DATUM_TARGET" in business_info:
                        leader_points = entity.get("leaderPoints", [])
                        if leader_points:
                            # 标注起点 leaderPoint
                            start_position = leader_points[0]
                            text_content = entity.get("textOption", {}).get("textContent", "未知")
                            ax.scatter(start_position[0], start_position[1], color="red", zorder=6)
                            ax.text(start_position[0], start_position[1], f"{text_content}", color="red", fontsize=12, zorder=6)

            except Exception as e:
                st.error(f"绘制 {entity.get('type', '未知类型')} 实体时出错: {e}")

        # 设置图形外观
        ax.set_aspect('equal', adjustable='datalim')
        ax.grid(True, linestyle='--', alpha=0.5)
        ax.set_title(f"视图 {selected_view_idx + 1} - {view.get('viewType', '未知类型')}")

        # 自动缩放视图
        ax.relim()
        ax.autoscale_view()

        # 显示图形
        st.pyplot(fig)

        # 高级功能: 导出过滤后的实体
        if st.sidebar.button("导出过滤后的实体为 JSON"):
            export_data = {"filtered_entities": filtered_entities}
            json_data = json.dumps(export_data, ensure_ascii=False, indent=4)
            st.sidebar.download_button(
                label="下载 JSON 文件",
                data=json_data,
                file_name="filtered_entities.json"
            )
    else:
        st.error("未找到任何视图数据！")
