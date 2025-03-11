# 基础镜像选择Python官方镜像（根据您的Python版本调整）
FROM python:3.11.11

# 设置工作目录
WORKDIR /TDvis

# 复制依赖文件
COPY requirements.txt .

# 安装依赖（使用阿里云镜像加速）
RUN pip3 install --no-cache-dir -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
RUN 

# 复制项目文件
COPY . .

# 暴露Streamlit默认端口
EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

# 启动命令（假设主程序是app.py）
ENTRYPOINT ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]