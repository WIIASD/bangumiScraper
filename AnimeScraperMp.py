from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from mysql import connector
from Tools import Tools
import requests
import time
import multiprocessing

#db = connector.connect(
#    host="localhost",
#    port="3307",
#    user="WIIASD",
#    password="987654321",
#    database="myanime"
#)
#
#mycursor = db.cursor()

ua = UserAgent()
headers={"User-Agent": ua.random}

urls = [f"https://bangumi.tv/anime/list/556647/collect?page={i}" for i in range(1, 13)]

totalPgNum = 2
currentPgNum = 1

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

def getBangumiPgInfoBoxData(url, commandArray):
    """
    从infobox提取信息
    :param url: 某一番剧页面的网址
    :param command: 指令list
                        {"episodes": "话数: ", "studio": "动画制作: ", "original": "原作: ",
                        "director": "导演: ", "official": "官方网站: ", "date": "放送开始: "}
    :return: 返回信息的字符串
    """
    soup = soupUrl(url)
    infoBox = soup.find("ul", id="infobox")
    result = Tools.getData(infoBox, commandArray)

    return result

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
        description = Tools.fkSpace(description)[:3]
        infobox = getBangumiPgInfoBoxData(bangumiPgUrl, ["episodes","date","original","director","studio"])
        infobox = Tools.fkDoubleQuote(infobox)
        episodes = infobox[0]
        date = infobox[1] if infobox[1] != "未知" else Tools.toDate(description[1])#
        original = infobox[2]
        director = infobox[3]
        studio = infobox[4]
        chineseName = title.find("a").text
        japaneseName = title.find(("small")).text if (title.find(("small")) is not None) else chineseName
        bangumiNum = bangumiPgUrl.split("/")[-1]
        #mycursor.execute(f'INSERT INTO watched2 (中文名, 日文名, 首播日期, 集数, 原作, 导演, 动画制作, Bangumi页面, 封面链接)'
        #                 f' VALUES ("{chineseName}", "{japaneseName}", "{date}", "{episodes}", "{original}", "{director}", "{studio}", "{bangumiNum}", "{coverUrl}");')
        #db.commit()
        print(f"中文名：{chineseName}\n"
              f"日文名：{japaneseName}\n"
              f"首播日期：{date}\n"
              f"集数：{episodes}\n"
              f"原作：{original}\n"
              f"导演：{director}\n"
              f"动画制作：{studio}\n"
              f"Bangumi页面：{bangumiNum}\n"
              f"封面链接：{coverUrl}\n")
    return

#bangumiPgUrls = []

def loadLinks(items):
    """
    loadPageUrls HELPER
    加载Bangumi动画列表里的全部内容到bangumiPgUrls里
    :param items: 包含页面上番剧所有li标签的list
    :return: 无
    """
    for item in items:
        bangumiPgUrl = int(str(item.find("a")["href"]).split("/")[2])
        print(bangumiPgUrl)
        #bangumiPgUrls.append(bangumiPgUrl)
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

def loadPage(pgNum):
    """
    加载Bangumi番剧列表的其中一页并打印
    :param pgNum: 页数
    :return: 无
    """
    global totalPgNum
    pgUrl = "https://bangumi.tv/anime/list/556647/collect?page=" + str(pgNum)
    soup = soupUrl(pgUrl)
    itemHolder = soup.find("ul", class_="browserFull")
    items = itemHolder.findAll("li")
    pgNumHolder = soup.find("span", class_="p_edge").text.split("\xa0")
    totalPgNum = int(pgNumHolder[3])
    printItems(items)
    print(f"页数：{pgNum}/{totalPgNum}")
    return

def loadAllPages():
    """
    加载所有Bangumi番剧列表并打印  （多进程，信息准确）
    :return:无
    """
    soup = soupUrl("https://bangumi.tv/anime/list/556647/collect?page=1")
    pgNumHolder = soup.find("span", class_="p_edge").text.split("\xa0")
    totalPgNum = int(pgNumHolder[3])

    urls = urls = [i for i in range(1, totalPgNum+1)]
    pool = multiprocessing.Pool(multiprocessing.cpu_count())
    pool.map(loadPage, urls)
    pool.close()
    pool.join()
    return

def loadAllPagesUrls():
    """
    加载所有Bangumi番剧页面到bangumiPgUrls里  （多进程）
    :return:无
    """
    pool = multiprocessing.Pool(multiprocessing.cpu_count())
    pool.map(loadPageUrls, urls)
    pool.close()
    pool.join()
    return

def loadAllPagesUrlsGARBAGE():
    """
    加载所有Bangumi番剧页面到bangumiPgUrls里  (非多进程)
    :return:无
    """
    global totalPgNum
    for url in urls:
        loadPageUrls(url)
    return

if __name__ == "__main__":
    start = time.time()
    loadAllPages()
    #mycursor.execute("select * from watched2")
   # for i in mycursor:
    #    print(i)
    #loadAllPagesUrls()
    #loadAllPagesUrlsGARBAGE()
    end = time.time()
    print(end-start)

