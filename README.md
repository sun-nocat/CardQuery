# CardQuery
一卡通查询1.0
### 使用Python的Web框架Django。后台部分完成了以下功能
- 基于微信公众号的OAuth2.0认证，用户获取用户的信息
- 使用Python进行模拟登陆一卡通网站，获取用户的消费流水信息
- 通过建立实际餐厅档口的信息和消费流水之间的关系，从而确定用户的实际消费情况（消费流水信息中只有刷卡机编号，没有商家信息）
- 分析和统计数据，获取用户消费次数最多和消费额度最多的商家
- 前后端分离开发，并提供跨域支持
- 数据库使用MySQL。

### 将来打算完成功能
- 模拟登录一卡通网站时的验证码识别问题，现阶段是保存图片，然后交给用户自己手动输入验证码。这样不利于用户体验。尝试使用百度的OCR验证码识别系统并未解决问题，自己使用Python编写验证码识别程序依然成功率太低
- 添加一卡通余额较低时主动提醒功能：因为无法有效识别验证码，所以主动获取用户的消费信息，所以此功能尚未实现
