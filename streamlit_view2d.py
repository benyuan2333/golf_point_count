import streamlit as st
import json
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Polygon, Arc, Ellipse
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

def debug_entity(entity, entity_type="unknown"):
    """调试输出实体信息"""
    st.sidebar.expander(f"调试信息 - {entity_type}", expanded=False).json(entity)
    print(f"\n调试 {entity_type}:", json.dumps(entity, indent=2))

def validate_arc_data(edge, edge_type="arc"):
    """验证圆弧/椭圆弧数据的有效性"""
    required_fields = {
        "arc": ["center", "radius", "startAngle", "endAngle"],
        "ellipticArc": ["center", "majorAxis", "majorRadius", "minorRadius", "startAngle", "endAngle"]
    }
    
    missing_fields = [field for field in required_fields[edge_type] if field not in edge]
    if missing_fields:
        print(f"警告: {edge_type} 缺少必要字段: {missing_fields}")
        return False
        
    if edge_type == "ellipticArc" and not all(isinstance(x, (int, float)) for x in edge["majorAxis"]):
        print(f"警告: majorAxis 数据类型错误: {edge['majorAxis']}")
        return False
        
    return True

def debug_hatch_loop(loop, loop_index):
    """调试输出 hatch loop 信息"""
    print(f"\n调试 Loop {loop_index}:")
    for i, edge in enumerate(loop):
        print(f"Edge {i}: Type={edge['type']}")
        if edge['type'] == "edgeCircArc2d":
            print(f"  圆弧数据: center={edge.get('center')}, radius={edge.get('radius')}, "
                  f"angles={edge.get('startAngle')}-{edge.get('endAngle')}")
        elif edge['type'] == "edgeEllipArc2d":
            print(f"  椭圆弧数据: center={edge.get('center')}, majorAxis={edge.get('majorAxis')}, "
                  f"radii={edge.get('majorRadius')},{edge.get('minorRadius')}, "
                  f"angles={edge.get('startAngle')}-{edge.get('endAngle')}")

def generate_arc_points(center, radius, start_angle, end_angle, num_points=100):
    """生成圆弧的点"""
    # 将角度转换为弧度
    start_rad = np.radians(start_angle)
    end_rad = np.radians(end_angle)
    
    # 确保终止角度大于起始角度
    if end_rad < start_rad:
        end_rad += 2 * np.pi
        
    angles = np.linspace(start_rad, end_rad, num_points)
    x = center[0] + radius * np.cos(angles)
    y = center[1] + radius * np.sin(angles)
    return list(zip(x, y))

def generate_ellipse_arc_points(center, major_axis, major_radius, minor_radius, start_angle, end_angle, num_points=100):
    """生成椭圆弧的点"""
    try:
        # 将角度转换为弧度
        start_rad = np.radians(start_angle)
        end_rad = np.radians(end_angle)
        
        # 确保终止角度大于起始角度
        if end_rad < start_rad:
            end_rad += 2 * np.pi
            
        # 计算旋转角度
        rotation_angle = np.arctan2(major_axis[1], major_axis[0])
        
        # 生成参数方程的角度序列
        angles = np.linspace(start_rad, end_rad, num_points)
        
        # 计算未旋转的椭圆点
        x_unrotated = major_radius * np.cos(angles)
        y_unrotated = minor_radius * np.sin(angles)
        
        # 应用旋转变换
        x = center[0] + (x_unrotated * np.cos(rotation_angle) - y_unrotated * np.sin(rotation_angle))
        y = center[1] + (x_unrotated * np.sin(rotation_angle) + y_unrotated * np.cos(rotation_angle))
        
        return list(zip(x, y))
    except Exception as e:
        print(f"生成椭圆弧点时出错: {str(e)}")
        return []

if uploaded_file is not None:
    try:
        data = json.load(uploaded_file)
        st.sidebar.header("绘图信息")

        drawing = data[0].get("drawing", {})
        views = drawing.get("views", [])

        if views:
            view_names = [f"视图 {i+1} ({view.get('viewType', '未知类型')})" for i, view in enumerate(views)]
            selected_view_idx = st.sidebar.selectbox("选择视图", range(len(view_names)), format_func=lambda x: view_names[x])
            view = views[selected_view_idx]

            entities = view.get("entities", [])
            st.sidebar.write(f"实体总数: {len(entities)}")

            entity_types = list(set(entity["type"] for entity in entities))
            selected_types = st.sidebar.multiselect("选择要显示的实体类型", entity_types, default=entity_types)

            filtered_entities = [entity for entity in entities if entity["type"] in selected_types]

            fig, ax = plt.subplots(figsize=(12, 12))

            for entity in filtered_entities:
                try:
                    if entity["type"] == "line":
                        start = entity["start"]
                        end = entity["end"]
                        ax.plot(
                            [start[0], end[0]],
                            [start[1], end[1]],
                            color="blue",
                            alpha=0.7
                        )

                    elif entity["type"] == "arc":
                        debug_entity(entity, "arc")
                        if validate_arc_data(entity, "arc"):
                            center = entity["center"]
                            radius = entity["radius"]
                            start_angle = entity["startAngle"]
                            end_angle = entity["endAngle"]
                            arc = Arc(
                                xy=center,
                                width=2*radius,
                                height=2*radius,
                                theta1=start_angle,
                                theta2=end_angle,
                                angle=0,
                                color="blue",
                                alpha=0.7
                            )
                            ax.add_patch(arc)

                    elif entity["type"] == "ellipticArc":
                        debug_entity(entity, "ellipticArc")
                        if validate_arc_data(entity, "ellipticArc"):
                            center = entity["center"]
                            major_axis = entity["majorAxis"]
                            major_radius = entity["majorRadius"]
                            minor_radius = entity["minorRadius"]
                            start_angle = entity["startAngle"]
                            end_angle = entity["endAngle"]
                            
                            rotation_angle = np.degrees(np.arctan2(major_axis[1], major_axis[0]))
                            
                            ellipse = Arc(
                                xy=center,
                                width=2*major_radius,
                                height=2*minor_radius,
                                angle=rotation_angle,
                                theta1=start_angle,
                                theta2=end_angle,
                                color="blue",
                                alpha=0.7
                            )
                            ax.add_patch(ellipse)

                    elif entity["type"] == "hatch":
                        debug_entity(entity, "hatch")
                        loops = entity.get("loops", [])
                        
                        if not loops:
                            print("警告: hatch 实体没有 loops 数据")
                            continue
                            
                        for loop_idx, loop in enumerate(loops):
                            debug_hatch_loop(loop, loop_idx)
                            vertices = []
                            
                            for edge in loop:
                                try:
                                    if edge["type"] == "edgeLineSeg2d":
                                        if "start" in edge and "end" in edge:
                                            vertices.append(edge["start"])
                                            vertices.append(edge["end"])
                                        else:
                                            print(f"警告: 直线段缺少起点或终点数据: {edge}")
                                            
                                    elif edge["type"] == "edgeCircArc2d":
                                        if validate_arc_data(edge, "arc"):
                                            start_angle = edge["startAngle"]
                                            end_angle = edge["endAngle"]
                                            if end_angle < start_angle:
                                                end_angle += 360
                                            arc_points = generate_arc_points(
                                                edge["center"], 
                                                edge["radius"],
                                                start_angle,
                                                end_angle,
                                                num_points=50
                                            )
                                            vertices.extend(arc_points)
                                            
                                    elif edge["type"] == "edgeEllipArc2d":
                                        if validate_arc_data(edge, "ellipticArc"):
                                            start_angle = edge["startAngle"]
                                            end_angle = edge["endAngle"]
                                            if end_angle < start_angle:
                                                end_angle += 360
                                            ellipse_points = generate_ellipse_arc_points(
                                                edge["center"],
                                                edge["majorAxis"],
                                                edge["majorRadius"],
                                                edge["minorRadius"],
                                                start_angle,
                                                end_angle,
                                                num_points=50
                                            )
                                            vertices.extend(ellipse_points)
                                            
                                except Exception as e:
                                    print(f"处理边缘时出错: {str(e)}")
                                    continue
                            
                            if len(vertices) < 3:
                                print(f"警告: Loop {loop_idx} 顶点数量不足以形成多边形: {len(vertices)}")
                                continue
                                
                            if vertices[0] != vertices[-1]:
                                vertices.append(vertices[0])
                            
                            try:
                                polygon = Polygon(
                                    vertices,
                                    closed=True,
                                    edgecolor='red',
                                    facecolor='lightcoral',
                                    hatch='////',
                                    alpha=0.7,
                                    linewidth=0.5
                                )
                                ax.add_patch(polygon)
                            except Exception as e:
                                print(f"创建多边形时出错: {str(e)}")

                    elif entity["type"] == "circle":
                        center = entity["start"]
                        radius = entity.get("radius", 1)
                        circle = Circle(center, radius, edgecolor="red", fill=False, linewidth=1.5)
                        ax.add_patch(circle)

                except Exception as e:
                    print(f"处理实体时出错: {str(e)}")
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
