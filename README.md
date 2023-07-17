# DNSLog-Python
a Python DNSLog 


# 配置参数
### -h 查看配置参数
### -\-domain 你的域名 <必填>
### -\-host 你的ip (默认 0.0.0.0)
### -\-port Web UI 端口 (默认 8000)


# 使用方式
## 通过 Python 使用
### 1. 修改 .../python3.x/http/server.py 文件中,
```bash
def send_header(self, keyword, value):
    ...
            ("%s: %s\r\n" % (keyword, value)).encode('utf8', 'strict') # 将 latin-1 修改为 utf8
```
### 2. 安装依赖包
```bash
pip install -r requirements.txt
```
### 3. 运行
```bash
python -dm yourdomain -i yourip        
```
### 4. 访问 域名:端口（默认8000）

## 通过二进制文件使用
### 1. 下载二进制文件包 
[releases](https://github.com/nek0us/DNSLog-Python/releases)
### 2. 赋予权限
```bash
chmod u+x dnslog
```
### 3. 运行
```bash
dnslog -dm yourdomain -i yourip        
```
### 4. 访问 域名:端口（默认8000）

## 关闭方式
### 狂按 Ctrl + C 


# 域名配置方式
## 单域名配置方式
### 1.添加一条A记录到服务器公网IP，两条NS记录到该A记录
[![pCoIteJ.png](https://s1.ax1x.com/2023/07/17/pCoIteJ.png)](https://imgse.com/i/pCoIteJ)
### 2.域名管理中，修改 DNS Host 为A记录值
[![pCoIJL4.png](https://s1.ax1x.com/2023/07/17/pCoIJL4.png)](https://imgse.com/i/pCoIJL4)
[![pCoINw9.png](https://s1.ax1x.com/2023/07/17/pCoINw9.png)](https://imgse.com/i/pCoINw9)
## 双域名配置方式
### 见搜索引擎
