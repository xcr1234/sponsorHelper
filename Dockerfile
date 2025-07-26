# 使用官方 Python 基础镜像
FROM python:3.12


# 设置工作目录
WORKDIR /app

# 将当前目录的文件复制到容器中
COPY . .


# 安装依赖
RUN pip install --no-cache-dir  -r requirements.txt


# 启动命令
CMD ["python", "main.py"]