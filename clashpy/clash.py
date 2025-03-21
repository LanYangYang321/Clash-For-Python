import os
import subprocess
import time
import requests
import yaml
from threading import Lock
from typing import Dict, Optional


class Clash:
    """
    Clash 内核 Python 控制类

    Attributes:
        exe_path (str): Clash 可执行文件路径
        config_path (str): 配置文件路径
        controller (str): 控制接口地址
        api_secret (str): API 密钥
        show_output (bool): 是否显示Clash输出
    """

    def __init__(self, config_path: Optional[str] = None,
                 exe_path: str = os.path.join(os.path.dirname(__file__), "clash-verge-core.exe"),
                 controller: str = "http://127.0.0.1:9090",
                 api_secret: Optional[str] = None,
                 show_output: bool = False):
        self.exe_path = exe_path
        self.config_path = config_path
        self.controller = controller.rstrip('/')
        self.api_secret = api_secret
        self.show_output = show_output
        self.process = None
        self._runtime_config = {}
        self._lock = Lock()

        # 解析配置文件
        if self.config_path:
            self._parse_initial_config()

    def _parse_initial_config(self):
        """解析初始化配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                # 处理控制端口
                if 'external-controller' in config:
                    self._update_controller(config['external-controller'])
                # 处理密钥
                if 'secret' in config and self.api_secret is None:
                    self.api_secret = config['secret']
        except Exception as e:
            print(f"配置文件解析警告: {str(e)}")

    def _update_controller(self, controller_str: str):
        """更新控制地址"""
        if ':' in controller_str:
            host, port = controller_str.split(':', 1)
            self.controller = f"http://127.0.0.1:{port}" if host == '0.0.0.0' else f"http://{controller_str}"

    def start(self, wait: int = 5):
        """启动Clash核心"""
        args = [self.exe_path]
        if self.config_path:
            args.extend(["-f", self.config_path])

        try:
            self.process = subprocess.Popen(
                args,
                stdout=subprocess.PIPE if not self.show_output else None,
                stderr=subprocess.STDOUT if not self.show_output else None
            )
            time.sleep(wait)
            # 获取最新配置
            self._sync_current_config()
        except Exception as e:
            raise RuntimeError(f"启动失败: {str(e)}")

    def _sync_current_config(self):
        """同步当前配置"""
        try:
            config = self.get_config()
            if 'external-controller' in config:
                self._update_controller(config['external-controller'])
            if 'secret' in config:
                self.api_secret = config.get('secret', self.api_secret)
        except:
            pass

    def stop(self):
        """停止Clash核心"""
        if self.process:
            self.process.terminate()
            self.process.wait()

    def _headers(self) -> Dict:
        return {"Authorization": f"Bearer {self.api_secret}"} if self.api_secret else {}

    def _request(self, method: str, endpoint: str, **kwargs):
        """发送API请求"""
        url = f"{self.controller}{endpoint}"
        try:
            response = requests.request(
                method,
                url,
                headers=self._headers(),
                timeout=10,
                **kwargs
            )
            response.raise_for_status()
            return response.json() if response.content else {}
        except Exception as e:
            raise RuntimeError(f"API请求失败: {str(e)}")

    # 以下是API封装（示例实现关键API）
    def update_config(self, updates: Dict):
        """更新运行配置"""
        with self._lock:
            self._runtime_config.update(updates)
            return self._request("PATCH", "/configs", json=updates)

    def get_proxies(self) -> Dict:
        """获取所有代理"""
        return self._request("GET", "/proxies")

    def switch_proxy(self, group: str, proxy: str):
        """切换代理"""
        return self._request("PUT", f"/proxies/{group}", json={"name": proxy})

    def get_config(self) -> Dict:
        """获取当前配置"""
        return self._request("GET", "/configs")

    def set_runtime_config(self, updates: Dict):
        """设置运行时配置（合并更新）"""
        return self.update_config(updates)