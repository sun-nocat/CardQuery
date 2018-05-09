import requests
import datetime
import time
from cardquery import models
from django.http import HttpResponse,HttpResponseRedirect
from django.shortcuts import render
import json

def oauth(request):
    # if models.User.objects.filter()
    getCodeUrl="https://zypc.xupt.edu.cn/oauth/authorize"  # 获取Authorization Code的接口地址
    response_type="code"# 请求类型
    client_id = "7aa91010c59b31f25e56a53a49b517e803395739d8c2deea22672ce5bd7cb751"  # 客户端(一卡通查询)id
    redirect_uri = "http://127.0.0.1:8000/login"  # 成功授权之后的回调地址
    state = "1"  # 客户端的状态
    scope = ""  # 请求用户授权的时候，向用户显示的可进行授权的列表
    URL = getCodeUrl + "?" + "response_type=" + response_type + "&" + "client_id=" + client_id + "&"+"state="+state+"&" +"redirect_uri=" + redirect_uri + "&" + "scope=" + scope
    return HttpResponseRedirect(URL)





#登录接口
#返回登录页面，同时返回验证码和cookie
def login(request):
    try:
        code=request.GET.get("code",None)#获取code
        getTokrnUrl="https://zypc.xupt.edu.cn/oauth/token"  #获取token的接口
        grant_type="authorization_code" #参数
        client_id="7aa91010c59b31f25e56a53a49b517e803395739d8c2deea22672ce5bd7cb751" #客户端id
        client_secret="709d0d088607378cb581628ec9f8347b172485f9e3ca8d7e11d4203411de73fc"#客户端passwd
        redirect_uri="http://127.0.0.1:8000/login"  #重定向地址（上线时需要改）
        #
        #请求地址+参数
        URL=getTokrnUrl + "?" + "grant_type=" + grant_type + "&" + "client_id=" + client_id + "&" +"client_secret="+client_secret+"&"+ "code="+code+"&"+"redirect_uri=" + redirect_uri
        response=requests.post(URL) #发出请求
        text = json.loads(response.text) #将json数据转换为python对象
        access_token=text.get("access_token") #获取access_token
        #
        URL_use="https://zypc.xupt.edu.cn/oauth/userinfo"  #获取用户信息的接口
        URL_user=URL_use+"?"+"access_token=" + access_token  #完整的请求地址+参数
        req=requests.get(URL_user)  #发出请求
        txt=json.loads(req.text)
        # username=txt.get("username") #
        student_no=txt.get("student_no") #获取用户的信息
        request.session['student_no']=student_no  #将用户的卡号保存在session中

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
        if models.User.objects.filter(idserial=student_no):
            res=render(request,"loginNoPasswd.html")
        else:
            res=render(request,"login.html")
        res.set_cookie("name",cookie)
        return res
    except:
        res = render(request, "error.html")
        return res
#登录表单提交接口
#前端传入参数：idserial cardpwd checkcode begindate enddate page
#返回值：如果登录成功，返回登录成功页面
def api_login(request):
    #模拟登录的接口
    loginurl = 'http://172.16.200.7/WebQueryUI/indexAction!userLogin.action'
    idserial = request.session.get('student_no')  # 从session中获取学号
    session = requests.Session()
    if request.method=="POST":
        if models.User.objects.filter(idserial=idserial):
            result=list(models.User.objects.filter(idserial=idserial).values())
            print(result)
            cardpwd=result[0]["cardpwd"]

        else:
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
            if not models.User.objects.filter(idserial=idserial):
                models.User.objects.create(
                    idserial=idserial,
                    cardpwd=cardpwd
                )
            return render(request,"index.html")
        elif msg.get("returncode")=="ERROR":
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
        text=str(response2.text)
        req=json.dumps(text,ensure_ascii=False)
        return HttpResponse(req,content_type="application/json,charset=utf-8")





