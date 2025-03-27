import os
import subprocess
import tempfile
import time
import requests
import yaml
from threading import Lock
from typing import Dict, List, Optional, Union


class Clash:
    def __init__(self, config_path: Optional[str] = None,
                 exe_path: str = os.path.join(os.path.dirname(__file__), "clash-verge-core.exe"),
                 controller: str = "127.0.0.1:9090",
                 show_output: bool = False,
                 mode: str = "rule"):

        self.exe_path = exe_path
        self.original_config_path = config_path
        self.temp_config_path = None  # type: Optional[str]
        self.controller = controller
        self.show_output = show_output
        self.process = None  # type: Optional[subprocess.Popen]
        self._runtime_config = {}
        self._lock = Lock()

        # 处理配置文件
        if self.original_config_path:
            self._prepare_config_file()

    def __del__(self):
        if self.process:
            self.process.terminate()
            self.process.wait()
            self.process = None
        if self.temp_config_path and self.temp_config_path != self.original_config_path:
            try:
                os.remove(self.temp_config_path)
                print(f"Removed temporary config: {self.temp_config_path}")
            except Exception as e:
                print(f"清理临时文件失败: {str(e)}")
            finally:
                self.temp_config_path = None

    def _prepare_config_file(self):
        """通过文本替换方式处理配置文件"""

        # 解析目标controller地址
        target_controller = self.controller.replace("http://", "").replace("https://", "")

        # 读取原始配置文件内容
        with open(self.original_config_path, 'r', encoding='utf-8') as f:
            raw_config = f.read()
        with open(self.original_config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        if 'external-controller' in config:
            controller_addr = config['external-controller']
            temp_config = raw_config.replace(f"external-controller: '{controller_addr}'", f"external-controller: '{target_controller}'")
        else:
            temp_config = f"external-controller: '{target_controller}'\n" + raw_config


        # 创建临时文件
        fd, temp_path = tempfile.mkstemp(suffix='.yaml', dir=tempfile.gettempdir())
        os.close(fd)

        # 写入处理后的内容
        with open(temp_path, 'w', encoding='utf-8') as f:
            f.write(temp_config)

        self.temp_config_path = temp_path
        print(f"Generated temporary config at: {temp_path}")

    def start(self, wait: int = 5):
        """启动Clash核心"""
        args = [self.exe_path]
        config_path = self.temp_config_path or self.original_config_path

        if config_path:
            if not os.path.exists(config_path):
                raise FileNotFoundError(f"配置文件不存在: {config_path}")
            args.extend(["-f", config_path])

        try:
            self.process = subprocess.Popen(
                args,
                stdout=subprocess.PIPE if not self.show_output else None,
                stderr=subprocess.STDOUT if not self.show_output else None,
                start_new_session=True
            )
            time.sleep(wait)
            self._sync_current_config()
        except Exception as e:
            self._cleanup_temp_file()
            raise RuntimeError(f"启动失败: {str(e)}")

    def update_config(self, updates: Dict):
        """更新运行配置"""
        with self._lock:
            self._runtime_config.update(updates)
            return self._request("PATCH", "/configs", json=updates)

    def get_delay(self,
                  target: str,
                  test_url: str = "http://www.example.com",
                  timeout: int = 2000) -> Optional[int]:
        """
        获取节点/策略组延迟（单位：ms）

        Args:
            target: 节点名称或策略组名称
            test_url: 测试用的URL
            timeout: 超时时间（毫秒）

        Returns:
            延迟数值（毫秒），失败返回None
        """
        params = {"url": test_url, "timeout": timeout}
        try:
            # 尝试作为代理节点测试
            result = self._request("GET", f"/proxies/{target}/delay", params=params)
            return result.get("delay")
        except:
            # 尝试作为策略组测试
            try:
                result = self._request("GET", f"/group/{target}/delay", params=params)
                return result.get("delay")
            except:
                return None

    def set_mode(self, mode: str = "rule"):
        """设置代理模式（rule/global/direct）"""
        valid_modes = ["rule", "global", "direct"]
        if mode not in valid_modes:
            raise ValueError(f"Invalid mode. Valid options: {valid_modes}")
        return self.update_config({"mode": mode})

    def get_groups(self) -> List[str]:
        return [
            name for name, info in requests.get(f"http://{self.controller}/proxies").json().get("proxies", {}).items()
            if info.get("type") in ["Selector", "URLTest", "Fallback", "LoadBalance"]
        ]

    def get_nodes(self, group: Union[str, int]) -> List[str]:
        # 处理数字索引输入
        if isinstance(group, int):
            groups = self.get_groups()
            group = groups[group]

        try:
            return requests.get(f"http://{self.controller}/proxies/{group}").json().get("all", [])
        except:
            return []

    def set_proxy(self,
                  group: Union[str, int],
                  node: Union[str, int]):

        # 处理数字索引输入
        if isinstance(group, int):
            groups = self.get_groups()
            group = groups[group]

        # 处理节点索引
        if isinstance(node, int):
            nodes = self.get_nodes(group)
            node = nodes[node]

        return requests.put(f"http://{self.controller}/proxies/{group}", json={"name": node})

    def close_all_connections(self):
        """清除所有连接"""
        return requests.delete(f"{self.controller}")
        return self._request("DELETE", "/connections")
