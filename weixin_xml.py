# -*-coding:utf8-*-
import re
import os
import urllib
import json
import sys
import pymysql
from bs4 import BeautifulSoup

conn = pymysql.connect(host='127.0.0.1', port=3306, user='liyang', passwd='123456', db='mysql')
cursor = conn.cursor()

#请求地址，返回信息
def getHTML(url):
  page = urllib.urlopen(url)
  # print page.info()
  if page.getcode() == '200':
    print u'加入页面:' + url
  return page.read()

#创建文件，把信息写入到文件，如果存在文件直接替换
def writeFile(content, filePath):
  f = open(filePath, 'w')
  f.write(content)
  f.close()

#解析节点 寻找微信文章链接
def parselink(node):
  reg = r'href="(.*?)"'
  change = re.compile(reg)
  lists = re.findall(change, node)
  for l in lists:
    if l:
      l = l.replace('amp;', '')
      ori = re.search("profile", l)
      if ori:
        return l

# 用来获取搜狗搜索的第一个结果，实例化列表
def wrapPageNode(html):
  searchPage = {}
  soup = BeautifulSoup(html, "html.parser")
  results = soup.find_all("div", class_="results mt7")[0]
  searchPage["Wname"] = results.h3.string #微信名称 unicode(results.h3.string)
  searchPage["Wnumber"] = results.label.string #微信号
  searchPage["artlink"] = parselink(str(results)) #微信号文章页面链接
  lowList = results.find_all("p", "s-p3")
  searchPage["funcms"] = lowList[0].find_all("span","sp-txt")[0].string #微信功能介绍
  searchPage["sptit"] = lowList[1].find_all("span","sp-txt")[0].string #微信认证
  searchPage["artSrc"] = lowList[2].find_all("span","sp-txt")[0].a['href'] #微信最新文章链接
  searchPage["artTit"] = lowList[2].find_all("span","sp-txt")[0].a.string #微信最新文章
  # searchPage["ico"] = results.span["ico-bg"]  #头像链接，存在在css文件中
  return searchPage

def dict_to_list(d):
    a = []
    for key, value in d.iteritems():
        if (type(value) is dict):
            value = dict_to_list(value)
        a.append([key, value])
    return a

#得到文章列表
def getArticleTitle(html):
  articleList = []
  soup = BeautifulSoup(html, "html.parser")
  soup5 = soup.find_all('script')[5]
  reg = r"msgList = '(.*?)'"
  change = re.compile(reg)
  # print str(soup5)
  lists = re.search(change, str(soup5)).group().replace(r"&amp;", '&')
  lists = lists.replace(r"msgList = ",' ',1)
  lists = lists.replace(r"&quot;", '"')
  lists = lists.replace(r"&amp;", '&')
  lists = lists.replace(r'&lt;', '<')
  lists = lists.replace(r'&gt;;', '>')
  lists = lists.replace(r'&lt;', '<')
  lists = lists.replace(r'&nbsp;', ' ')
  writeFile(eval(lists),'./message/article.json')                                                  #
  encode_json = eval(lists)
  decode_json = json.loads(encode_json)["list"]
  # print type(decode_json)
  for message in decode_json:
    # print type(message)
    if message.has_key("app_msg_ext_info"):
      otherArticle = message["app_msg_ext_info"]["multi_app_msg_item_list"]
      articleList.extend(otherArticle)
      onlyArticle = message["app_msg_ext_info"].pop("multi_app_msg_item_list")
      articleList.append(message["app_msg_ext_info"])
  return articleList

def console(arg):
  # 如果是list,遍历list,遍历的值再判断
  if isinstance(arg, list):
    for i in arg:
      console(i)
  # 如果是dict,遍历dict,打印dict键值对
  elif isinstance(arg, dict):
    for x in arg:
      if x:
        print x + ' ' +arg[x]
  else:
    print 'what is it?'

def online():
  print u'在线抓取(online)'
  # 请求用户输入的微信号 1查找并输出微信号信息 2写入html文件（用于离线请求）
  searchText = input('searchText: ')
  funLink = "http://weixin.sogou.com/weixin?type=1&query=" + searchText
  html = getHTML(funLink)
  searchPage = wrapPageNode(html)
  writeFile(html,'./message/search.html')                                                   #
  # 请求文章在线地址 1输出文章详情数组 2写入html文件
  getArticlePage = getHTML(searchPage["artlink"])
  articleList = getArticleTitle(getArticlePage)
  writeFile(getArticlePage,'./message/article.html')                                        #

def offline():
  print u'离线抓取(offline)'
  html = open("./message/search.html")
  searchPage = wrapPageNode(html)
  console(searchPage)
  #请求离线地址
  articlePage = open('./message/article.html')
  articleList = getArticleTitle(articlePage)
  for tit in articleList:
    print tit["title"]
    # print tit["content_url"]

def main():
  argv = sys.argv
  print len(argv)
  if len(argv) >= 2:
    if argv[1] == 'offline':
      offline()
    elif argv[1] == 'online':
      online()
  else:
    online()

if __name__ == '__main__':
  main()

#微信号信息列表
  # name        #微信名称
  # number      #微信号
  # artlink     #微信号文章页面链接
  # funcms      #微信功能介绍
  # sptit       #微信认证
  # artSrc      #微信最新文章链接
  # artTit      #微信最新文章标题
#文章列表
#articleList
  # "title": "",         文章标题
  # "digest": "",
  # "content": "",
  # "fileid": 502346996,
  # "content_url": "",   文章url
  # "source_url": "",
  # "cover": "",
  # "subtype": 0,
  # "is_multi": 1,



