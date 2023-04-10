# 2023年4月1日19:26:58  写一个ChatGPT PC客户端  通过API连接服务器
# 2023年4月10日13:49:48 ChatCompletion, Completion大致完成
# 1.0.0
import sys,threading,os,json,datetime,time,random,openai,string,glob
from PyQt5.QtWidgets import QMainWindow,QApplication,QMessageBox,QPushButton,QListWidgetItem,QInputDialog,QWidget,QLineEdit
from PyQt5.QtCore import QSize,pyqtSignal
from PyQt5.QtGui import QTextCursor
from Ui_ChatGPTClient import Ui_Frame
from MyLineEdit import MyLineEdit

# 定义全局常量
KEY = ''
INITFLAG = False
# 定义全局函数



class Client( QMainWindow, Ui_Frame): 
    # 定义一个信号,用于子线程给主线程发信号
    signalCrossThread = pyqtSignal(str, str)     #两个str参数,第一个接收信号类型,第二个接收信号内容

    def __init__(self,parent =None):
        global KEY, INITFLAG
        super( Client,self).__init__(parent)
        self.setupUi(self)

        # 初始化界面
        requestType = ['ChatCompletion', 'Completion', 'Edits', 'Images', 'Image edit', 'Image variation',
                       'Embeddings', 'Audio transcription', 'Audio translation']
        self.cbRequestType.addItems(requestType)
        self.mfRequestTypeChanged()
        # 设置会话列表的行高
        self.lwSessions.setUniformItemSizes(True)
        self.tbChat.setReadOnly(False)      # 先把tbChat设置为可编辑  正式发布的时候根据清空,看用不用改过来

        # 设置test按钮 捐赠按钮不可见
        self.btnTest.hide()

        # 先不修改CSS  窗口颜色先不改
        # tbChatCSS = "p { line-height: 30px; }"      #  background-color: gray;
        # self.tbChat.document().setDefaultStyleSheet(tbChatCSS)
        # self.tbChat.setStyleSheet("background-color: rgb(53, 53, 65);")

        #打开配置文件,初始化界面数据
        if os.path.exists( "./Chat.ini"):
            try:
                iniFileDir = os.getcwd() + "\\"+ "Chat.ini"
                with open( iniFileDir, 'r', encoding="utf-8") as iniFile:
                    iniDict = json.loads( iniFile.read())
                if iniDict:
                    # self.sbPanelLX.setValue( iniDict['panelLX'])
                    # 动态添加按钮, 更新聊天框内容
                    pass

                # 用Chat.ini初始化之后, 还要打开key.ini读取key

            except:
                QMessageBox.about( self, "提示", "打开聊天记录文件Chat.ini异常, 软件关闭时会自动重新创建Chat.ini文件")

        # 打开 key.ini  读取API Key
        if os.path.exists( "./key.ini"):
            try:
                keyFileDir = os.getcwd() + "\\"+ "key.ini"
                with open( keyFileDir, 'r', encoding="utf-8") as keyFile:
                    keyDict = json.loads( keyFile.read())
                if keyDict:
                    KEY = keyDict['key']

                # 用Chat.ini初始化之后, 还要打开key.ini读取key

            except:
                QMessageBox.about( self, "提示", "打开存储API Key的key.ini文件失败. 点击API Key按钮输入Key")

        # 在chat文件夹下查找.chat文件. 初始化会话列表lwSessions. 如果没有找到.chat文件,在会话列表中新建一个空的会话
        chatList = [os.path.basename(f) for f in (glob.glob(os.path.join(os.path.abspath('./chat') , '*.chat')))]
        chatList = [s[:-5] for s in chatList]
        if chatList:        # 判断列表不为空
            for i in range(len(chatList)):
                self.mfNewSession()
                tempListWidgetItem = self.lwSessions.item( i)
                tempLineEdit = self.lwSessions.itemWidget( tempListWidgetItem).findChild(MyLineEdit)
                tempLineEdit.setText(chatList[i])

            self.mfOpenSession(len(chatList) -1)
        else:
            self.mfNewSession()


        # 绑定槽函数
        self.btnNewSession.clicked.connect( self.mfNewSession)
        self.btnAPIKey.clicked.connect( self.mfChangeKey)
        self.btnGetModels.clicked.connect(self.mfGetModels)
        self.btnSend.clicked.connect(self.mfSend)
        self.btnStop.clicked.connect(self.mfStop)
        self.cbRequestType.currentIndexChanged.connect(self.mfRequestTypeChanged)
        self.btnDonate.clicked.connect(self.mfHelp)

        self.btnTest.clicked.connect(self.mfChatToMessages)       # 测试按钮 btnTest
        self.signalCrossThread.connect( self.mfSignal)       # 处理子线程给主线程发的信号

        INITFLAG = True     # 初始化已执行完毕
    # 槽函数定义
    # 点击使用帮助
    def mfHelp( self):
        QMessageBox.about( self, '使用帮助', 
        '首次使用请设置API Key\
        \n其他功能我会尽快完善\
        \n\
        \nrenrendoushikexuejia@gmail.com\
        \nhttps://github.com/renrendoushikexuejia\
         '
         )
    
    # 点击会话列表,切换session
    def mfSwitchSession(self):
        self.mfSaveChat()       # 先保存当前界面的内容, 再打开新会话的文件 更新界面
        row = self.lwSessions.indexAt(self.sender().parent().pos()).row()
        self.mfOpenSession(row)
        
    # 当请求类型改变时,同时改变请求类型对应的模型
    def mfRequestTypeChanged(self):        
        self.cbModel.clear()
        requestType = self.cbRequestType.currentText()
        if requestType == 'ChatCompletion':
            self.cbModel.addItems(['gpt-3.5-turbo', 'gpt-4', 'gpt-4-0314', 'gpt-4-32k', 
                                   'gpt-4-32k-0314', 'gpt-3.5-turbo-0301'])
        elif requestType == 'Completion':
            self.cbModel.addItems(['text-davinci-003', 'text-davinci-002', 'text-curie-001', 'text-babbage-001', 
                                   'text-ada-001', 'davinci', 'curie', 'babbage', 'ada'])
        
        
    # 获取可用模型按钮,从OpenAI获取当前可用模型
    def mfGetModels(self):
        global KEY
        if KEY == '':
            QMessageBox.about( self, "提示", "请点击API Key按钮,输入API Key")
        else:
            openai.api_key = KEY
            tempModelsDict = openai.Model.list().to_dict()   
            with open('models.ini', 'w') as f:
                json.dump(tempModelsDict, f, indent=4)
            self.tbChat.append( str(tempModelsDict))
            self.tbChat.append("\n\n模型列表已保存在当前目录下的models.ini文件中")

    # 点击新建会话按钮
    def mfNewSession( self):
        global INITFLAG
        # 根据实例是否初始化过,来判断是否保存当前的界面. 
        # 因为在初始化__init__函数中要调用mfNewSession(),这个时候是不能保存当前界面的,否则.chat文件的内容会被清空
        if INITFLAG == True:
            if self.lwSessions.currentRow() != -1:      # 当前有选中的行
                # print('in new session', self.lwSessions.currentRow())
                self.mfSaveChat()

        # 初始化新建的界面
        self.tbChat.clear()
        self.teMessage.clear()
        # self.cbRequestType.setCurrentText()     # requestType 不改变,延续用户上一个会话的设置
        # self.cbModel.setCurrentText()       # model 不改变,延续用户上一个会话的设置
        self.dsbTemperature.setValue(1)
        self.dsbTopP.setValue(1)
        self.sbMaxTokens.setValue(12)       # 发布时要调整
        self.sbBestOf.setValue(1)       # 发布时要调整
        self.sbN.setValue(1)
        self.dsbPresencePenalty.setValue(0)
        self.dsbFrequencyPenalty.setValue(0)
        self.leSuffix.setText("")
        self.leUser.setText("")
        self.leSystemContent.setText("You are a helpful assistant.")

        tempWidget = QWidget()
        tempWidget.setFixedHeight( 50)
        tempLineEdit = MyLineEdit( tempWidget)      # 这里使用的是 MyLineEdit类
        tempRenameButton = QPushButton( "重命名", tempWidget)
        tempDeleteButton = QPushButton( "删除", tempWidget)

        tempLineEdit.move( 0, 0)
        tempLineEdit.resize( 170, 50)
        tempLineEdit.setReadOnly(True)      # 使名称文本框不可编辑
        font = tempLineEdit.font()      # 设置字体大小
        font.setPointSize(12)
        tempLineEdit.setFont(font)

        timeStr = datetime.datetime.now().strftime("%m%d%H%M")      
        randomStr = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        tempLineEdit.setText(timeStr + '-' + randomStr)     # 新建的会话名称为 时间月日时分-随机4位字符串
        
        tempRenameButton.move( 171, 0)
        tempRenameButton.resize( 50, 50)
        tempDeleteButton.move( 222,0)
        tempDeleteButton.resize( 39, 50)

        tempListWidgetItem = QListWidgetItem()
        tempListWidgetItem.setSizeHint(QSize(100, 50))
        self.lwSessions.addItem(tempListWidgetItem)
        self.lwSessions.setItemWidget(tempListWidgetItem, tempWidget)

        # 新添加的行是最后一行,把最后一行设置为当前选中行
        lastRow = self.lwSessions.count() - 1
        self.lwSessions.setCurrentRow(lastRow)

        # 绑定函数
        tempLineEdit.clicked.connect(self.mfSwitchSession)
        tempRenameButton.clicked.connect(self.mfRename)
        tempDeleteButton.clicked.connect(self.mfDeleteSession)

    # 点击会话列表中的一个会话,读取会话信息,更新聊天记录窗口
    def mfOpenSession(self, row):
        # print('in openSession')
        # row = self.lwSessions.indexAt(self.sender().parent().pos()).row()
        self.lwSessions.setCurrentRow(row)      # 设置当前行为选中状态
        tempListWidgetItem = self.lwSessions.item( row)
        tempLineEdit = self.lwSessions.itemWidget( tempListWidgetItem).findChild(MyLineEdit)
        tempChatName = tempLineEdit.text()
        tempChatDir = './chat/' + tempChatName + '.chat'
        if os.path.exists(tempChatDir):     # 如果chat文件存在
            with open( tempChatDir, 'r', encoding="utf-8") as tempChatFile:
                tempChatDict = json.loads( tempChatFile.read())
            # print( tempChatDict)
            # print(tempChatDict['parameters']['requestType'], tempChatDict['parameters']['model'])

            self.cbRequestType.setCurrentText(tempChatDict['parameters']['requestType'])
            self.mfRequestTypeChanged()
            self.cbModel.setCurrentText(tempChatDict['parameters']['model'])
            self.dsbTemperature.setValue(tempChatDict['parameters']['temperature'])
            self.dsbTopP.setValue(tempChatDict['parameters']['topP'])
            self.sbMaxTokens.setValue(tempChatDict['parameters']['maxTokens'])
            self.sbBestOf.setValue(tempChatDict['parameters']['bestOf'])
            self.sbN.setValue(tempChatDict['parameters']['n'])
            self.dsbPresencePenalty.setValue(tempChatDict['parameters']['presencePenalty'])
            self.dsbFrequencyPenalty.setValue(tempChatDict['parameters']['frequencyPenalty'])
            self.leSuffix.setText(tempChatDict['parameters']['suffix'])
            self.leUser.setText(tempChatDict['parameters']['user'])
            self.teMessage.setPlainText(tempChatDict['chat']['message'])
            self.tbChat.setHtml(tempChatDict['chat']['history'])
            self.leSystemContent.setText(tempChatDict['chat']['systemContent'])
        else:
            self.mfSaveChat()       # 如果文件不存在, 调用mfSaveChat()创建文件




    # 判断一个字符串是否能做windows系统的文件名
    def mfIsValidFileName(self, fileName):
        invalidChars = r'\/:*?"<>|'
        for char in invalidChars:
            if char in fileName:
                return False
        return True

    # 点击会话列表中的重命名按钮, 使lineEdit可以编辑
    def mfRename( self):
        row = self.lwSessions.indexAt(self.sender().parent().pos()).row()
        newName, tempBool = QInputDialog.getText( self, "重命名", "请输入会话名称:") 
        if tempBool:
            if newName != '':
                if self.mfIsValidFileName(newName):
                    tempListWidgetItem = self.lwSessions.item( row)
                    tempLineEdit = self.lwSessions.itemWidget( tempListWidgetItem).findChild(MyLineEdit)
                    originalName = tempLineEdit.text()
                    originalFile = './chat/' + originalName + '.chat'
                    if os.path.exists(originalFile):        # 如果文件存在 同时修改文件名
                        os.rename(originalFile, './chat/' + newName + '.chat')
                    tempLineEdit.setText(newName)
                else:
                    QMessageBox.about( self, "提示", "会话名称不能包含 " + r' \ / : * ? " < > |')
            else:
                QMessageBox.about( self, "提示", "未输入会话名称")

    # 点击会话列表中的删除按钮, 删除对应的行 和 对应的文件
    def mfDeleteSession( self):
        row = self.lwSessions.indexAt(self.sender().parent().pos()).row()
        # 根据行号找到对应的会话名称
        item = self.lwSessions.item(row)
        widget = self.lwSessions.itemWidget(item)
        lineEdit = widget.findChild(MyLineEdit)
        sessionName = lineEdit.text()
        sessionDir = './chat/' + sessionName + '.chat'
        # 判断文件是否存在,文件存在就删掉
        if os.path.exists(sessionDir):
            os.remove(sessionDir)

        self.lwSessions.takeItem( row)

        # 删除会话之后,还要打开最后一个会话 更新界面
        if self.lwSessions.count() == 0:    # 如果所有会话都已经被删除
            self.teMessage.setText("请新建会话或者使用临时会话, 临时会话内容不会被保存")
            self.tbChat.clear()
        else:
            self.mfOpenSession(self.lwSessions.count() -1)



    # 点击API KEY按钮,弹出对话框,输入key,关闭对话框的时候保存key
    def mfChangeKey( self):
        global KEY
        # 返回一个元组，其中第一个元素是用户输入的文本，第二个元素是一个布尔值，表示用户是否点击了确定按钮。
        tempKey, tempBool = QInputDialog.getText( self, "API Key", "请输入你的API Key")     
        if tempBool:
            if tempKey != '':
                KEY = tempKey
                tempKeyDict = {'key':KEY}
                saveKeyJson = json.dumps( tempKeyDict, indent=4)
                try:
                    saveKeyFile = open( "./key.ini", "w",  encoding="utf-8")
                    saveKeyFile.write( saveKeyJson)
                    # saveKeyFile.close()
                except:
                    QMessageBox.about( self, "提示", "保存API key 失败")
                finally:
                    saveKeyFile.close()
            else:
                QMessageBox.about( self, "提示", "API key 格式错误")

    # 保存当前页面的聊天记录和配置
    def mfSaveChat(self):
        # print('in mfSaveChat')
        tempChatDict = {}
        tempChatDict['parameters'] = {}
        tempChatDict['chat'] = {}

        tempChatDict['parameters']['requestType'] = self.cbRequestType.currentText()
        tempChatDict['parameters']['model'] = self.cbModel.currentText()
        tempChatDict['parameters']['temperature'] = self.dsbTemperature.value()
        tempChatDict['parameters']['topP'] = self.dsbTopP.value()
        tempChatDict['parameters']['maxTokens'] = self.sbMaxTokens.value()
        tempChatDict['parameters']['bestOf'] = self.sbBestOf.value()
        tempChatDict['parameters']['n'] = self.sbN.value()
        tempChatDict['parameters']['presencePenalty'] = self.dsbPresencePenalty.value()
        tempChatDict['parameters']['frequencyPenalty'] = self.dsbFrequencyPenalty.value()
        tempChatDict['parameters']['suffix'] = self.leSuffix.text()
        tempChatDict['parameters']['user'] = self.leUser.text()
        tempChatDict['chat']['message'] = self.teMessage.toPlainText()      # 存储发送消息的teMessage中的内容
        tempChatDict['chat']['history'] = self.tbChat.toHtml()      # 保存聊天记录窗口中的内容
        tempChatDict['chat']['systemContent'] = self.leSystemContent.text()       # 保存聊天时的system角色信息

        row = self.lwSessions.currentRow()
        item = self.lwSessions.item(row)
        widget = self.lwSessions.itemWidget(item)
        lineEdit = widget.findChild(MyLineEdit)
        sessionName = lineEdit.text()
        tempChatDict['parameters']['sessionName'] = sessionName


        tempDir = './chat/' + sessionName + '.chat'
        # 下面是正确代码,使用Unicode编码, json文件里的中文显示为\+五位字符  例如"\u662f\u4ec0\u4e48\uff1f\n\n\u6587"
        # 发布时用Unicode, 要支持多语言
        # with open(tempDir, 'w') as f:
        #     json.dump(tempChatDict, f, indent=4)

        #下面是测试代码, 记事本里的中文显示
        with open(tempDir, 'w', encoding='utf-8') as f:
            json.dump(tempChatDict, f, ensure_ascii=False, indent=4)
        
    # 把tbChat中的聊天记录转换成ChatCompletion中的messages参数
    def mfChatToMessages(self):
        history = self.tbChat.toPlainText()
        lines = history.splitlines()
        non_empty_lines = [line for line in lines if line.strip()]
        result = '\n'.join(non_empty_lines)
        results = result.split('->')
        # print(results)
        messagesList = []
        systemContent = self.leSystemContent.text()
        if systemContent:
            messagesList.append({"role": "system", "content": systemContent})

        for tempStr in results:
            if tempStr.startswith('user:  '):
                tempStr = tempStr.split(':  ')[1]
                tempDict = {"role": "user", "content": tempStr}
                messagesList.append(tempDict)
            else:
                if len(tempStr.split(':  ')) > 1:
                    tempStr = tempStr.split(':  ')[1]
                    tempDict = {"role": "assistant", "content": tempStr}
                    messagesList.append(tempDict)
            

        # print(messagesList)
        return messagesList


    # 处理子线程给主线程发的信号, 信号signalType是字符串'QMessageBox' 'Display' 
    def mfSignal( self, signalType, content):
        if signalType == 'QMessageBox':
            QMessageBox.about( self, "提示", content)

        elif signalType == 'Display':
            self.tbChat.append( content)
            
        elif signalType == 'ClearMessage':
            self.teMessage.clear()

    # 退出程序
    def mfQuit( self):
        self.mfSaveChat()
        app = QApplication.instance()
        app.quit()
        
                
    # 点击发送按钮, 创建一个线程, 执行发送请求的任务. 这种方式是为了防止服务器响应太慢 软件会卡住
    def mfSend(self):
        interactionThreading = threading.Thread( target= self.mfRun)
        interactionThreading.start()
        self.btnSend.setText("等待中")
        self.btnSend.setEnabled(False)
        # interactionThreading.join()

    # 点击停止按钮, 使发送按钮可以再次发送消息
    def mfStop(self):
        self.btnSend.setText("发送")
        self.btnSend.setEnabled(True)
    
    # 与服务器交互
    def mfRun(self):
        # 从界面获取参数
        global KEY
        requestType = self.cbRequestType.currentText()
        model = self.cbModel.currentText()
        temperature = self.dsbTemperature.value()
        topP = self.dsbTopP.value()
        maxTokens = self.sbMaxTokens.value()
        bestOf = self.sbBestOf.value()
        n = self.sbN.value()
        presencePenalty = self.dsbPresencePenalty.value()
        frequencyPenalty = self.dsbFrequencyPenalty.value()
        suffix = self.leSuffix.text()
        user = self.leUser.text()
        message = self.teMessage.toPlainText()      # 存储发送消息的teMessage中的内容
        history = self.tbChat.toHtml()      # 保存聊天记录窗口中的内容

        # 判断参数是否符合要求
        if message == '':
            # print( "message is none", message)
            self.btnSend.setText("发送")
            self.btnSend.setEnabled(True)
            return

        if n > bestOf:      # n不能大于bestOf
            self.signalCrossThread.emit( 'QMessageBox', "n不能大于bestOf")
            self.signalCrossThread.emit('ClearMessage', '')
            self.btnSend.setText("发送")
            self.btnSend.setEnabled(True)
            return
        
        if KEY == '':
            self.signalCrossThread.emit( 'QMessageBox', "请点击API Key按钮,输入API Key")
            self.btnSend.setText("发送")
            self.btnSend.setEnabled(True)
            return
        
        openai.api_key = KEY

        # print(KEY)
        # print(requestType)

        #   先不修改CSS
        messageText = '\n->user:  ' + message
        messageHtml = f'<div style="background-color: rgb(53, 53, 65); color: rgb(213, 221, 230); ">{message}</div>'
        self.signalCrossThread.emit('Display', messageText)     # 把发送的消息添加到tbChat聊天记录窗口
        time.sleep(0.2)
        self.signalCrossThread.emit('ClearMessage', '')     # 消息发送之后,清空消息窗口
        # 聊天窗口tbChat滚动到最后一行
        # scrollbar = self.tbChat.verticalScrollBar()
        # scrollbar.setValue(scrollbar.maximum())
        self.tbChat.moveCursor(QTextCursor.End)


        
        # 判断选中的请求类别-------------
        if requestType == 'Completion':
            # try:
            # completion可用模型列表['text-davinci-003', 'text-davinci-002', 'text-curie-001', 'text-babbage-001', 
            #    'text-ada-001', 'davinci', 'curie', 'babbage', 'ada']
            # if model in ['a', 'b', 'c']: 判断语句简单写法
            if model in ['text-davinci-003', 'text-davinci-002']:
                response = openai.Completion.create(model=model, prompt=message, suffix=suffix, max_tokens=maxTokens, 
                                                    temperature=temperature, top_p=topP, n=n, presence_penalty=presencePenalty,
                                                    frequency_penalty=frequencyPenalty, best_of=bestOf, user=user)
                # print(response)
                responseText = model + ':  ' +response['choices'][0]['text'].strip()     
            
            elif model in ['text-curie-001', 'text-ada-001','text-babbage-001', 'curie', 'ada', 'babbage', 'davinci']:    # 不需要suffix
                response = openai.Completion.create(model=model, prompt=message, max_tokens=maxTokens, 
                                                    temperature=temperature, top_p=topP, n=n, presence_penalty=presencePenalty,
                                                    frequency_penalty=frequencyPenalty, best_of=bestOf, user=user)
                # print(response)
                responseText = model + ':  ' +response['choices'][0]['text'].strip()
            
            else:
                # self.signalCrossThread.emit('QMessageBox',  model + " 此功能尚未实现")
                responseText = requestType + ' ' + model + ' 功能尚未实现'


            #   先不修改CSS   # 开头加-> 是为了之后分割语句
            responseTextHtml = f'<div style="background-color: rgb(68, 70, 84); color: rgb(213, 221, 230); ">{responseText}</div>'
            self.signalCrossThread.emit('Display', '->' + responseText)

            # except:
            #     self.signalCrossThread.emit('QMessageBox', "获取消息回复超时, 请检查网络连接")


        elif requestType == 'ChatCompletion':
            # ChatCompletion可用的模型列表 ['gpt-3.5-turbo', 'gpt-4', 'gpt-4-0314', 'gpt-4-32k', 
            #    'gpt-4-32k-0314', 'gpt-3.5-turbo-0301']
            messages = self.mfChatToMessages()
            # messages.append({"role": "user", "content": message})     # 需要发送的消息已经添加到tbChat里面了,不需要再次添加
            # print('messages', messages)
            # print('model', model)
            # print('max tokens', maxTokens)


            if model in ['gpt-3.5-turbo', 'gpt-3.5-turbo-0301']:      # 不需要best_of参数
                response = openai.ChatCompletion.create(model=model, max_tokens=maxTokens, messages=messages,
                                                    temperature=temperature, top_p=topP, n=n, presence_penalty=presencePenalty,
                                                    frequency_penalty=frequencyPenalty, user=user)
                # print(response)
                responseText = model + ':  ' +response['choices'][0]['message']['content'].strip()


            elif model in ['gpt-4', 'gpt-4-0314', 'gpt-4-32k', 'gpt-4-32k-0314',]:
                responseText = requestType + ' ' + model + ' 功能尚未实现'
            else:
                responseText = requestType + ' ' + model + ' 功能尚未实现'

            #   先不修改CSS   # 开头加-> 是为了之后分割语句
            responseTextHtml = f'<div style="background-color: rgb(68, 70, 84); color: rgb(213, 221, 230); ">{responseText}</div>'
            self.signalCrossThread.emit('Display', '->' + responseText)

        else:
            responseText = requestType + ' 功能尚未实现'
            self.signalCrossThread.emit('Display', '->' + responseText)


        # 更新界面
        # print('over ?')
        # 聊天窗口tbChat滚动到最后一行
        # scrollbar = self.tbChat.verticalScrollBar()
        # scrollbar.setValue(scrollbar.maximum()+50)
        self.tbChat.moveCursor(QTextCursor.End)
        self.btnSend.setText("发送")
        self.btnSend.setEnabled(True)



#主程序入口
if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWin = Client()
    myWin.show()

    appExit = app.exec_()
    #退出程序之前,保存界面上的设置
    if myWin.lwSessions.count() > 0:
        myWin.mfSaveChat()

    tempDict = { }
    saveIniJson = json.dumps( tempDict, indent=4)
    try:
        saveIniFile = open( "./Chat.ini", "w",  encoding="utf-8")
        saveIniFile.write( saveIniJson)
        saveIniFile.close()
    except:
        QMessageBox.about( myWin, "提示", "保存配置文件Chat.ini失败")

    sys.exit( appExit)
# sys.exit(app.exec_())  