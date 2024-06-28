import requests
import time
from datetime import datetime
import streamlit as st

# 定义API凭证和端点
API_URL_FILTER = "https://www.wellcee.com/api/house/filter"
API_URL_DETAIL = "https://www.wellcee.com/api/house/getHouseInfo"
AUTHORIZATION = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0eW1lIjoxNzE5NDE3NDY4LjcwMjMxMywidXNlcl9pZCI6IjE3MTk0MTc0Nzc4NzQ5NTYiLCJleHAiOjE3NTA1MjE0NjguNzAyMzEzNCwidXNlcl9uYW1lIjoiXHU2NzJjXHU2ZTkwIn0.rnqDrzmzexm6UZvqHpRRrL4hxvcFHCfyheNndGVO0So"
HEADERS = {
    "Accept": "*/*",
    "Accept-Language": "zh",
    "Authorization": AUTHORIZATION,
    "Wellcee-DID": "52a6c99b1aad28f2b4ab1d8ce46cdb24",
    "W-SUID": "1719417477874956",
    "timestamp": str(int(time.time() * 1000)),
    "nonce": "188220",
    "signature": "OWEzN2RjODk4ZTM2MDQ2OTkzNmExMjkxN2E2NDg5Njc=",
    "Content-Type": "application/json; charset=UTF-8",
    "Host": "www.wellcee.com",
    "Connection": "Keep-Alive",
    "Accept-Encoding": "gzip",
    "User-Agent": "okhttp/4.10.0"
}
PAYLOAD_TEMPLATE = {
    "bedroom": [],
    "businessIds": [],
    "cityId": "15102233103895305",
    "districtIds": [],
    "lang": 1,
    "pn": 1,
    "price": [
        {
            "id": "16508962902406134",
            "maxPrice": 2800,
            "minPrice": 1500
        }
    ],
    "rentTypeIds": [],
    "subwayStationIds": [],
    "subways": [],
    "tagTypeIds": [],
    "timeTypeIds": [],
    "userId": "1719417477874956"
}

# 获取租房信息列表
def fetch_listings(pn, rent_type):
    payload = PAYLOAD_TEMPLATE.copy()
    payload["pn"] = pn
    payload["rentTypeIds"] = [rent_type]
    response = requests.post(API_URL_FILTER, headers=HEADERS, json=payload)
    response_data = response.json()

    if response_data.get("ret"):
        listings = response_data["data"]["list"]
        filtered_listings = [
            listing for listing in listings 
            if "NEW" in listing.get("typeTags", []) and
               "公寓" not in listing.get("typeTags", []) and 
               "青年社区" not in listing.get("typeTags", []) and
               not any(keyword in listing.get("address", "") for keyword in ["松江", "青浦", "奉贤", "金山", "公寓"])
        ]
        return filtered_listings
    else:
        print(f"获取列表失败，页码: {pn}")
        return []

# 获取房源详细信息
def fetch_house_detail(house_id):
    params = {
        "id": house_id,
        "lang": 1,
        "userId": "1719417477874956"
    }
    response = requests.get(API_URL_DETAIL, headers=HEADERS, params=params)
    response_data = response.json()

    if response_data.get("ret"):
        house_detail = response_data["data"]
        return house_detail
    else:
        print(f"获取房源详情失败，房源ID: {house_id}")
        return {}

# 格式化消息
def format_message(listings):
    formatted_listings = []
    for listing in listings:
        imgs = listing["imgs"][:5]
        rent = listing["rent"]
        address = listing["address"]

        # 获取房源详细信息
        house_detail = fetch_house_detail(listing["id"])
        if house_detail:
            desc = house_detail.get("desc", "无描述")
            desc = desc[:50] + '...' if len(desc) > 50 else desc
            deposit = house_detail.get("deposit", "未提供押金信息")
            subways = house_detail.get("subways", "未提供地铁信息")
            share_url = house_detail.get("shareUrl", "未提供主页信息")

            # 解析loginTime
            login_time_timestamp = listing.get("loginTime", 0)
            dt_object = datetime.fromtimestamp(login_time_timestamp)
            formatted_login_time = dt_object.strftime('%Y-%m-%d %H:%M:%S')

            formatted_listings.append({
                "address": address,
                "rent": rent,
                "deposit": deposit,
                "desc": desc,
                "subways": subways,
                "login_time": formatted_login_time,
                "share_url": share_url,
                "imgs": imgs
            })

    return formatted_listings

# Streamlit 应用
st.title("Wellcee 房源信息")
rent_type = st.selectbox("选择租房类型", ["NJ整租-Wellcee", "NJ合租-Wellcee"])
rent_type_id = "15103931190241306" if rent_type == "NJ整租-Wellcee" else "15102331590936289"

if st.button("获取最新房源"):
    listings = []
    for pn in range(1, 21):
        new_listings = fetch_listings(pn, rent_type_id)
        listings.extend(new_listings)

    # 按loginTime排序
    listings = sorted(listings, key=lambda x: x["loginTime"], reverse=True)
    formatted_listings = format_message(listings)

    # 显示房源信息
    for listing in formatted_listings:
        st.subheader(f"地址: {listing['address']}")
        st.write(f"租金: {listing['rent']} 元")
        st.write(f"押金: {listing['deposit']}")
        st.write(f"描述: {listing['desc']}")
        st.write(f"地铁信息: {listing['subways']}")
        st.write(f"最后登录时间: {listing['login_time']}")
        st.write(f"[房源链接]({listing['share_url']})")
        for img in listing["imgs"]:
            st.image(img, width=400)
        st.markdown("---")