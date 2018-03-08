# --*-- coding:utf-8 --*--
# 服务器端的ip地址192.168.72.129，编写的文件socket_server.py
# 客户端的地址ip192.168.72.130,需要编写文件socket_client.py

import socket
import time

host = ''  # ''与‘0.0.0.0’表示所有机器都可以连接,'192.168.72.130'连接特定机器
port = 7777  # 表示启用端口7777，不能使用双引号
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((host, port))  # 绑定主机与端口
s.listen(2)  # 启用两个监听2进程

while 1:  # 会出现客户端请求完成后，服务器端一直没有中断，使服务器处于死循环中
    conn, addr = s.accept()  # 地址接收所有的连接
    print 'Got connection from:', addr  # 打印连接地址
    data = conn.recv(4096)  # 一次性可以连接4096字节
    print 'get data', data  # 打印客户端请求的数据
    if not data:  # 如果没有收到客户端数据就继续接收
        time.sleep(1.5)  # 每次暂停1.5秒
        continue
    conn.sendall(data.upper())  # 如果有数据就全部回显,并且把回显的字母全部变成大写字母
conn.close()  # 如果break话，就关闭会话
