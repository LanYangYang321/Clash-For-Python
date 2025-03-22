from clashpy import Clash
import requests
import threading
import time
from typing import List


class ClashInstance:
    def __init__(
            self,
            instance_id: int,
            base_port: int = 7890,
            base_api_port: int = 9090,
            initial_node_index: int = 0
    ):
        self.instance_id = instance_id
        self.port = base_port + instance_id
        self.api_port = base_api_port + instance_id
        self.initial_node_index = initial_node_index
        self.current_node_index = initial_node_index

        # 初始化Clash实例
        self.clash = Clash(
            controller=f"http://127.0.0.1:{self.api_port}",
            show_output=False
        )

        # 设置运行时配置
        self.clash.update_config({
            "mixed-port": self.port,
            "external-controller": f"0.0.0.0:{self.api_port}",
            "mode": "rule"
        })

        self.proxy_group = None
        self.nodes = []

    def start_instance(self):
        try:
            # 启动Clash核心
            self.clash.start(wait=3)

            # 获取第一个策略组
            groups = self.clash.get_groups()
            if not groups:
                raise RuntimeError("No proxy groups found")
            self.proxy_group = groups[0]

            # 获取所有节点
            self.nodes = self.clash.get_nodes(self.proxy_group)
            if not self.nodes:
                raise RuntimeError("No nodes available")

            # 设置初始节点
            self._switch_node(self.initial_node_index % len(self.nodes))

            print(f"Instance {self.instance_id} started on port {self.port}")
        except Exception as e:
            print(f"Instance {self.instance_id} failed to start: {str(e)}")

    def _switch_node(self, index: int):
        """切换节点并更新当前索引"""
        if index >= len(self.nodes):
            index = 0  # 循环选择

        try:
            self.clash.set_proxy(self.proxy_group, index)
            self.current_node_index = index
        except Exception as e:
            print(f"Instance {self.instance_id} failed to switch node: {str(e)}")

    def check_ip(self):
        """检测当前IP地址"""
        proxies = {
            "http": f"http://127.0.0.1:{self.port}",
            "https": f"http://127.0.0.1:{self.port}"
        }

        try:
            response = requests.get(
                "https://api-ipv4.ip.sb/ip",
                proxies=proxies,
                timeout=10
            )
            return response.text.strip()
        except Exception as e:
            return f"Error: {str(e)}"

    def run_test_cycle(self):
        """执行测试循环"""
        while True:
            # 获取当前IP
            ip = self.check_ip()
            print(f"Instance {self.instance_id} | Node {self.current_node_index} | IP: {ip}")

            # 切换到下一个节点
            next_index = self.current_node_index + 1
            self._switch_node(next_index)

            time.sleep(5)


def main():
    # 创建5个实例，初始节点索引分别为0,5,10,15,20
    instances: List[ClashInstance] = [
        ClashInstance(0, initial_node_index=0),
        ClashInstance(1, initial_node_index=5),
        ClashInstance(2, initial_node_index=10),
        ClashInstance(3, initial_node_index=15),
        ClashInstance(4, initial_node_index=20),
    ]

    # 启动所有实例
    threads = []
    for instance in instances:
        # 启动Clash实例
        start_thread = threading.Thread(target=instance.start_instance)
        start_thread.start()
        threads.append(start_thread)
        time.sleep(1)  # 错开启动时间

    # 等待所有实例启动完成
    time.sleep(5)

    # 启动测试线程
    for instance in instances:
        test_thread = threading.Thread(target=instance.run_test_cycle)
        test_thread.daemon = True
        test_thread.start()
        threads.append(test_thread)

    try:
        # 主线程保持运行
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping instances...")
        for instance in instances:
            instance.clash.stop()


if __name__ == "__main__":
    main()
