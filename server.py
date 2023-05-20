import asyncio

import websockets
import websockets.exceptions
from chatting import handle_message
from config import connections
from connections import handle_connection, receive_system_message, handle_new_connection, handle_connection_closed


# 创建异步事件循环并启动
async def main1():
    async with websockets.serve(handle_connection, 'localhost', 8000):
        while True:
            await receive_system_message()
            await asyncio.sleep(1)  # 控制接收消息的频率


async def start_server():
    # 创建WebSocket服务器
    server = await websockets.serve(handle_connection, "localhost", 8000)
    print("WebSocket server started.")
    await receive_system_message()  # 接收系统消息

    # 接收连接请求并处理连接
    async for client_websocket, client_address in server:
        # 处理新连接
        await handle_new_connection(client_websocket, client_address)
        # 接收和处理消息
        try:
            async for message in client_websocket:
                await handle_message(message, connections[client_websocket]["id"])
        except websockets.exceptions.ConnectionClosed:
            # 连接关闭时的处理
            await handle_connection_closed(client_websocket)
