import asyncio
import datetime
import json
import uuid

import websockets
import websockets.exceptions
from chatting import handle_message, generate_message_id, clients, connected_users, blocked_users
from config import connections


# 生成客户端ID
def generate_client_id():
    return str(uuid.uuid4())


# 发送欢迎消息
async def send_welcome_message(client_websocket, client_id):
    welcome_message = f"Welcome, client {client_id}!"
    await client_websocket.send(welcome_message)





# 接收系统发送的消息
async def receive_system_message():
    for client_websocket in clients.values():
        try:
            # 接收系统消息
            message = await client_websocket.recv()

            # 在这里编写处理系统消息的逻辑
            # 根据接收到的消息内容进行相应的操作

            # 处理消息并触发消息提醒
            if message == "notification":
                show_notification()

        except websockets.exceptions.ConnectionClosed:
            # 处理连接关闭时的异常
            continue


# 通知提醒功能还没写好
def show_notification():
    pass





# 获取客户端信息
async def get_client_info(client_websocket):
    # 在这里编写获取客户端信息的逻辑
    # 根据客户端的请求参数获取用户名、IP地址等信息

    # 获取WebSocket连接的请求对象
    request = client_websocket.request

    # 获取远程地址（IP地址）
    remote_address = client_websocket.remote_address[0]

    # 获取用户代理（User-Agent）
    user_agent = request.headers.get('User-Agent', '')

    return {
        'remote_address': remote_address,
        'user_agent': user_agent
    }


# 添加客户端到连接列表
def add_client_to_list(client_websocket, client_id, client_info):
    # 在这里编写将客户端添加到连接列表的逻辑
    # 例如将客户端信息保存到一个全局连接列表中
    # 将客户端WebSocket对象和客户端信息作为键值对添加到字典中
    connections[client_websocket] = {"id": client_id, "address": client_info}

# 创建新连接
async def handle_new_connection(client_websocket, client_address):
    try:
        # 执行与新连接相关的初始化操作
        # 分配一个唯一的客户端ID
        client_id = generate_client_id()

        welcome_message = "Welcome to the chat room!"
        await client_websocket.send(welcome_message)

        # 示例：获取客户端信息
        client_info = await get_client_info(client_websocket)

        # 在这里可以根据需求进行其他操作
        # 例如将客户端信息添加到连接列表中
        # 添加到连接列表
        add_client_to_list(client_websocket, client_id, client_info)
        # 发送欢迎消息给客户端
        await send_welcome_message(client_websocket, client_id)
        # 打印连接信息
        print(f"New connection from {client_address}")
    except websockets.exceptions.ConnectionClosedError as e:
        # 连接关闭异常处理
        print("连接关闭：", e)
        # 其他处理逻辑，如记录日志、通知相关人员等
    except websockets.exceptions.WebSocketException as e:
        # WebSocket异常处理
        print("WebSocket异常：", e)
        # 其他处理逻辑
    except Exception as e:
        # 处理连接初始化过程中的异常
        print(f"Error handling new connection from {client_address}: {str(e)}")
        await client_websocket.close()


# 处理WebSocket连接，最基本的那个函数
async def handle_connection(websocket, path):
    # 接收客户端的连接请求
    client_id = await websocket.recv()
    # 不知道这里要不要填个数字来限制消息大小
    print(f"New client connected: {client_id}")

    # 添加客户端到字典中
    clients[client_id] = websocket

    # 发送欢迎消息给客户端
    welcome_message = {
        "id": generate_message_id(),
        "type": "system",
        "content": "Welcome to the chat room!"
    }
    await websocket.send(json.dumps(welcome_message))

    # 处理客户端发送的消息
    try:
        async for message in websocket:
            await handle_message(message, connections[websocket]["id"])
    except websockets.exceptions.ConnectionClosedOK:
        # 连接关闭
        await handle_connection_closed(websocket)
    except websockets.exceptions.ConnectionClosed:
        # 连接关闭时的处理
        await handle_connection_closed(websocket)
    finally:
        # 从字典中删除客户端
        del clients[client_id]
        print(f"Client disconnected: {client_id}")

async def handle_connection_closed(client_websocket):
    # 获取客户端ID和地址
    client_id = connections[client_websocket]["id"]
    client_address = connections[client_websocket]["address"]

    # 从连接列表和已连接用户字典中删除客户端
    del connections[client_websocket]
    if client_id in connected_users:
        del connected_users[client_id]

    # 如果该客户端被屏蔽，则从被屏蔽用户字典中删除
    if client_id in blocked_users:
        del blocked_users[client_id]

    # 向其他客户端广播连接关闭的消息
    disconnect_message = {
        "id": generate_message_id(),
        "type": "system",
        "content": f"Client {client_id} has disconnected."
    }
    for client in clients.values():
        await client.send(json.dumps(disconnect_message))

    # 输出连接关闭的消息
    print(f"Client {client_id} disconnected: {client_address}")

    # 关闭 WebSocket 连接
    await client_websocket.close()