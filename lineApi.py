from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)
from sqlite import Sqlite3
import datetime
import time
import json

app = Flask(__name__)
sql = Sqlite3()

with open('secure.key') as data_file:
    data = json.load(data_file)

line_bot_api = LineBotApi(data["Channel Access Token"])
handler = WebhookHandler(data["Channel Secret"])

helpMessage = '''你可以用 'help' 印出本訊息
\ud83d\udccc '本月'
<本月 xx度>
  更新本月電度數
<本月>
  印出本月房租
\ud83d\udccc '更新'
<更新 本月 xx度>
<更新 上月 xx度>
<更新 x月 xx度>
  更新之前月份的度數'''

@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    print(event)
    if event.message.type is "text":
        if event.message.text == "help":
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=helpMessage))
        elif event.message.text.strip().startswith("本月"):
            thisMonth(event)
        elif event.message.text.strip().startswith("更新"):
            updateBefore(event)

def thisMonth(event):
    months = datetime.datetime.now().strftime("%Y%m")
    existedMonthly = sql.fetchMonthly(event.source.user_id, months)
    lastMonthly = sql.fetchMonthly(event.source.user_id,lastMonths(months)) 
    if "度" in event.message.text:
        monthlyDic = {}
        monthlyDic['kwh'] = int(event.message.text.replace(" ","").replace("本月","").replace("度",""))
        monthlyDic['months'] = months
        monthlyDic['timestamp'] = str(int(time.time()))
        monthlyDic['price'] = 5.5
        monthlyDic['userId'] = event.source.user_id
        print(monthlyDic)
    #本月xxx度
        if existedMonthly:
        #已有資料且match
            if existedMonthly[3] == monthlyDic['kwh']:
                printRent(event.reply_token, existedMonthly, lastMonthly)
        #新資料與舊資料衝突
            else:
                replyMessage(event.reply_token, "這個月是%d度電\n錯誤請用 '更新' 功能" % existedMonthly[3])
        #沒有舊資料，新增後印出
        else:
            sql.insertMonthly(monthlyDic)
            existedMonthly = sql.fetchMonthly(event.source.user_id, months)
            printRent(event.reply_token, existedMonthly, lastMonthly)
    #直接印出
    elif event.message.text == "本月":
        if existedMonthly:
            printRent(event.reply_token, existedMonthly, lastMonthly)
        else:
        #本月沒資料，印上個月
            last2Monthly = sql.fetchMonthly(event.source.user_id,lastMonths(lastMonths(months)))
            printRent(event.reply_token, lastMonthly, last2Monthly)

def updateBefore(event):
    nowYear = int(datetime.datetime.now().strftime("%Y"))
    nowMonth = int(datetime.datetime.now().strftime("%m"))
    if "度" in event.message.text and "月" in event.message.text:
        command = event.message.text.replace(" ","")
        month = command.replace("更新","").split("月")[0]
        year = nowYear
    #確認月份
        if month.isnumeric():
            if int(month) > 12 or int(month) <= 0:
                replyMessage(event.reply_token,"別開玩笑了！我不懂%s月" % month)
                return
    #也可以用"本"&"上"
        elif month != "本" and month != "上":
            print(month)
            replyMessage(event.reply_token,"別開玩笑了！我不懂%s月" % month)
            return
        #更新上個月
        if month == "上" or (month.isnumeric() and int(month) == nowMonth - 1):
            months = lastMonths("%04d%02d" % (year, nowMonth))
            year = int(months[0:4])
            month = int(months[4:6])
        #更新去年的,比目前大的月份
        elif month.isnumeric() and int(month) > nowMonth:
            existedMonthly = sql.fetchMonthly(event.source.user_id, "%4d%02d" % (nowYear-1, int(month)))
            if not existedMonthly:
                replyMessage(event.reply_token, "更新失敗！\n去年%s月沒有資料" % month)
                return
            else:
                year = nowYear - 1
        #更新比目前小的月份
        elif month.isnumeric() and int(month) < nowMonth:
            year = nowYear
        #更新這個月
        elif (month.isnumeric() and int(month) == nowMonth) or month == "本":
            month = nowMonth
            year = nowYear
#check kwh
        kwh = command.replace("更新","").split("月")[1].split("度")[0]
        if not kwh.isnumeric():
            replyMessage(event.reply_token,"你給我翻譯翻譯什麼叫%s度" % kwh)
            return
        lastMonthsString = lastMonths("%04d%02d" % (year, int(month)))
        lastmonthYear = lastMonthsString[0:4]
        lastMonth = lastMonthsString[4:6]
    #確認沒有比上月多
        lastMonthData = sql.fetchMonthly(event.source.user_id, lastMonthsString) 
        if lastMonthData:
            if lastMonthData[3] > int(kwh):
                replyMessage(event.reply_token,"最好是%s月比%s月多\n%s月%d度\n%s月%d度(騙人)" % (lastMonth, month, lastMonth, lastMonthData[3], month, int(kwh)))
                return
        thisMonthData = sql.fetchMonthly(event.source.user_id, "%4d%02d" % (year, int(month)))
    #過去有資料，做更新，如果剛好是本月然後印出房租
        if thisMonthData:
            sql.updateKwhWithUserIdMonths(int(kwh), event.source.user_id, "%4d%02d" % (year, int(month)))
            if ("%04d%02d" % (nowYear, nowMonth)) == ("%4d%02d" % (year, int(month))):
                savedData = sql.fetchMonthly(event.source.user_id, "%4d%02d" % (year, int(month)))
                printRent(event.reply_token, savedData, lastMonthData)
            else:
                replyMessage(event.reply_token,"之前%s月是%d度\n更新為%d度\u26a1\ufe0f" % (month, thisMonthData[3], int(kwh)))
    #要更新的這個月有沒有舊資料，如果剛好是本月就印出房租
        else:
            monthlyDic = {}
            monthlyDic['kwh'] = int(kwh)
            monthlyDic['months'] = "%4d%02d" % (year, int(month))
            monthlyDic['timestamp'] = str(int(time.time()))
            monthlyDic['price'] = 5.5
            monthlyDic['userId'] = event.source.user_id
            sql.insertMonthly(monthlyDic)
            if ("%04d%02d" % (nowYear, nowMonth)) == ("%4d%02d" % (year, int(month))):
                savedData = sql.fetchMonthly(event.source.user_id, "%4d%02d" % (year, int(month)))
                printRent(event.reply_token, savedData, lastMonthData)
            else:
                replyMessage(event.reply_token,"沒有%s月資料，更新為%s度\u26a1\ufe0f" % (month, kwh))

def lastMonths(months):
    if len(months) != 6 and not months.isnumeric():
        return "0"
    year = int(months[0:4])
    month = int(months[4:6])
    #print("year:%d month:%d" % (year, month))
    if month == 1:
        year = year - 1
        month = 12
    else:
        month = month - 1
    return "%04d%02d" % (year, month)
    
def printRent(replyToken, thisMonthly, lastMonthly):
    if lastMonthly:
        thisMonthKwh = thisMonthly[3]
        lastMonthKwh = lastMonthly[3]
        deltaKwh = thisMonthKwh - lastMonthKwh
        thisMonthDate = thisMonthly[2]
        year = int(thisMonthDate[0:4])
        month = int(thisMonthDate[4:6])
        rentInfo = "--%d/%d月份--\n電錶%d度-上期%d度=%d度\n%d度*5.5元=%.0d元\n+公區費%d元\n+房租9000元\n=合計%d元" % (year, month, thisMonthKwh, lastMonthKwh, deltaKwh, deltaKwh, deltaKwh * 5.5, deltaKwh, 9000 + (deltaKwh * 5.5) + deltaKwh)
        replyMessage(replyToken, rentInfo)
    else:
        replyMessage(event.reply_token, "本月%d度，但沒有上個月資料比對", thisMonthly[3]) 
        return

def replyMessage(replyToken, message):
    line_bot_api.reply_message(replyToken, TextSendMessage(text=message))

if __name__ == "__main__":
    context = ('dnhuang.me.crt','dnhuang.me.key')
    app.run(host='0.0.0.0', port='8000', ssl_context=context)

