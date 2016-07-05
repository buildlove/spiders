# -*-coding:utf8-*-
__author__ = 'liyang'

import re
import os
import urllib
import json
import sys
import unicodedata
import time
# import pymysql
from lxml import etree
from bs4 import BeautifulSoup
reload(sys)
sys.setdefaultencoding('utf-8')
#创建空xml对象
root = etree.Element("root")
#设置时间格式
ISOTIMEFORMAT="%Y-%m-%d %X"

# conn = pymysql.connect(host='127.0.0.1', port=3306, user='liyang', passwd='123456', db='mysql')
# cursor = conn.cursor()

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
  start_page = time.clock()
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
  end_page = time.clock()
  print u"实例化列表成功: %f s" % (end_page - start_page)
  return searchPage

#得到文章列表
def getArticleTitle(html):
  if not html: print "页面不存在"
  start_art = time.clock()
  articleList = []
  soup = BeautifulSoup(html, "html.parser")
  soup6 = soup.find_all('script')[6]
  # print soup6
  reg = r"msgList = '(.*?)'"
  change = re.compile(reg)
  lists = re.search(change, str(soup6)).group()
  lists = lists.replace(r"&amp;", '&')
  lists = lists.replace(r"msgList = ",' ',1)
  lists = lists.replace(r"&quot;", '"')
  lists = lists.replace(r"&amp;", '&')
  lists = lists.replace(r'&lt;', '<')
  lists = lists.replace(r'&gt;;', '>')
  lists = lists.replace(r'&lt;', '<')
  lists = lists.replace(r'&nbsp;', ' ')
  writeFile(eval(lists),'./message/article.json')
  encode_json = eval(lists)
  if encode_json:
    decode_json = json.loads(encode_json)["list"]
    for message in decode_json:
      if message.has_key("app_msg_ext_info"):
        otherArticle = message["app_msg_ext_info"]["multi_app_msg_item_list"]
        articleList.extend(otherArticle)
        onlyArticle = message["app_msg_ext_info"].pop("multi_app_msg_item_list")
        articleList.append(message["app_msg_ext_info"])
    end_art = time.clock()
    print u"得到文章列表: %f s" % (end_art - start_art)
    return articleList

# 减少重复代码(有待优化)
def textToXml(tit, searchPage):
  title = etree.SubElement(root, tit)
  title.text = searchPage[tit]

# 创建XML文件
def createXML(searchPage, articleList):
  start_xml = time.clock()
  textToXml('Wname', searchPage)
  textToXml('Wnumber', searchPage)
  textToXml('artlink', searchPage)
  textToXml('funcms', searchPage)
  Path = os.getcwd() + '/xml/' + searchPage["Wnumber"] + '.xml'

  for info in articleList:
    textToXml('title', info)
    content_url = etree.SubElement(root, "url")
    content_url.text = "http://mp.weixin.qq.com" + info['content_url']
    times = etree.SubElement(root, "data-time")
    times.text = time.strftime( ISOTIMEFORMAT, time.localtime() )

  xml = etree.tostring(root, pretty_print=True)

  #写入xml文件
  with open(Path, 'w') as el:
    el.write(xml)
  end_xml = time.clock()
  print u"创建xml文件: %f s" % (end_xml - start_xml)

#在线抓取
def online():
  print u'在线抓取(online)'
  # 请求用户输入的微信号 1查找并输出微信号信息 2写入html文件（用于离线请求）
  searchText = input('searchText: ')
  funLink = "http://weixin.sogou.com/weixin?type=1&query=" + searchText
  html = getHTML(funLink)
  searchPage = wrapPageNode(html)
  if searchPage:
    writeFile(html,'./message/search.html')
    # 请求文章在线地址 1输出文章详情数组 2写入html文件
    getArticlePage = getHTML(searchPage["artlink"])
    articleList = getArticleTitle(getArticlePage)
    if articleList:
      createXML(searchPage, articleList)
      writeFile(getArticlePage,'./message/article.html')
    else:
      print u"解析json节点失败"

#离线抓取
def offline():
  print u'离线抓取(offline)'
  html = open("./message/search.html")
  searchPage = wrapPageNode(html)
  if searchPage:
    #请求离线地址
    articlePage = open('./message/article.html')
    articleList = getArticleTitle(articlePage)
    if articleList:
      createXML(searchPage, articleList)

    else:
      print "检查文件/message/article.html是否存在"
  else:
    print "检查文件/message/search.html是否存在"

def main():
  argv = sys.argv
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



