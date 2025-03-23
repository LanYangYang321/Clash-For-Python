import os
import subprocess
import tempfile
import time
import requests
import yaml
from threading import Lock
from typing import Dict, List, Optional, Union


class Clash:
    """
    Clash 内核 Python 控制类

    Attributes:
        exe_path (str): Clash 可执行文件路径
        original_config_path (str): 原始配置文件路径
        temp_config_path (str): 临时配置文件路径
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
        self.original_config_path = config_path
        self.temp_config_path = None  # type: Optional[str]
        self.controller = controller.rstrip('/')
        self.api_secret = api_secret
        self.show_output = show_output
        self.process = None  # type: Optional[subprocess.Popen]
        self._runtime_config = {}
        self._lock = Lock()

        # 处理配置文件
        if self.original_config_path:
            self._prepare_config_file()

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

    def stop(self):
        """停止Clash核心并清理临时文件"""
        if self.process:
            self.process.terminate()
            self.process.wait()
            self.process = None
        self._cleanup_temp_file()

    def _cleanup_temp_file(self):
        """清理临时配置文件"""
        if self.temp_config_path and self.temp_config_path != self.original_config_path:
            try:
                os.remove(self.temp_config_path)
                print(f"Removed temporary config: {self.temp_config_path}")
            except Exception as e:
                print(f"清理临时文件失败: {str(e)}")
            finally:
                self.temp_config_path = None

    def _sync_current_config(self):
        """同步当前配置"""
        try:
            config = self.get_config()
            # 更新实际生效的controller地址
            if 'external-controller' in config:
                effective_controller = config['external-controller']
                self.controller = f"http://{effective_controller}"
            # 同步API密钥
            if 'secret' in config:
                self.api_secret = config.get('secret', self.api_secret)
        except Exception as e:
            print(f"配置同步警告: {str(e)}")

    def __del__(self):
        """析构时确保清理"""
        self.stop()

    def _headers(self) -> Dict:
        return {"Authorization": f"Bearer {self.api_secret}"} if self.api_secret else {}

    def _request(self, method: str, endpoint: str, **kwargs):
        """发送API请求"""
        url = f"http://{self.controller}{endpoint}"
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
            raise RuntimeError(f"API请求失败: {str(e)}, 请检查是否已经启动了clash核心")

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
        """获取所有策略组名称列表"""
        proxies = self._request("GET", "/proxies").get("proxies", {})
        return [
            name for name, info in proxies.items()
            if info.get("type") in ["Selector", "URLTest", "Fallback", "LoadBalance"]
        ]

    def get_nodes(self, group: Union[str, int]) -> List[str]:
        """
        获取策略组内的所有节点名称

        Args:
            group: 策略组名称或通过get_groups()获取的索引位置
        """
        # 处理数字索引输入
        if isinstance(group, int):
            groups = self.get_groups()
            group = groups[group]

        try:
            info = self._request("GET", f"/proxies/{group}")
            return info.get("all", [])
        except:
            return []

    def set_proxy(self,
                  group: Union[str, int],
                  node: Union[str, int]):
        """
        设置策略组使用指定节点

        Args:
            group: 策略组名称或get_groups()返回的索引
            node: 节点名称或get_nodes()返回的索引
        """
        # 处理数字索引输入
        if isinstance(group, int):
            groups = self.get_groups()
            group = groups[group]

        # 处理节点索引
        if isinstance(node, int):
            nodes = self.get_nodes(group)
            node = nodes[node]

        return self._request("PUT", f"/proxies/{group}", json={"name": node})