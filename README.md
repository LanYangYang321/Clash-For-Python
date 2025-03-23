# Clash-for-python








[![Bilibili 粉丝](https://img.shields.io/badge/dynamic/json?color=blue&label=BiliBili&labelColor=white&query=$.data.follower&url=https://api.bilibili.com/x/relation/stat?vmid=1084866085&logo=bilibili)](https://space.bilibili.com/1084866085)
[![YouTube](https://img.shields.io/badge/YouTube-white?logo=youtube&logoColor=FF0000)](https://www.youtube.com/@lyyontop)
[![GitHub last commit](https://img.shields.io/github/last-commit/LanYangYang321/Clash-For-Python?color=yellow&logo=github&labelColor=black&label=Latest)](https://github.com/LanYangYang321/Clash-For-Python)
[![PyPI](https://img.shields.io/pypi/v/clashlite?color=greeen&label=Clashlite&logo=Pypi&logoColor=white)](https://pypi.org/project/clashlite/)
## clashlite

A Python library for managing Clash core instances with advanced configuration control.

## Features

- Start and stop Clash core instances.
- Dynamically update configurations.
- Manage proxies and groups.
- Test node latency.
- Support for temporary configuration files.

## Installation

```bash
pip install clashlite
```

## Usage
### 1. Init a clash core instance:
```python
clash = Clash(
    config_path: Optional[str] = "..\config.yaml",
    exe_path: str = "clash-verge-core.exe",
    controller: str = "127.0.0.1:9090",
    api_secret: Optional[str] = None,
    show_output: bool = False
)
```
- config: a clash config `..\config.yaml`
- exe_path: enter the clash core you want to use, or leave blank to use default clash core. `..\clah-verge-core.exe` 
- controller: set the clash external controller address, or leave blankto default. Default value: `127.0.0.1:9090`
- api_secret: clash core controller api secret
- show_output: `bool` show clash core output or not.

### 2. Start and stop

```python
clash.start(wait: int = 5)
```
launch the clash core.
- wait: the wait time after send the launch command, to ensure the core is fully lunched.


```python
clash.stop()
```
stop a clash core

---

## 快速开始

```python
from clashlite import Clash

# 创建 Clash 实例
clash = Clash(config_path="config.yaml", controller="http://127.0.0.1:9090")

# 启动 Clash 核心
clash.start()

# 获取所有代理组
groups = clash.get_groups()

# 切换到第一个代理组的第一个节点
clash.set_proxy(groups[0], 0)

# 停止 Clash 核心
clash.stop()
```

---

## API 文档

### 1. 初始化 Clash 实例

```python
clash = Clash(
    config_path: Optional[str] = None,
    exe_path: str = "clash-verge-core.exe",
    controller: str = "http://127.0.0.1:9090",
    api_secret: Optional[str] = None,
    show_output: bool = False
)
```

**参数**:
- `config_path`: Clash 配置文件路径（可选）。
- `exe_path`: Clash 可执行文件路径，默认为当前目录下的 `clash-verge-core.exe`。
- `controller`: Clash 控制 API 地址，默认为 `http://127.0.0.1:9090`。
- `api_secret`: Clash API 密钥（如果配置文件中已设置，可省略）。
- `show_output`: 是否显示 Clash 核心的输出日志。

---

### 2. 启动和停止 Clash 核心

- **启动 Clash 核心**:
  ```python
  clash.start(wait: int = 5)
  ```
  **参数**:
  - `wait`: 启动后等待的秒数，确保 Clash 核心完全启动。

- **停止 Clash 核心**:
  ```python
  clash.stop()
  ```

---


- **获取当前配置**:
  ```python
  config = clash.get_config()
  ```
  **返回**: 当前 Clash 配置的字典。

---

- **切换代理**:
  ```python
  clash.switch_proxy(group_name: str, new_proxy: str)
  ```
  **参数**:
  - `group_name`: 代理组名称。
  - `new_proxy`: 新的代理节点名称。

---

- **获取所有策略组**:
  ```python
  groups = clash.get_groups()
  ```
  **返回**: 所有策略组名称的列表。


---

- **测试节点延迟**:
  ```python
  def get_delay(self,
                  target: str,
                  test_url: str = "http://www.example.com",
                  timeout: int = 2000)
  ```
  **参数**:
  - `test_url`: 测试 URL。
  - `timeout`: 超时时间（毫秒）。

---

- **设置代理模式**:
  ```python
  clash.set_mode(mode: str = "rule")
  ```
  **参数**:
  - `mode`: 代理模式（`rule`/`global`/`direct`）。


