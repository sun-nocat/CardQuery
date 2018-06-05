import requests
import datetime
import time
from collections import Counter
from cardquery import models
from django.http import HttpResponse,HttpResponseRedirect
from django.shortcuts import render
import json
import isort

#返回主页面
def api_index(request):
    return render(request, "index.html")




#进行oauth认证，
#重定向到西邮社区认证页面。请求用户授权，授权之后重定向到登录界面
def oauth(request):
    getCodeUrl="https://zypc.xupt.edu.cn/oauth/authorize" #获取Code的接口地址
    response_type="code" # 请求类型
    client_id = "7aa91010c59b31f25e56a53a49b517e803395739d8c2deea22672ce5bd7cb751" #客户端(一卡通查询)id
    redirect_uri = "http://127.0.0.1:8000/login" #授权成功之后的回调地址（上线需要更改）
    state = "1" #客户端的状态
    scope = "" #请求用户授权的时候，向用户显示的可进行授权的列表
    URL = getCodeUrl + "?" + "response_type=" + response_type + "&" + "client_id=" + client_id + "&"+"state="+state+"&" +"redirect_uri=" + redirect_uri + "&" + "scope=" + scope
    return HttpResponseRedirect(URL) #重定向到认证页面




#用户授权之后的回调接口（由认证服务器完成回调）
#参数：认证通过之后url中的code参数
#功能：1获取用户信息，2模拟登陆，获取验证码和cookie，3返回相应的页面
def login(request):
    getTokrnUrl = "https://zypc.xupt.edu.cn/oauth/token" #获取token的接口
    grant_type = "authorization_code" #参数
    client_id = "7aa91010c59b31f25e56a53a49b517e803395739d8c2deea22672ce5bd7cb751" #客户端id
    client_secret = "709d0d088607378cb581628ec9f8347b172485f9e3ca8d7e11d4203411de73fc" #客户端passwd
    URL_use = "https://zypc.xupt.edu.cn/oauth/userinfo"  # 获取用户信息的接口
    session = requests.Session()  # 创建session,用来模拟登录
    redirect_uri = "http://127.0.0.1:8000/login" #重定向地址（上线时需要改）
    captchaurl = 'http://172.16.200.7/WebQueryUI/servlet/AuthImageServlet'  # 图片验证码的URL(上线时需要更改)
    headers = {
        "Referer": "http://172.16.200.7/WebQueryUI/",
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87'
    }  # 构建请求头（上线时需要更改
    try:
        code=request.GET.get("code",None) #从回调URL中获取code
        if code==None: #如果code不存在,说明用户未授权，返回授权失败页面
            return render(request,"oauthError.html")
        URL = getTokrnUrl + "?" + "grant_type=" + grant_type + "&" + "client_id=" + client_id + "&" + "client_secret=" + client_secret + "&" + "code=" + code + "&" + "redirect_uri=" + redirect_uri  # 请求地址+参数
        response=requests.post(URL) #模拟登录，获取token
        text = json.loads(response.text) #将获取到的json数据转换为python对象
        access_token=text.get("access_token",None) #获取token
        if access_token!=None: #如果获取到token
            URL_user=URL_use+"?"+"access_token=" + access_token #获取用户信息，完整的请求地址+参数
            req=requests.get(URL_user)#获取用户信息
            txt=json.loads(req.text)
            student_no=txt.get("student_no",None) #获取用户的信息
            if student_no != None: #如果获取到了用户信息
                request.session['student_no'] = student_no  #将用户的卡号保存在session中
                checkcodecontent = session.get(captchaurl, headers=headers)  # 模拟登陆，发出第一次请求获取验证码
                cookies = requests.utils.dict_from_cookiejar(session.cookies)
                cookie = cookies.get('JSESSIONID', None)  # 从返回信息中获取cookie的值
                with open('static/img/chckcode.jpg', 'wb') as f:  # 将获取到的验证码保存在本地
                    f.write(checkcodecontent.content)
                    f.close()
                if models.User.objects.filter(idserial = student_no) and cookie != None:   # 返回页面和cookie
                    res = render(request, "loginNoPasswd.html")
                else:
                    res = render(request, "login.html")
                res.set_cookie("name", cookie)
                return res
            else:
                return render(request,"oauthError.html")
        else:
            if models.User.objects.filter(idserial=request.session.get('student_no',None)):
                return render(request,"loginNoPasswd.html")
            else: 
                return render(request, "login.html")
    except:
        # res = render(request, "error.html")
        # return res
        return HttpResponseRedirect("/oauth")


#登录表单提交接口
#前端传入参数：idserial cardpwd checkcode begindate enddate page
#返回值：如果登录成功，返回登录成功页面
def api_check(request):
    loginurl = 'http://172.16.200.7/WebQueryUI/indexAction!userLogin.action' #模拟登录的接口(上线需要更改)
    idserial = request.session.get('student_no',None)  #从session中获取学号
    session = requests.Session()
    if request.method=="POST":
        if idserial!=None:
            if models.User.objects.filter(idserial=idserial):
                result=list(models.User.objects.filter(idserial=idserial).values())
                cardpwd=result[0]["cardpwd"] #获取用户的密码
            else:
                cardpwd=request.POST.get("cardpwd",None)
            checkcode=request.POST.get("checkcode",None)
        else:
            re = json.dumps({
                "status": 1,
                "msg": "从session获取一卡通账号失败",
                "data": "",
            })
            return HttpResponse(re, content_type="application/json")
        cookie1=request.COOKIES.get("name",None) #获取模拟登录所需要的cookie
        if cookie1!=None:
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

            response=session.post(loginurl,headers=headers,data=data) #进行模拟登录，
            status=str(response.status_code)
            msg=json.loads(response.text)
            if status=="200" and msg.get("returncode")=="SUCCESS":#如果登录成功
                if not models.User.objects.filter(idserial=idserial): # 将用户的信息存储到数据库中
                    models.User.objects.create(
                        idserial=idserial,
                        cardpwd=cardpwd
                    )

                re = json.dumps({
                    "status": 0,
                    "msg": "用户登录成功",
                    "data":idserial,
                })

                # return HttpResponse(re, content_type="application/json") #测试使用，上线需要取点注释
                return render(request,"index.html")  #测试使用

            elif msg.get("returncode")=="ERROR":
                if models.User.objects.filter(idserial=idserial):
                    re = json.dumps({
                        "status": 1,
                        "msg": "验证码错误",
                        "data":"",
                    })
                    return HttpResponse(re, content_type="application/json")
                else:
                    re = json.dumps({
                        "status": 1,
                        "msg": "用户名或验证码错误",
                        "data":"",
                    })
                    return HttpResponse(re, content_type="application/json")
            else:
                re = json.dumps({
                    "status": 1,
                    "msg": "登录失败,请联系管理员",
                    "data":"",
                })
                return HttpResponse(re, content_type="application/json")
        else:
            return HttpResponseRedirect("/oauth")
    else:
        return HttpResponseRedirect("/oauth")



'''
返回给前端最近的10条消费信息
前端请求类型--post请求
从一个月的数据中返回前十条数据
'''


def api_getNewData(request):
    if request.method=="POST":
        session = requests.Session()
        score_url = 'http://172.16.200.7/WebQueryUI/card/selfTradeAction!getSelfTradeList.action'
        cookie1=request.COOKIES.get("name",None) #获取cookie
        cookie="JSESSIONID="+cookie1 #生成模拟登录需要的cookie

        begindate=request.POST.get("begindate",None)
        enddate=request.POST.get("enddate",None)
        page=str(request.POST.get("page",None))
        # count = request.POST.get("count",None)  #获取参数count
        if begindate==None or enddate==None or page==None: #如果未获取到查询时间和分页信息，则进行查询最新10条数据
            t = datetime.datetime.now() #获取目前时间
            t1 = datetime.timedelta(weeks=-4)
            begin = t + t1 #获取当前时间之前的4周时间
            enddate = t.date()
            begindate = begin.date()
            page=1 #查询第一页，获取最新的数据

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

        response2=session.post(score_url,headers=headers1,data=pay) #模拟登录，获取流水信息
        dicttext=json.loads(response2.text) #将json格式转化为字典格式
        data=dicttext.get("tradelist") #最终返回的数据，dict格式

# 数据处理


        all = 0 #保存花费总和
        codelist = []  #保存记录中的poscode
        data2={}  #保存排序后数据
        allD=0 #东升苑消费总和
        allX=0 #旭日苑消费总和
        allM=0 #美广消费总和
        allQ=0 #其他。。。
        allS=0 #商店的花费总和
        dir={} #将所有地方的消费总和放一起
        for i in range(len(data)):
            all = all + abs(float(data[i].get("txamt")))  # 使用all保存计算之后的用户周消费总和。
            codelist.append(data[i].get("poscode"))   #将消费的pos机编号存在一个列表中

            shopname = list(models.List.objects.filter(lid=data[i].get('poscode')).values())
            if len(shopname) != 1:
                name = "无"
            else:
                name = str(shopname[0].get('dir'))
            lists=['0241','0242','0243','0244','0245','0249','0250','0251','0258','0501','0355','0354','0361','0075','0356','0076']  #商店的poscode列表
            if data[i].get('poscode') in lists:
                allS = allS + abs(float(data[i].get("txamt")))

            if name == "东升苑" and data[i].get('poscode') not in lists:
                allD = allD + abs(float(data[i].get("txamt")))
            elif name=="旭日苑" and data[i].get('poscode') not in lists:
                allX = allX + abs(float(data[i].get("txamt")))
            elif name == "美广" and data[i].get('poscode') not in lists:
                allM = allM + abs(float(data[i].get("txamt")))
            elif data[i].get('poscode') not in lists:
                allQ = allQ + abs(float(data[i].get("txamt")))

        dir["旭日苑"]=allX
        dir["东升苑"] = allD
        dir["美广"] = allM
        dir["其他"] = allQ
        dir["商店"] = allS

        a=Counter(codelist)  #将数据进行统计
        b = sorted(a.items(),key=lambda x:x[1],reverse=True)  #将统计过的数据进行排序
        toplist = []
        for i in range(b.__len__()):#获取到吃的最多的档口的poscode  和次数
            data2["time"]=b[i][1]  #将次数保存下来
            eatsum = 0
            for j in range(len(data)): #遍历流水信息
                code = str((data[j].get("poscode"))) #获取流水信息中的poscode
                if code ==b[i][0]: #找到消费最多的档口   ---==0355
                    name1 = list(models.List.objects.filter(lid=code).values()) #数据库中查询对应信息
                    if len(name1)!=1:
                        data2["shopname"]='无'
                    else:
                        data2["shopname"]=name1[0].get('shop')  #将档口名保存
                    eatsum=eatsum+abs(float(data[j].get("txamt"))) #统计消费总和
                data2["sum"]=eatsum  #将消费总和保存起来
            toplist.append(data2.copy())

        #-----将查询到的具体店名的信息插入到返回数据中
        for i in range(len(data)):
            shopname = list(models.List.objects.filter(lid=data[i].get('poscode')).values())
            # dirname = list(models.List.objects.filter(li))
            if len(shopname)!=1:
                dirshop = "无"
                name = "无"
            else:
                name = shopname[0].get('shop')
                dirshop = shopname[0].get('dir')

            dict2 = {'shopname':name,'dir':dirshop}
            data1= dict(data[i], **dict2)
            data[i]=data1

#数据处理结束

        re = json.dumps({
            "status": 0,
            "msg": "查询成功！",
            "cost":all,
            "data": data,
            "dirlist":[dir],
            "toplist":top(toplist)

        })
        return HttpResponse(re,content_type="application/json,charset=utf-8")
    else:
        re = json.dumps({
            "status": 1,
            "msg": "请使用post请求",
            "data": "",}
        )
        return HttpResponse(re, content_type="application/json")


'''
调用接口，返回一周的数据，如果今天是周天则返回周一到周天的数据，如果今天是周一，那就返回周一的数据

参数，count=1-----返回一周数据中的消费记录的和
      count=0------返回一周的所有数据  
'''
def api_getOneWeekData(request):
    if request.method=="POST":
        # count=request.POST.get("count",None) #从前端获取到参数，确定是返回所有数据还是计算数据之后然后返回。
        session = requests.Session()
        score_url = 'http://172.16.200.7/WebQueryUI/card/selfTradeAction!getSelfTradeList.action'
        cookie1=request.COOKIES.get("name",None) # 获取cookie和从session中获取分页的信息
        cookie="JSESSIONID="+cookie1
        nowdata = (str(datetime.datetime.now().date()))#获取当前时间
        begindate=getThisWeek(nowdata)
        enddate=nowdata
        print(begindate)
        print(enddate)
        page = 0 #分页为0表示不进行分页，一次获取所有的数据
        headers1 = {
            "Referer": "http://172.16.200.7/WebQueryUI/card/  selfTrade.html",
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.186 Safari/537.36',
            'Host': '172.16.200.7',
            "Accept-Language": "zh-CN",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Origin": "http://172.16.200.7",
            'X-Requested-With': 'XMLHttpRequest',
            "Pragma": "no-cache",
            "Cookie": cookie,
        }
        pay = {
            'paramMap.begindate': begindate,
            'paramMap.enddate': enddate,
            "paramMap.page": page,
            "paramMap.tradetype": 1
        }
        response2=session.post(score_url,headers=headers1,data=pay) #模拟登录，获取流水信息
        dicttext=json.loads(response2.text) #将json格式转化为字典格式
        data=dicttext.get("tradelist") #最终返回的数据，dict格式



        all = 0 #保存花费总和
        codelist = []  #保存记录中的poscode
        data2={}  #保存排序后数据
        allD=0 #东升苑消费总和
        allX=0 #旭日苑消费总和
        allM=0 #美广消费总和
        allQ=0 #其他。。。
        allS=0 #商店的花费总和
        dir={} #将所有地方的消费总和放一起
        for i in range(len(data)):
            all = all + abs(float(data[i].get("txamt")))  # 使用all保存计算之后的用户周消费总和。
            codelist.append(data[i].get("poscode"))   #将消费的pos机编号存在一个列表中

            shopname = list(models.List.objects.filter(lid=data[i].get('poscode')).values())
            if len(shopname) != 1:
                name = "无"
            else:
                name = str(shopname[0].get('dir'))
            lists=['0241','0242','0243','0244','0245','0249','0250','0251','0258','0501','0355','0354','0361','0075','0356','0076']  #商店的poscode列表
            if data[i].get('poscode') in lists:
                allS = allS + abs(float(data[i].get("txamt")))

            if name == "东升苑" and data[i].get('poscode') not in lists:
                allD = allD + abs(float(data[i].get("txamt")))
            elif name=="旭日苑" and data[i].get('poscode') not in lists:
                allX = allX + abs(float(data[i].get("txamt")))
            elif name == "美广" and data[i].get('poscode') not in lists:
                allM = allM + abs(float(data[i].get("txamt")))
            elif data[i].get('poscode') not in lists:
                allQ = allQ + abs(float(data[i].get("txamt")))

        dir["旭日苑"]=allX
        dir["东升苑"] = allD
        dir["美广"] = allM
        dir["其他"] = allQ
        dir["商店"] = allS

        a=Counter(codelist)  #将数据进行统计
        b = sorted(a.items(),key=lambda x:x[1],reverse=True)  #将统计过的数据进行排序
        toplist = []
        for i in range(b.__len__()):#获取到吃的最多的档口的poscode  和次数
            data2["time"]=b[i][1]  #将次数保存下来
            eatsum = 0
            for j in range(len(data)): #遍历流水信息
                code = str((data[j].get("poscode"))) #获取流水信息中的poscode
                if code ==b[i][0]: #找到消费最多的档口   ---==0355
                    name1 = list(models.List.objects.filter(lid=code).values()) #数据库中查询对应信息
                    if len(name1)!=1:
                        data2["shopname"]='无'
                    else:
                        data2["shopname"]=name1[0].get('shop')  #将档口名保存
                    eatsum=eatsum+abs(float(data[j].get("txamt"))) #统计消费总和
                data2["sum"]=eatsum  #将消费总和保存起来
            toplist.append(data2.copy())

        #-----将查询到的具体店名的信息插入到返回数据中
        for i in range(len(data)):
            shopname = list(models.List.objects.filter(lid=data[i].get('poscode')).values())
            # dirname = list(models.List.objects.filter(li))
            if len(shopname)!=1:
                dirshop = "无"
                name = "无"
            else:
                name = shopname[0].get('shop')
                dirshop = shopname[0].get('dir')

            dict2 = {'shopname':name,'dir':dirshop}
            data1= dict(data[i], **dict2)
            data[i]=data1

        re = json.dumps({
            "status": 0,
            "msg": "查询成功！",
            "cost":all,
            "data": data,
            "dirlist":[dir],
            "toplist":top(toplist)

        })
        return HttpResponse(re,content_type="application/json,charset=utf-8")

    else:
        re = json.dumps({
            "status": 1,
            "msg": "请使用post请求",
            "data": "",
        })
        return HttpResponse(re, content_type="application/json")













'''
调用接口，返回一月的数据，如果今天是30号则返回这个月1号到30号的数据，如果今天是1号，那就返回1号的数据

参数，count=1-----返回每月1号到目前时间点的数据中的消费记录的和
      count=0------返回每月1号到现在的所有数据  
'''
def api_getOneMonthData(request):
    if request.method=="POST":

        session = requests.Session()
        score_url = 'http://172.16.200.7/WebQueryUI/card/selfTradeAction!getSelfTradeList.action'
        cookie1=request.COOKIES.get("name",None) # 获取cookie和从session中获取分页的信息
        cookie="JSESSIONID="+cookie1
        nowdata = (str(datetime.datetime.now().date()))#获取当前时间
        begindate=getOneMonth()
        enddate=nowdata

        page = 0
        headers1 = {
            "Referer": "http://172.16.200.7/WebQueryUI/card/  selfTrade.html",
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.186 Safari/537.36',
            'Host': '172.16.200.7',
            "Accept-Language": "zh-CN",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Origin": "http://172.16.200.7",
            'X-Requested-With': 'XMLHttpRequest',
            "Pragma": "no-cache",
            "Cookie": cookie,
        }
        pay = {
            'paramMap.begindate': begindate,
            'paramMap.enddate': enddate,
            "paramMap.page": page,
            "paramMap.tradetype": 1
        }
        response2=session.post(score_url,headers=headers1,data=pay) #模拟登录，获取流水信息
        dicttext=json.loads(response2.text) #将json格式转化为字典格式
        data=dicttext.get("tradelist") #最终返回的数据，dict格式



        all = 0 #保存花费总和
        codelist = []  #保存记录中的poscode
        data2={}  #保存排序后数据
        allD=0 #东升苑消费总和
        allX=0 #旭日苑消费总和
        allM=0 #美广消费总和
        allQ=0 #其他。。。
        allS=0 #商店的花费总和
        dir={} #将所有地方的消费总和放一起
        for i in range(len(data)):
            all = all + abs(float(data[i].get("txamt")))  # 使用all保存计算之后的用户周消费总和。
            codelist.append(data[i].get("poscode"))   #将消费的pos机编号存在一个列表中

            shopname = list(models.List.objects.filter(lid=data[i].get('poscode')).values())
            if len(shopname) != 1:
                name = "无"
            else:
                name = str(shopname[0].get('dir'))
            lists=['0241','0242','0243','0244','0245','0249','0250','0251','0258','0501','0355','0354','0361','0075','0356','0076']  #商店的poscode列表
            if data[i].get('poscode') in lists:
                allS = allS + abs(float(data[i].get("txamt")))

            if name == "东升苑" and data[i].get('poscode') not in lists:
                allD = allD + abs(float(data[i].get("txamt")))
            elif name=="旭日苑" and data[i].get('poscode') not in lists:
                allX = allX + abs(float(data[i].get("txamt")))
            elif name == "美广" and data[i].get('poscode') not in lists:
                allM = allM + abs(float(data[i].get("txamt")))
            elif data[i].get('poscode') not in lists:
                allQ = allQ + abs(float(data[i].get("txamt")))

        dir["旭日苑"]=allX
        dir["东升苑"] = allD
        dir["美广"] = allM
        dir["其他"] = allQ
        dir["商店"] = allS

        a=Counter(codelist)  #将数据进行统计
        b = sorted(a.items(),key=lambda x:x[1],reverse=True)  #将统计过的数据进行排序
        toplist = []
        for i in range(b.__len__()):#获取到吃的最多的档口的poscode  和次数
            data2["time"]=b[i][1]  #将次数保存下来
            eatsum = 0
            for j in range(len(data)): #遍历流水信息
                code = str((data[j].get("poscode"))) #获取流水信息中的poscode
                if code ==b[i][0]: #找到消费最多的档口   ---==0355
                    name1 = list(models.List.objects.filter(lid=code).values()) #数据库中查询对应信息
                    if len(name1)!=1:
                        data2["shopname"]='无'
                    else:
                        data2["shopname"]=name1[0].get('shop')  #将档口名保存
                    eatsum=eatsum+abs(float(data[j].get("txamt"))) #统计消费总和
                data2["sum"]=eatsum  #将消费总和保存起来
            toplist.append(data2.copy())


        #-----将查询到的具体店名的信息插入到返回数据中
        for i in range(len(data)):
            shopname = list(models.List.objects.filter(lid=data[i].get('poscode')).values())
            # dirname = list(models.List.objects.filter(li))
            if len(shopname)!=1:
                dirshop = "无"
                name = "无"
            else:
                name = shopname[0].get('shop')
                dirshop = shopname[0].get('dir')

            dict2 = {'shopname':name,'dir':dirshop}
            data1= dict(data[i], **dict2)
            data[i]=data1



        re = json.dumps({
            "status": 0,
            "msg": "查询成功！",
            "cost":all,
            "data": data,
            "dirlist":[dir],
            "toplist":top(toplist)

        })
        return HttpResponse(re,content_type="application/json,charset=utf-8")

    else:
        re = json.dumps({
            "status": 1,
            "msg": "请使用post请求",
            "data": "",
        })
        return HttpResponse(re, content_type="application/json")










#获取当前所在月份的第一天的日期
#参数，输入月份
def getOneMonth():
    month=datetime.datetime.now().month
    year=str(datetime.datetime.now().year)
    # nowdate=datetime.date.fromtimestamp(time.mktime(time.strptime(str(datetime.datetime.now().date()), "%Y-%m-%d")))
    if month<10:
        month="0"+str(month)
    monthdate=year+"-"+str(month)+"-01"
    return monthdate


#获取输入日期所造周的周一
#输入参数格式times="2018-5-19"
#返回周一的日期 2018-5-14
def getThisWeek(times):
    # 尝试将参数转换成为datetime.date格式，1是方便后面的日期加减，2是验证日期是否有效。
    date_input = datetime.date.fromtimestamp(time.mktime(time.strptime(str(times), "%Y-%m-%d")))
    n = datetime.datetime.weekday(date_input)
    this_day = date_input + datetime.timedelta(0 - n)
    return this_day











def addList1(request):
    num1 = 1

    list = ['lala', '四季水果蔬菜配送', '四季水果蔬菜配送', '西府削筋面', '西府削筋面', '缘福记：小笼包&馄饨', '缘福记：小笼包&馄饨', '食话食说快餐', '食话食说快餐',
            '烤冷面&杂粮煎饼&寿司', '烤冷面&杂粮煎饼&寿司', '岐山臊子面&岐山擀面皮', '岐山臊子面&岐山擀面皮', '洋芋擦擦&粗粮面', '洋芋擦擦&粗粮面', '冷热麻食&同州月牙饼',
            '冷热麻食&同州月牙饼', '溢香园饺子', '溢香园饺子', '么么哒快餐', '么么哒快餐', '无刺鲫鱼', '无刺鲫鱼', '潼关肉夹馍&香香土豆粉', '潼关肉夹馍&香香土豆粉',
            '肉夹馍&鸡丝馄饨&手擀粉', '肉夹馍&鸡丝馄饨&手擀粉', '港式粥&铁板炒饭', '港式粥&铁板炒饭', '东北饺子', '东北饺子', '7+1木桶饭', '7+1木桶饭', '金柳叶：鸡汤刀削面&手擀面',
            '金柳叶：鸡汤刀削面&手擀面', '绝味鸭脖：卤菜&关中大碗面', '绝味鸭脖：卤菜&关中大碗面', '川味小炒&盖浇饭', '川味小炒&盖浇饭', '云南傣家米线', '云南傣家米线', '无', '无',
            '无', '无', '夹拣成厨麻辣香锅', '夹拣成厨麻辣香锅', '兰州拉面 牛肉泡馍盖饭', '兰州拉面 牛肉泡馍盖饭', '煲仔快餐', '煲仔快餐', '小碗菜&瓦罐煨汤', '小碗菜&瓦罐煨汤',
            '炒菜，石锅盖饭，盖浇饭', '炒菜，石锅盖饭，盖浇饭', '大碗卤肉饭', '大碗卤肉饭', '川渝营养快餐', '川渝营养快餐', '无', '无', '复盛隆米粉凉皮', '复盛隆米粉凉皮',
            '老成都鸡捞面', '老成都鸡捞面', '馋嘴猫香辣粉', '馋嘴猫香辣粉', '南京鸭血粉丝汤', '南京鸭血粉丝汤', '荆记粥铺菜夹馍', '荆记粥铺菜夹馍', '美食美容麻辣拌', '美食美容麻辣拌',
            '安徽风味饼', '安徽风味饼', '商店', '商店']

    num2 = 1
    for num in range(1, 77):
        if int(num) < 10:
            num1 = "000" + str(num)
        else:
            num1 = "00" + str(num)


        models.List.objects.create(

            lid = num1,
            shop = list[num],
            dir = '美广'
        )
    re = json.dumps({
        "status": 1,
        "msg": "添加成功",
        "data": "",
    })
    return HttpResponse(re, content_type="application/json")



def addList2(request):
    num1 = 1

    list = ['lala', '米粉', '米粉', '湖南蒸菜', '湖南蒸菜', '香辣炸鸡饭', '香辣炸鸡饭', '鸡肉卷，炒饭', '鸡肉卷，炒饭', '兄弟快餐', '兄弟快餐', '兄弟快餐', '兄弟快餐',
            '夹馍，酸菜鱼米线', '夹馍，酸菜鱼米线', '小笼包，粗粮面', '小笼包，粗粮面', '刀削面', '刀削面', '营养套餐', '营养套餐', '营养套餐', '营养套餐', '香锅冒菜', '香锅冒菜',
            '重庆小面', '重庆小面', '邮电风味快餐', '邮电风味快餐', '邮电风味快餐', '邮电风味快餐', '砂锅凉皮肉夹馍', '砂锅凉皮肉夹馍', '芝士焗饭', '芝士焗饭', '刀削面', '刀削面',
            '朝鲜烤冷面', '朝鲜烤冷面', '炒饭炒面', '炒饭炒面', '麻辣鱼', '麻辣鱼', '黄焖鸡', '黄焖鸡', '老碗煮馍', '老碗煮馍', '火锅冒菜', '火锅冒菜', '盖浇饭', '盖浇饭',
            '牛肉拉面', '砂锅', '砂锅', '二楼吧台', '一楼商店', '无', '无', '无', '粥', '无', '无', 'i上菓子', '无', '无', '无', '无', '无', '粥',
            '风味饼', '风味饼', '无', '无', '无', '无', '商店', '商店']

    num2 = 1
    for num in range(1, 71):
        if int(num) < 10:
            num1 = "030" + str(num)
        else:
            num1 = "03" + str(num)

        models.List.objects.create(

            lid = num1,
            shop = list[num],
            dir = '东升苑'
        )
    re = json.dumps({
        "status": 1,
        "msg": "添加成功",
        "data": "",
    })
    return HttpResponse(re, content_type="application/json")


def addList3(request):
    num1 = 1

    list = ['lala', '香锅粉类&腊汁肉拌面', '鸡汤方便面', '南方风味饼', '南方风味饼', '永和鲜豆浆', '永和鲜豆浆', '花样饼&胡辣汤', '花样饼&胡辣汤', '骨汤冒菜&麻辣香锅',
            '小馋虫烩麻食', '腊汁肉夹馍', '红油米线', '初味柠檬鱼', '精品套餐', '精品套餐', '自选快餐', '自选快餐', '天津包子', '天津包子', '手擀软面', '手擀软面', '菠菜面',
            '手擀面', '醉三国', '醉三国', '秦镇凉皮&煎饼果子', '云南过桥米线', '淮南牛肉汤', '盛香煲仔饭', '兰州牛肉面', '兰州牛肉面', '盖浇饭', '盖浇饭', '五谷渔粉',
            '五谷渔粉', '景娘煮馍', '景娘煮馍', '重庆砂锅', '东兴快餐', '东兴快餐', '山东掉渣饼', '山东掉渣饼', '山西饼', '山西饼', '山西饼', '粗粮玉米面', '老北京鸡肉卷',
            '南方甜食', '南方甜食', '传昊鲜渔粉&高记肉夹馍', '汉中米皮', '无', '无', '客来粥到', '无', '无', '无', '无', '好再来拉面馆', '好再来拉面馆', '木桶饭',
            '木桶饭', '食客思百味', '食客思百味', '锅巴米饭', '锅巴米饭', '蜀香园小炒', '蜀香园小炒', '川味小炒', '川味小炒', '湖南土菜馆', '湖南土菜馆', '重庆鸡公煲',
            '重庆鸡公煲', '杨铭宇黄焖鸡米饭', '杨铭宇黄焖鸡米饭', '刘记广式快餐', '刘记广式快餐', '老陕面馆', '老陕面馆', '西府削筋面', '西府削筋面', '东北饺子', '东北饺子',
            '东北饺子', '东北饺子', '丝路米粉', '丝路米粉', '重庆冒菜', '重庆冒菜', '重庆小火锅', '重庆小火锅', '凉皮肉夹馍', '凉皮肉夹馍', '小盘鸡拌面', '小盘鸡拌面',
            '台湾鸡排烤肉拌饭', '台湾鸡排烤肉拌饭', '爱尚麻辣香锅', '爱尚麻辣香锅', '楞娃手擀面', '楞娃手擀面', '楞娃手擀面', '楞娃手擀面', '无', '无', '无', '无', '无',
            '无', '无', '无', '无', '无 ', '土豆片夹馍', '无', '无', '重庆砂锅', '无', '无', '无', '无', '无', '无', '无', '无', '无', '无', '无',
            '无', '无', '无', '一楼面包', '一楼面包', '一楼面包', '无', '无', '无', '无', '无', '旭日院一楼商店', '旭日院一楼商店', '旭日院一楼商店', '旭日院一楼商店',
            '旭日院一楼商店', '无', '桶饼', '爱品客西点屋', '二楼商店', '二楼商店', '二楼商店', '鹏宇快印（靠近男生宿舍打印店）', '书香苑', '蜜雪冰城',
            '西邮快印（靠近女生宿舍旁打印店）', '无', '无', '综合经营部（商店）','无']

    num2 = 1
    for num in range(1, 160):
        if int(num) < 10:
            num1 = "010" + str(num)
        elif int(num) < 100:
            num1 = "01" + str(num)
        elif int(num) < 200:
            num1 = "0" + str(100 + int(num))


        models.List.objects.create(

            lid = num1,
            shop = list[num],
            dir = '旭日苑'
        )
    re = json.dumps({
        "status": 1,
        "msg": "添加成功",
        "data": "",
    })
    return HttpResponse(re, content_type="application/json")

def top(toplist):
    toplist2 = toplist
    for i in range(len(toplist)):
        for j in range(i + 1, len(toplist)):
            timeI = toplist[i].get('time')
            shopnameI = toplist[i].get('shopname')
            sumI = toplist[i].get('sum')
            timeJ = toplist[j].get('time')
            shopnameJ = toplist[j].get('shopname')
            sumJ = toplist[j].get('sum')
            if shopnameI == shopnameJ and i!=j:
                chen = {}
                chen1 ={}
                chen['time'] = timeI + timeJ
                chen['sum'] = sumI + sumJ
                toplist2[i].update(chen)                   #
                chen1['time'] = 0
                chen1['sum'] = 0
                chen1['shopname'] = 0
                toplist2[j].update(chen1)
    data=[]
    for i in range(len(toplist2)):
        if str(toplist2[i].get('shopname')) != "无" and str(toplist2[i].get('shopname')) != "0":
            data1={}
            data1['time']=toplist2[i].get('time')
            data1['shopname']=toplist2[i].get('shopname')
            data1['sum']=toplist2[i].get('sum')
            data.append(data1)
    return data