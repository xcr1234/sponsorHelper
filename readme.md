自动拉取b站视频，AI总结广告之后，推送到插件https://bsbsb.top/

如何使用，

1.将文件project.example.toml复制成project.toml，然后修改其中的配置

2.执行main.py，扫码登录本服务

服务运行的时候，会产生 credential.json文件，用于记住b站登录凭证，不要泄露！

data.db文件，sqlite数据库存储所有标注过的视频

# 容器启动

推荐使用容器启动

1.将文件project.example.toml复制成project.toml，然后修改其中的配置

2.执行`docker compose up -d --build`