# 使用一个轻量级的基础镜像
FROM alpine:latest

# 1. 安装 cron 和 find 工具
RUN apk add --no-cache dcron

# 2. 复制 cron 任务文件
COPY my-cron-job /etc/cron.d/my-cron-job

# 3. 赋予正确的权限
RUN chmod 0644 /etc/cron.d/my-cron-job

# 4. 创建日志文件，以便我们可以看到 cron 的输出
RUN touch /var/log/cron.log

# 5. 启动 cron 服务并持续输出日志，使其作为前台进程运行
# 这可以防止容器在启动 cron 后立即退出
CMD crond -f -l 8 && tail -f /var/log/cron.log