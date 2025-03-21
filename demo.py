from clashpy import Clash
import requests
import time


def main():
    # 初始化实例（使用默认配置）
    clash = Clash("config.yaml", show_output=True, controller='127.0.0.1:9093')

    try:
        # 启动Clash
        clash.start()

        # 设置混合端口到7893
        print("Setting mixed port to 7893...")
        clash.update_config({"mixed-port": 7893})
        time.sleep(2)  # 等待配置生效

        # 获取代理列表
        proxies = clash.get_proxies().get('proxies', {})

        # 查找第一个Selector类型的代理组
        proxy_group = next(
            (v for v in proxies.values() if v.get('type') == 'Selector'),
            None
        )

        if not proxy_group:
            raise RuntimeError("No proxy group found")

        group_name = proxy_group['name']
        available = proxy_group.get('all', [])

        if not available:
            raise RuntimeError("No available proxies")

        # 选择第一个代理
        selected = available[0]
        print(f"Selecting proxy: {selected}")
        clash.switch_proxy(group_name, selected)

        # 通过代理访问
        proxies_config = {
            'http': 'http://127.0.0.1:7893',
            'https': 'http://127.0.0.1:7893'
        }

        resp = requests.get('https://google.com', proxies=proxies_config)
        print(f"Status code: {resp.status_code}")
        print(f"Content length: {len(resp.text)}")

    finally:
        clash.stop()


if __name__ == "__main__":
    main()