from setuptools import setup, find_packages

# 读取 README.md 作为长描述
with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="clashlite",  # 这里是pip项目发布的名称
    version="0.1.0",  # 版本号
    author="LanYangYang321",
    author_email="lanyyontop@gmail.com",
    description="Managing Clash proxy core elegantly with python.",  # 简短描述
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/LanYangYang321/clash-for-python",  # 项目主页 URL
    license="MIT",
    packages=find_packages(),  # 自动查找包
    include_package_data=True,  # 包含非代码文件
    install_requires=[  # 依赖项
        "requests",
        "pyyaml",
    ],
    python_requires=">=3.7",  # Python 版本要求
    keywords=["clash", "clashlite", "pyclash", "ClashForPython", "liteclash", "clashpy"],
    platforms="Windows"
)