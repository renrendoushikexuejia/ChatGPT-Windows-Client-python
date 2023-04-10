版本号: 1.0.0
Chat.ini  文件在当前目录下
key.ini 保存API Key 文件在当前目录下
Chat文件夹 保存聊天记录 聊天记录文件名和会话列表中的文件名一致 每一个会话都用一个单独的json文件保存聊天记录

聊天记录的json文件
{
    "parameters": {
        "requestType": "Completion",
        "model": "text-davinci-003",
        "temperature": 1.0,
        "topP": 1.0,
        "maxTokens": 12,
        "bestOf": 1,
        "n": 1,
        "presencePenalty": 0.0,
        "frequencyPenalty": 0.0,
        "suffix": "",
        "user": "",
        "sessionName": "04101411-HS8T"
    },
    "chat": {
        "message": "...",
        "history": "..."
    }
}

配置文件Chat.ini的结构
{
}

还需要一个文件单独保存API key
{
    key: xxxxxxxxxxxxxxx    保存的API key
}
