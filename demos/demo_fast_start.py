from clashlite import Clash
import requests
import time


# 创建 Clash 实例
clash = Clash(config_path="..\config.yaml", controller="127.0.0.1:9095")

# 启动 Clash 核心
clash.start()

# 获取所有代理组
groups = clash.get_groups()
print(clash.get_nodes(groups[1]))
# 切换到第一个代理组的第一个节点
clash.set_proxy(groups[0], 20)

clash.update_config({"mixed-port": 7883})
clash.set_mode('global')

# 获取代理列表
proxies = clash.get_proxies().get('proxies', {})

# 通过代理访问
proxies_config = {
    'http': 'http://127.0.0.1:7883',
    'https': 'http://127.0.0.1:7883'
}

resp = requests.get('https://google.com', proxies=proxies_config)
print(f"Status code: {resp.status_code}")
print(f"Content length: {len(resp.text)}")

