# --*-- coding:utf-8 --*--
# 客户端的地址ip192.168.72.130,编写文件为socket_client.py

import socket  # 导入socket模块

host = 'localhost'  # 服务器端的ip地址
port = 7777  # 服务器端的端口
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # 启用ipv4的tcp/ip协议与类型
s.connect((host, port))  # 连接服务器端的主机与端口

s.sendall('/home/dl/sunbo/image_caption/im2txt/data/mscoco/raw-data/val2014/COCO_val2014_000000224477.jpg')  # 客户端发送的信息
data = s.recv(4096)  # 服务器端返回信息就赋值给data
s.close()  # 不返回信息就断开连接
print 'received', repr(data)  # 打印返回的信息
