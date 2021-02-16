from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import requests
from enum import Enum
import time
import mysql.connector
ua = UserAgent()
headers={"User-Agent": ua.random}

urls = [f"https://bangumi.tv/anime/list/556647/collect?page={i}" for i in range(1, 13)]
bangumiPgUrls = []

totalPgNum = 12
currentPgNum = 1

class INFOBOX(Enum):
    episodes = 1

def soupUrl(url):
    """
    Soup一个网址
    :param url: 要soup的网址
    :return: 返回BeautifulSoup实例
    """
    source = requests.get(url, headers=headers)
    source.encoding = "utf-8"
    html = source.text
    return BeautifulSoup(html, "lxml")

def fkSpace(strs):
    """
    把空格都cao飞
    :param strs: 任意字符串数组
    :return: 前后无空格的strs
    """
    for i in range(len(strs)):
        strs[i]=strs[i].strip()
    return strs

def toDate(str):
    """
    yyyy年mm月dd日 转 yyyy-mm-dd
    :param str: yyyy年mm月dd日
    :return: yyyy-mm-dd
    """
    str=str.replace("年","-")
    str=str.replace("月","-")
    str=str.replace("日","")
    return str

commands = {"episodes":"话数: ", "studio":"动画制作: ", "original":"原作: ",
            "director":"导演: ", "official":"官方网站: "}

def getBangumiPgInfoBoxData(url, command):
    """
    从infobox提取信息
    :param url: 某一番剧页面的网址
    :param command: 指令
                        1. episodes：获取话数
                        2. studio：获取动画制作公司
    :return: 返回信息的字符串
    """
    result = ""
    cmd = commands.get(command)
    if cmd is None:
        print("Invalid Command!")
        return

    soup = soupUrl(url)
    infoBox = soup.find("ul", id="infobox")
    result = infoBox.find("span", string=cmd)
    if result is None:
        return "未知"
    return result.parent.text.split(" ")[1]

def printItems(items):
    """
    打印Bangumi动画列表里的全部内容
    :param items: 包含页面上番剧所有li标签的list
    :return: 无
    """
    for item in items:
        title = item.find("h3")
        bangumiPgUrl = "https://bangumi.tv" + item.find("a")["href"]
        coverUrl = "https:" + item.find("img", class_="cover")["src"].replace("/s/", "/c/") #/s/为小封面/c/为大封面
        description = item.find("p").text.split("/")
        description = fkSpace(description)[:3]
        if description[0].find("年") != -1:
            episodes = getBangumiPgInfoBoxData(bangumiPgUrl, "episodes")
            date = toDate(description[0])
        else:
            episodes = description[0].replace("话", "")
            date = toDate(description[1])
        try:
            original = description[2]
        except IndexError:
            original = "没显示"
        chineseName = title.find("a").text
        japaneseName = title.find(("small")).text if (title.find(("small")) is not None) else chineseName

        print(f"中文名：{chineseName}")
        print(f"日文名：{japaneseName}")
        print(f"首播日期：{date}")
        print(f"集数：{episodes}")
        print(f"原作：{original}") #这个original有时会变成导演或者其他奇怪的东西，想要准确的最好用getBangumiPgInfoBoxData()
        print(f"封面链接：{coverUrl}")
        print(f"Bangumi页面：{bangumiPgUrl}")
    return

def loadLinks(items):
    """
    loadPageUrls HELPER
    加载Bangumi动画列表里的全部内容到bangumiPgUrls里
    :param items: 包含页面上番剧所有li标签的list
    :return: 无
    """
    for item in items:
        bangumiPgUrl = "https://bangumi.tv" + item.find("a")["href"]
        #print(bangumiPgUrl)
        bangumiPgUrls.append(bangumiPgUrl)
    return

def loadPageUrls(pgUrl):
    """
    loadAllPagesUrls HELPER
    加载Bangumi番剧列表的其中一页并加入BangumiPgUrls里
    :param pgNum: 页面url
    :return: 无
    """
    soup = soupUrl(pgUrl)
    itemHolder = soup.find("ul", class_="browserFull")
    items = itemHolder.findAll("li")
    loadLinks(items)
    return

def loadPage1(pgNum):
    """
    加载Bangumi番剧列表的其中一页并打印
    :param pgNum: 页数
    :return: 无
    """
    global totalPgNum
    pgUrl = "https://bangumi.tv/anime/list/556647/collect?page=" + str(pgNum)
    source = requests.get(pgUrl, headers=headers)
    source.encoding = "utf-8"
    html = source.text
    soup = BeautifulSoup(html, "lxml")
    itemHolder = soup.find("ul", class_="browserFull")
    items = itemHolder.findAll("li")
    #pgNumHolder = soup.find("span", class_="p_edge").text.split("\xa0")
    #totalPgNum = int(pgNumHolder[3])
    printItems(items)
    #print(f"页数：{pgNum}/{totalPgNum}")
    return

def loadAllPages1():
    """
    加载所有Bangumi番剧列表并打印 (速度很快但信息不完全, 原作信息或有错漏)
    :return:无
    """
    global currentPgNum
    global totalPgNum
    while currentPgNum <= totalPgNum:
        loadPage1(currentPgNum)
        currentPgNum+=1
    currentPgNum = 1
    return

def loadAllPagesUrls():
    """
    加载所有Bangumi番剧页面到bangumiPgUrls里
    :return:无
    """
    global totalPgNum
    for url in urls:
        loadPageUrls(url)
    return

start = time.time()
#loadAllPages1()
source = requests.get("https://bangumi.tv/anime/list/556647/collect?page=3", headers=headers)
end = time.time()
print(end-start)



