from clashlite import Clash
import requests
import time


def main():
    clash = Clash("../config.yaml", show_output=True, controller='127.0.0.1:9093')

    try:
        clash.start()

        # 设置全局参数
        clash.set_mode("global")
        clash.update_config({"mixed-port": 7893})
        # 获取并打印所有策略组
        groups = clash.get_groups()
        print(f"可用策略组: {groups}")

        if not groups:
            raise RuntimeError("没有找到策略组")

        # 获取第一个策略组的节点
        target_group = groups[0]
        nodes = clash.get_nodes(target_group)
        print(f"'{target_group}' 可用节点: {nodes}")

        if not nodes:
            raise RuntimeError("没有可用节点")

        # 测试节点延迟
        print("\n节点延迟测试:")
        for node in nodes[:8]:  # 测试前三个节点
            delay = clash.get_delay(node)
            print(f"{node}: {delay or '超时'} ms")

        # 自动选择最低延迟节点
        valid_nodes = [(node, clash.get_delay(node)) for node in nodes]
        valid_nodes = [x for x in valid_nodes if x[1] is not None]
        if valid_nodes:
            best_node = min(valid_nodes, key=lambda x: x[1])[0]
            print(f"\n自动选择节点: {best_node}")
            clash.set_proxy(target_group, best_node)
        else:
            print("\n没有可用节点，使用第一个节点")
            clash.set_proxy(0, 0)  # 使用索引方式

        # 验证连接
        proxies = {"http": "http://127.0.0.1:7893", "https": "http://127.0.0.1:7893"}
        resp = requests.get("https://example.com", proxies=proxies)
        print(f"\n访问结果: HTTP {resp.status_code}")

    finally:
        clash.stop()


if __name__ == "__main__":
    main()