from fake_useragent import UserAgent
from Databases import Databases
from bs4 import BeautifulSoup
from mysql import connector
from Tools import Tools
import multiprocessing
import asyncio
import aiohttp
import time


#urls = []
#pgHtmls = []
#htmls = []
ua = UserAgent()
headers={"User-Agent": ua.random}
table = "watched2"
db = Databases(host="localhost", port="3307", user="WIIASD", password="987654321", database="myanime", table=table)



async def getHtml(url):
    '''
    异步返回对应url的html

    Parameters
    ----------
    url: String
        网页url

    Returns: String
        网页html
    -------

    '''
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as source:
            result = await source.text(encoding = "utf-8")
            await session.close()
            return result

"""
异步封装getHtml
"""
async def addPgHtmls(url, pgHtmls):
    '''
    异步封装getHtml，将结果放入pgHtmls
    Parameters
    ----------
    url: String
        网页url
    pgHtmls: String []
        外部变量：储存所有（番剧列表页面）的html
    Returns: void
    -------

    '''
    pgHtmls.append(await getHtml(url))

async def addHtmls(url, htmls):
    '''
        异步封装getHtml，将结果放入htmls
        Parameters
        ----------
        url: String
            网页url
        htmls: String []
            外部变量：储存所有（番剧页面）的html
        Returns: void
        -------

    '''
    htmls.append(await getHtml(url))


def getPagesHtmls():
    '''
    异步获取所有（番剧列表页面）的html
    Returns: void
    -------

    '''
    totalPgNum = Tools.getPgNum();
    pgUrls = [f"https://bangumi.tv/anime/list/556647/collect?page={i}" for i in range(1, totalPgNum+1)]
    tasks = []
    pgHtmls = []
    loop = asyncio.get_event_loop()
    for url in pgUrls:
        task = loop.create_task(addPgHtmls(url, pgHtmls))
        tasks.append(task)
    loop.run_until_complete(asyncio.gather(*tasks))
    return pgHtmls


def getAllUrls(pgHtmls):
    '''
    获取所有(番剧页面)的url
    Parameters
    ----------
    pgHtmls: String []
        存放所有（番剧列表页面）的html
    Returns: String []
        返回所有（番剧页面）的url
    -------

    '''
    urls = []
    for html in pgHtmls:
        soup = BeautifulSoup(html, "lxml")
        itemHolder = soup.find("ul", class_="browserFull")
        items = itemHolder.findAll("li")
        for item in items:
            urls.append("https://bangumi.tv/subject/" + item["id"][5:])
    return urls


def getAllHtmls(urls):
    '''
    异步获取所有(番剧页面)html
    Parameters
    ----------
    urls: String []
        存放所有（番剧页面）的url
    Returns: String []
        存放所有（番剧页面）的html
    -------

    '''
    tasks = []
    htmls = []
    loop = asyncio.get_event_loop()
    for url in urls:
        task = loop.create_task(addHtmls(url, htmls))
        tasks.append(task)
    loop.run_until_complete(asyncio.gather(*tasks))
    return htmls


def processInfo(html, resultList, failList):
    '''
    提取并打印单个番剧页面的信息
    Parameters
    ----------
    html: String
        单个（番剧页面）的html
    resultList: multiprocessing.Manager().list()
        （外部变量）多进程共享列表，储存得到的信息
    failList: multiprocessing.Manager().list()
        （外部变量）多进程共享列表，储存获取信息失败的html

    Returns: void
    -------

    '''
    soup = BeautifulSoup(html, "lxml")
    try:
        infoBox = Tools.getData(soup.find("ul", id="infobox"), ["episodes", "date", "original", "director", "studio", "chineseName"])
    except:
        print("Error: 获取数据失败")
        failList.append(html)
        return
    try:
        coverUrl = "https:" + soup.find("a", class_="thickbox cover")["href"]
    except Exception as e:
        coverUrl = "Error: 封面链接获取失败"
    infobox = Tools.fkDoubleQuote(infoBox)
    bangumiNum = soup.find("ul", class_="navTabs clearit").li.a["href"][9:]
    ranking = float(soup.find("div", class_="global_score").span.text)
    episodes = infobox[0]
    date = infobox[1]  # if infobox[1] != "未知" else Tools.toDate(description[1])
    original = infobox[2]
    director = infobox[3]
    studio = infobox[4]
    japaneseName = soup.find(class_="nameSingle").find("a").text
    chineseName = infobox[5] if infobox[5] != "未知" else japaneseName
    resultList.append((chineseName, japaneseName, date, episodes, original, director, studio, ranking, bangumiNum, coverUrl))
    if db.cursor == None:
        return
    db.cursor.execute(f'INSERT INTO {table} (中文名, 日文名, 首播日期, 集数, 原作, 导演, 动画制作, 评分, Bangumi页面, 封面链接)'
                     f' VALUES ("{chineseName}", "{japaneseName}", "{Tools.toDate(date)}", "{episodes}", "{original}", "{director}", "{studio}", "{ranking}", "{bangumiNum}", "{coverUrl}");')
    db.connection.commit()
    #print(f"中文名：{chineseName}\n"
            #f"日文名：{japaneseName}\n"
            #f"首播日期：{date}\n"
            #f"集数：{episodes}\n"
            #f"原作：{original}\n"
            #f"导演：{director}\n"
            #f"动画制作：{studio}\n"
            #f"Bangumi页面：{bangumiNum}\n"
            #f"封面链接：{coverUrl}\n"
          #)


def processAllInfo(htmls, resultList, failList):
    '''
    多进程提取并打印所有番剧页面的信息
    Parameters
    ----------
    htmls: String[]
        储存所有（番剧页面）的html
    resultList: multiprocessing.Manager().list()
        （外部变量）多进程共享列表，储存得到的信息
    failList: multiprocessing.Manager().list()
        （外部变量）多进程共享列表，储存获取信息失败的html

    Returns: void
    -------

    '''
    htmls = [(x, resultList, failList) for x in htmls] # 把htmls重构成（html, 多进程共享list）的形式
    pool = multiprocessing.Pool(multiprocessing.cpu_count())
    pool.starmap(processInfo, htmls)
    pool.close()
    pool.join()


def getAllId():
    '''
    获取所有（番剧页面）的bangumi id
    Returns: int[]
        所有（番剧页面)的id
    -------

    '''
    ids = []
    pgHtmls = getPagesHtmls()
    urls = getAllUrls(pgHtmls)
    for url in urls:
        ids.append(int(url.split("/")[-1]))
    return ids

#def getAllDbId():
#     '''
#     获取数据库现有的所有(番剧页面）的id
#     Returns: int []
#        数据库所有（番剧页面）的id
#     -------
#
#     '''
#     mycursor.execute("SELECT Bangumi页面 FROM watched2 ORDER BY Bangumi页面 ASC")
#     result = mycursor.fetchall()
#     dbId = [i[0] for i in result]
#     return dbId

def updateDb(resultList, failList):
    '''
    主要运行函数，更新数据库信息
    Parameters
    ----------
    resultList: multiprocessing.Manager().list()
        （外部变量）多进程共享列表，储存得到的信息
    failList: multiprocessing.Manager().list()
        （外部变量）多进程共享列表，储存获取信息失败的html

    Returns: void
    -------

    '''
    ids = getAllId()
    dbId = db.getAllId()
    if len(ids) == len(dbId):
        print("Database is up to date !")
        return
    if len(ids) > len(dbId):
        urls = ["https://bangumi.tv/subject/" + str(i) for i in set(ids).difference(set(dbId))]
        print(f"found {len(urls)} new urls")
        htmls = getAllHtmls(urls)
        if db.cursor == None:
            print("printing out all items...")
        else:
            print("inserting into the database...")
        processAllInfo(htmls, resultList, failList)
    else:
        id2Delete = [i for i in set(dbId).difference(set(ids))]
        for id in id2Delete:
            if db.deleteById(id):
                print(f"{id} deleted")
            else:
                print(f"{id} delete failed")

if __name__ == "__main__":

    if db.cursor == None:
        print("Not connected to the database!")
    else:
        print("Connected to the database!")

    start = time.time()
    manager = multiprocessing.Manager()
    resultList = manager.list() # 多进程共享列表，储存得到的信息
    failedList = manager.list() # 多进程共享列表，储存获取信息失败的html
    updateDb(resultList, failedList)

    print(*resultList, sep='\n')
    print(f"Insert successfully: {len(resultList)}")
    print(f"Insert failed: {len(failedList)}")
    end = time.time()
    print("Time spent: " + str(end-start) + " s")
    # 以下是老代码
    # print(len(set(ids).difference(set(dbId))))
    # getPagesHtmls()
    # getAllUrls()
    # getAllHtmls()
    # processAllInfo()