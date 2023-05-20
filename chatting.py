import base64
import datetime
import json

import websocket

from config import chat_history, clients, blocked_users, connected_users
from history import save_chat_history


# 生成消息ID
def generate_message_id():
    return str(datetime.datetime.now().timestamp())
# 处理收到的消息
async def handle_message(message, client_id):
    # 解析收到的消息
    try:
        data = json.loads(message)
        msg_type = data["type"]
        content = data["content"]
    except (json.JSONDecodeError, KeyError):
        # 消息解析错误，忽略该消息
        return

    if msg_type == "text":
        # 处理文本消息
        sender = client_id
        timestamp = datetime.datetime.now().timestamp()
        message_id = generate_message_id()

        # 创建文本消息
        text_message = {
            "id": message_id,
            "type": "text",
            "sender": sender,
            "timestamp": timestamp,
            "content": content
        }

        # 保存到聊天记录
        chat_history.append(text_message)
        save_chat_history()

        # 转发消息给其他客户端
        for client in clients.values():
            if client != websocket:
                await client.send(json.dumps(text_message))

    elif msg_type == "image":
        # 处理图片消息
        sender = client_id
        timestamp = datetime.datetime.now().timestamp()
        message_id = generate_message_id()

        # 解码图片数据
        image_data = base64.b64decode(content)

        # 生成图片文件名
        image_filename = f"image_{message_id}.png"

        # 保存图片文件
        with open(image_filename, "wb") as file:
            file.write(image_data)

        # 创建图片消息
        image_message = {
            "id": message_id,
            "type": "image",
            "sender": sender,
            "timestamp": timestamp,
            "content": image_filename
        }

        # 保存到聊天记录
        chat_history.append(image_message)
        save_chat_history()

        # 转发消息给其他客户端
        for client in clients.values():
            if client != websocket:
                await client.send(json.dumps(image_message))

    elif msg_type == "system":
        # 处理系统发送的消息
        system_message = content

        if system_message == "block_user":
            # 屏蔽用户
            blocked_user = client_id
            blocked_users[blocked_user] = True

            # 发送确认消息给客户端
            response = {
                "id": generate_message_id(),
                "type": "system",
                "content": f"You have blocked user: {blocked_user}"
            }
            for client in clients.values():
                if client == websocket:
                    await client.send(json.dumps(response))

        elif system_message == "unblock_user":
            # 解除屏蔽用户
            blocked_user = client_id
            if blocked_user in blocked_users:
                del blocked_users[blocked_user]

            # 发送确认消息给客户端
            response = {
                "id": generate_message_id(),
                "type": "system",
                "content": f"You have unblocked user: {blocked_user}"
            }
            for client in clients.values():
                if client == websocket:
                    await client.send(json.dumps(response))
    elif msg_type == "private":
        # 处理私聊消息
        sender = client_id
        recipient = content.get("recipient", "")
        message_content = content.get("content", "")

        if recipient and message_content:
            await handle_private_message(sender, recipient, message_content)


# 创建私聊消息
def create_private_message(message_id, sender, recipient, content):
    timestamp = datetime.datetime.now().timestamp()

    private_message = {
        "id": message_id,
        "type": "private",
        "sender": sender,
        "recipient": recipient,
        "timestamp": timestamp,
        "content": content
    }

    return private_message


# 发送私聊消息
async def send_private_message(sender, recipient, message):
    # 检查接收者是否在线
    if recipient in connected_users:
        recipient_websocket = connected_users[recipient]
        # 发送私聊消息给接收者
        await recipient_websocket.send(json.dumps(message))
    else:
        print(f"Error: Client {recipient} not found.")

    # 发送私聊消息给发送者
    sender_websocket = connected_users[sender]
    sender_websocket.send(json.dumps(message))


# 发送消息给指定客户端
def send_message_to_client(recipient, message):
    if recipient in clients:
        client_websocket = clients[recipient]
        client_websocket.send(json.dumps(message))
    else:
        print(f"Error: Client {recipient} not found.")


# 处理私聊消息
async def handle_private_message(sender, recipient, content):
    # 创建私聊消息
    message_id = generate_message_id()
    private_message = create_private_message(message_id, sender, recipient, content)

    # 保存到聊天记录
    chat_history.append(private_message)
    save_chat_history()

    # 转发消息给发送者和接收者
    await send_private_message(sender, recipient, private_message)
