from clashlite import Clash
import requests
import time


def main():
    clash = Clash("../config.yaml", controller='127.0.0.1:9091')

    try:
        clash.start()
        time.sleep(2)
        # 设置全局参数
        clash.set_mode("global")
        clash.update_config({"mixed-port": 7893})
        # 获取并打印所有策略组
        groups = clash.get_groups()
        print(f"可用策略组: {groups}")

        # 获取第一个策略组的节点
        target_group = groups[0]
        nodes = clash.get_nodes(target_group)

        for node in nodes[:8]:  # 测试前三个节点
            delay = clash.get_delay(node)
            print(f"{node}: {delay or '超时'} ms")

    finally:
        clash.stop()


if __name__ == "__main__":
    main()