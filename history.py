import json
import os

from config import chat_history


# 保存聊天记录到文件
def save_chat_history():
    with open("chat_history.txt", "w") as file:
        for message in chat_history:
            file.write(json.dumps(message) + "\n")


# 加载聊天记录
def load_chat_history():
    if os.path.exists("chat_history.txt"):
        with open("chat_history.txt", "r") as file:
            for line in file:
                message = json.loads(line.strip())
                chat_history.append(message)