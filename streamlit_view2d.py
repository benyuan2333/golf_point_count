import streamlit as st
import json
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Polygon
from matplotlib import rcParams

# 设置 Matplotlib 默认字体（无需特定中文字体）
rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans', 'Liberation Sans', 'sans-serif']
rcParams['axes.unicode_minus'] = False  # 正常显示负号

# 初始化 Streamlit 页面
st.set_page_config(page_title="2D CAD Viewer", layout="wide")
st.title("2D CAD Viewer")

# 上传 JSON 文件
uploaded_file = st.file_uploader("上传 JSON 文件", type=["json"])

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
            if entity["type"] == "hatch":
                loops = entity.get("loops", [])
                for loop in loops:
                    vertices = []
                    for edge in loop:
                        if edge["type"] == "edgeLineSeg2d":
                            vertices.append(edge["start"])
                            vertices.append(edge["end"])
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
                        # 标注 hatch 的中心点
                        center_x = sum(v[0] for v in vertices) / len(vertices)
                        center_y = sum(v[1] for v in vertices) / len(vertices)
                        ax.text(center_x, center_y, "Hatch", color="red", fontsize=12, ha='center', va='center')

            # 处理其他类型
            if entity["type"] == "circle":
                center = entity["start"]
                radius = entity.get("radius", 1)
                circle = Circle(center, radius, edgecolor="red", fill=False, linewidth=1.5)
                ax.add_patch(circle)

        # 提取并标注基准点信息
        datum_entities = [
            entity for entity in entities if entity["type"] == "mLeader" and 
            "DATUM_TARGET" in entity.get("userData", {}).get("businessInfo", [])
        ]
        for datum in datum_entities:
            leader_points = datum.get("leaderPoints", [])
            last_vertex = datum.get("lastVertex", [0, 0])
            if leader_points:
                # 标注起点 leaderPoint
                start_position = leader_points[0]
                text_content = datum.get("textOption", {}).get("textContent", "未知")
                ax.scatter(start_position[0], start_position[1], color="red", label="基准点起点", zorder=6)
                ax.text(start_position[0], start_position[1], f"{text_content}", color="red", fontsize=12, zorder=6)

        # 设置图形外观
        ax.set_aspect('equal', adjustable='datalim')
        ax.grid(True, linestyle='--', alpha=0.5)
        ax.set_title(f"视图 {selected_view_idx + 1} - {view.get('viewType', '未知类型')}")

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
