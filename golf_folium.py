import streamlit as st
import folium
import os
import geopandas as gpd
from streamlit_folium import folium_static

st.set_page_config(page_title="球场shapefile审查", page_icon=":golf:", layout="wide")

def apply_style(shape_type):
    style_dict = {
        "tree": {"fillColor": "green", "color": "darkgreen", "fillOpacity": 0.7, "weight": 0.5},
        "water": {"fillColor": "#6baed6", "color": "#3182bd", "fillOpacity": 0.5, "weight": 0.5},
        "sand": {"fillColor": "#fee391", "color": "#fec44f", "fillOpacity": 0.7, "weight": 0.5},
        "fairway": {"fillColor": "#a1d99b", "color": "#31a354", "fillOpacity": 0.6, "weight": 0.5},
        "green": {"fillColor": "#006d2c", "color": "#00441b", "fillOpacity": 0.7, "weight": 0.5},
        "road": {"color": "#bdbdbd", "weight": 0.5},
        "tee": {"fillColor": "#fdae6b", "color": "#e6550d", "fillOpacity": 0.7, "weight": 0.5},
        "course": {"fillColor": "#ccebc5", "color": "#006d2c", "fillOpacity": 0.3, "weight": 1},
        "land": {"fillColor": "#d9d9d9", "color": "#737373", "fillOpacity": 0.5, "weight": 0.5},
        "midline": {"color": "#ff0000", "weight": 2},
        "court": {"fillColor": "#fed976", "color": "#fd8d3c", "fillOpacity": 0.5, "weight": 1}
    }
    return style_dict.get(shape_type, {"color": "#000000", "weight": 1})

folder_path = st.text_input("请输入文件夹路径", r'C:\Users\20554\Documents\WeChat Files\wxid_3rgbpd4olus422\FileStorage\File\2024-08\Australia_200_1')
course_folders = [f for f in os.listdir(folder_path) if os.path.isdir(os.path.join(folder_path, f))]

if 'file_index' not in st.session_state:
    st.session_state.file_index = 0
if 'issues' not in st.session_state:
    st.session_state.issues = []
if 'confirm_flag' not in st.session_state:
    st.session_state.confirm_flag = False

def jump_to_course(index):
    if 0 <= index < len(course_folders):
        st.session_state.file_index = index

jump_to_index = st.number_input(f"跳转到球场索引（1-{len(course_folders)}）*点击输入框方向键上下可切换球场", min_value=1, max_value=len(course_folders))
jump_to_course(jump_to_index - 1)

course_folder = os.path.join(folder_path, course_folders[st.session_state.file_index])
court_file = os.path.join(course_folder, 'court.shp')

if os.path.exists(court_file):
    court_data = gpd.read_file(court_file)
    if court_data.crs is None:
        court_data.set_crs(epsg=4326, inplace=True)
    else:
        court_data = court_data.to_crs(epsg=4326)
    center = court_data.unary_union.centroid
    center_lat, center_lon = center.y, center.x
else:
    st.error(f"{court_file} 不存在")
    court_data = None
    center_lat, center_lon = 0, 0

m = folium.Map(location=[center_lat, center_lon], zoom_start=18, tiles=None)
folium.TileLayer(tiles='https://{s}.google.com/vt/lyrs=s&x={x}&y={y}&z={z}', attr='Google', name='Google Satellite', max_zoom=25, subdomains=['mt0', 'mt1', 'mt2', 'mt3']).add_to(m)
show_shapes = st.checkbox("显示形状", value=True)

highlight_function = lambda x: {'weight': 5, 'color': 'azure'}

def add_shapes_to_map(course_folder, m):
    if not show_shapes:
        return 0

    hole_data = {}
    non_empty_holes = set()
    
    for hole in range(1, 19):
        hole_folder = os.path.join(course_folder, str(hole))
        if os.path.isdir(hole_folder):
            hole_data[hole] = {}
            for shp_file in ["fairway.shp", "green.shp", "land.shp", "midline.shp", "road.shp", "sand.shp", "tee.shp", "tree.shp", "water.shp", "course.shp"]:
                shp_path = os.path.join(hole_folder, shp_file)
                if os.path.exists(shp_path):
                    gdf = gpd.read_file(shp_path)
                    if gdf.crs is None:
                        gdf.set_crs(epsg=4326, inplace=True)
                    else:
                        gdf = gdf.to_crs(epsg=4326)
                    if not gdf.empty:
                        hole_data[hole][shp_file] = gdf
                        non_empty_holes.add(hole)
                    else:
                        hole_data[hole][shp_file] = None
                else:
                    hole_data[hole][shp_file] = None

    if court_data is not None and not court_data.empty:
        court_layer = folium.GeoJson(
            court_data,
            name="court",
            style_function=lambda x: apply_style('court'),
            highlight_function=highlight_function,
            tooltip=folium.Tooltip('court')
        )
        court_layer.add_to(m)

    for hole in range(1, 19):
        layer_group = folium.FeatureGroup(name=f"Hole {hole}", show=True)  # Set default show to True
        for shape_type in ["course", "water", "fairway", "tree", "tee", "sand", "land", "green", "road", "midline"]:
            shp_file = f"{shape_type}.shp"
            if shp_file in hole_data[hole] and hole_data[hole][shp_file] is not None:
                gdf = hole_data[hole][shp_file]
                if not gdf.empty:
                    folium.GeoJson(gdf,style_function=lambda x, shape_type=shape_type: apply_style(shape_type),highlight_function=highlight_function,name=f"Hole {hole} - {shape_type}",tooltip=folium.Tooltip(f'{hole} - {shape_type}')).add_to(layer_group)
        layer_group.add_to(m)

    return len(non_empty_holes)

displayed_holes_count = add_shapes_to_map(course_folder, m)

st.write(f"当前球场文件夹: {course_folders[st.session_state.file_index]} ({st.session_state.file_index + 1}/{len(course_folders)}) - 球洞数: {displayed_holes_count}  -  坐标：{center_lat}, {center_lon}")

folium.LayerControl().add_to(m)

folium_static(m, width=2000, height=850)
