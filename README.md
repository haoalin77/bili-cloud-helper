# 云端弹幕模拟实验室（不向真实 B站发送）

使用纯 Python 标准库实现网页控制台和后台测试任务，可模拟从弹幕库中随机挑选文本，定期生成日志，并支持 CSV 导出。

**重要：本项目不访问 B站，不登录账号，不发送真实弹幕，也不计入直播活动。**

## 本地运行

需要 Python 3.9+，无需第三方依赖。

```bash
# macOS / Linux
ADMIN_TOKEN='自定义一个足够长的密码' python app.py

# Windows PowerShell
$env:ADMIN_TOKEN='自定义一个足够长的密码'
python app.py
```

打开 `http://localhost:8080`，在「管理口令」栏填写刚才设置的密码。

## Railway 部署

1. 新建一个 GitHub 仓库，将 `app.py`、`requirements.txt`、`Procfile`、`README.md` 上传；不需要上传用户设置文件。
2. 登录 https://railway.com ，选择 **New Project → Deploy from GitHub repo**，选择这个仓库。
3. 在 Railway 项目的服务变量（Variables）中新增 `ADMIN_TOKEN`，设为独立的长随机密码；不要把密码提交到 GitHub。
4. Railway 会依据 `Procfile` 运行 `python app.py`（如果未识别，可在 Start Command 手动设置 `python app.py`）。程序会自动读取平台提供的 `PORT`。
5. 在 Networking 中生成公开域名，浏览器访问域名，在页面输入管理口令，保存设置、启动模拟。
6. 如需重启后仍保存设置，在服务中配置持久磁盘卷并设置 `DATA_DIR` 为磁盘挂载目录。否则部署重启后配置可能丢失。
7. 不想继续使用时，到 Railway 停止或删除服务，避免持续计费。

不同套餐可能需要额外配置或支付运行费用，具体以官方价格页面为准。

## 注意事项

- 云端进程在正常运行时不依赖本机开机，但云平台可能因为额度、部署失败、重启等停止它。
- 管理口令尽量设置为随机长密码；不要在公开项目里写 B站登录信息或 Cookie。
- 「自动发送」仅指自动生成**模拟日志**，并未发送任何真实消息。
