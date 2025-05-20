import requests

url = "https://api.ownthink.com/kg/knowledge?entity "
params = {
    "entity": "深度求索"
}

response = requests.post(url, json=params)

print("Status Code:", response.status_code)  # 应为 200
print("Response Text:", response.text)      # 查看是否是 JSON 或 HTML

try:
    print("JSON Data:", response.json())    # 尝试解析 JSON
except requests.exceptions.JSONDecodeError:
    print("Failed to decode JSON.")
