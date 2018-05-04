import requests
from django.http import HttpResponse,HttpResponseRedirect
from django.shortcuts import render
import json
import datetime
import time
import sys
from cardquery import models



#登录接口
#返回登录页面，同时返回验证码和cookie
def login(request):
    #创建session,用来模拟登录
    session = requests.Session()
    # 图片验证码的URL
    captchaurl = 'http://172.16.200.7/WebQueryUI/servlet/AuthImageServlet'
    # 构建请求头
    headers = {
        "Referer": "http://172.16.200.7/WebQueryUI/",
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87'

    }
    # 发出第一次请求获取验证码
    checkcodecontent = session.get(captchaurl, headers=headers)
    # 从返回信息中获取cookie的值
    cookies = requests.utils.dict_from_cookiejar(session.cookies)
    cookie=cookies.get('JSESSIONID')
    # 将获取到的验证码保存在本地
    with open('static/img/chckcode.jpg', 'wb') as f:
        f.write(checkcodecontent.content)
        f.close()
    #返回页面和cookie
    res=render(request,"login.html")
    res.set_cookie("name",cookie)
    return res

#登录表单提交接口
#前端传入参数：idserial cardpwd checkcode begindate enddate page
#返回值：如果登录成功，返回登录成功页面
def api_login(request):
    #模拟登录的接口
    loginurl = 'http://172.16.200.7/WebQueryUI/indexAction!userLogin.action'
    session = requests.Session()
    if request.method=="POST":
        idserial=request.POST.get("idserial",None)
        cardpwd=request.POST.get("cardpwd",None)
        checkcode=request.POST.get("checkcode",None)

        # 获取模拟登录所需要的cookie
        cookie1=request.COOKIES.get("name",None)
        cookie="JSESSIONID="+cookie1
        headers = {
            "Referer": "http://172.16.200.7/WebQueryUI/",
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87',
            "Cookie":cookie,

        }
        data = {
            'paramMap.idserial': idserial,
            'paramMap.cardpwd': cardpwd,
            "paramMap.checkcode": checkcode,
            "paramMap.way": "w1"
        }
        #进行模拟登录，
        response=session.post(loginurl,headers=headers,data=data)
        status=str(response.status_code)
        msg=json.loads(response.text)
        if status=="200" and msg.get("returncode")=="SUCCESS":
            # 将用户的信息存储到数据库中
            models.User.objects.create(
                idserial=idserial,
                cardpwd=cardpwd
            )
            print(msg)
            print("服务端返回码 = " + str(response.status_code))
            print("服务端text = " + str(response.text))  # 为空表示登录成功
            return render(request,"index.html")
        elif msg.get("returncode")=="ERROR":
            print(msg)
            print("服务端返回码 = " + str(response.status_code))
            print("服务端text = " + str(response.text))  # 为空表示登录成功
            return render(request,"error.html")



#/////////////////////////// /.///

def api_find(request):
    if request.method=="POST":
        session = requests.Session()
        score_url = 'http://172.16.200.7/WebQueryUI/card/selfTradeAction!getSelfTradeList.action'
        cookie1=request.COOKIES.get("name",None)
        # 获取cookie和从session中获取分页的信息
        cookie="JSESSIONID="+cookie1

        begindate=request.POST.get("begindate",None)
        enddate=request.POST.get("enddate",None)
        page=request.POST.get("page",None)
        if begindate==None:
            t = datetime.datetime.now()
            t1 = datetime.timedelta(weeks=-4)
            lala = t + t1
            enddate = t.date()
            begindate = lala.date()
            page=1
            print(begindate)

        headers1={
            "Referer": "http://172.16.200.7/WebQueryUI/card/  selfTrade.html",
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.186 Safari/537.36',
            'Host':'172.16.200.7',
            "Accept-Language": "zh-CN",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Origin": "http://172.16.200.7",
            'X-Requested-With':'XMLHttpRequest',
            "Pragma": "no-cache",
            "Cookie":cookie,
        }
        pay={
            'paramMap.begindate': begindate,
            'paramMap.enddate': enddate,
            "paramMap.page": page,
            "paramMap.tradetype": 1
        }
        time.sleep(1)
        response2=session.post(score_url,headers=headers1,data=pay)
        print("服务端返回码 = "+str(response2.status_code))
        print("服务端url = "+str(response2.url))
        print("服务端text = "+str(response2.text))  #为空表示登录成功
        text=str(response2.text)
        req=json.dumps(text,ensure_ascii=False)
        return HttpResponse(req,content_type="application/json,charset=utf-8")





