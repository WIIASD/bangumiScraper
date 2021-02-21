from fake_useragent import UserAgent
from bs4 import BeautifulSoup
from mysql import connector
from Tools import Tools
import multiprocessing
import asyncio
import aiohttp
import time


urls = []
pgHtmls = []
htmls = []
failedHtmls = 0
ua = UserAgent()
headers={"User-Agent": ua.random}
db = connector.connect(
    host="localhost",
    port="3307",
    user="WIIASD",
    password="987654321",
    database="myanime"
)

mycursor = db.cursor()

"""
从url获取html文件    
:param url: url
:return: html字符串
"""
async def getHtml(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as source:
            result = await source.text(encoding = "utf-8")
            await session.close()
            return result

"""
异步封装getHtml
"""
async def addPgHtmls(url):
    pgHtmls.append(await getHtml(url))

async def addHtmls(url):
    htmls.append(await getHtml(url))

"""
异步获取所有列表html
"""
def getPagesHtmls():
    totalPgNum = Tools.getPgNum();
    pgUrls = [f"https://bangumi.tv/anime/list/556647/collect?page={i}" for i in range(1, totalPgNum+1)]
    tasks = []
    loop = asyncio.get_event_loop()
    for url in pgUrls:
        task = loop.create_task(addPgHtmls(url))
        tasks.append(task)
    loop.run_until_complete(asyncio.gather(*tasks))

"""
获取所有番剧页面url 
"""
def getAllUrls():
    for html in pgHtmls:
        soup = BeautifulSoup(html, "lxml")
        itemHolder = soup.find("ul", class_="browserFull")
        items = itemHolder.findAll("li")
        for item in items:
            urls.append("https://bangumi.tv/subject/" + item["id"][5:])

"""
异步获取所有番剧页面html 
"""
def getAllHtmls():
    tasks = []
    loop = asyncio.get_event_loop()
    for url in urls:
        task = loop.create_task(addHtmls(url))
        tasks.append(task)
    loop.run_until_complete(asyncio.gather(*tasks))
    return

"""
提取并打印单个番剧页面的信息
:param html: 番剧页面的html  
"""
def printInfo(html, resultList):
    soup = BeautifulSoup(html, "lxml")
    try:
        infoBox = Tools.getData(soup.find("ul", id="infobox"), ["episodes", "date", "original", "director", "studio", "chineseName"])
    except:
        print("Error: 获取数据失败")
        return
    try:
        coverUrl = "https:" + soup.find("a", class_="thickbox cover")["href"]
    except Exception as e:
        coverUrl = "Error: 封面链接获取失败"
    infobox = Tools.fkDoubleQuote(infoBox)
    bangumiNum = soup.find("ul", class_="navTabs clearit").li.a["href"][9:]
    episodes = infobox[0]
    date = infobox[1]  # if infobox[1] != "未知" else Tools.toDate(description[1])
    original = infobox[2]
    director = infobox[3]
    studio = infobox[4]
    japaneseName = soup.find(class_="nameSingle").find("a").text
    chineseName = infobox[5] if infobox[5] != "未知" else japaneseName
    resultList.append((chineseName, japaneseName, date, episodes, original, director, studio, bangumiNum, coverUrl))
    #mycursor.execute(f'INSERT INTO watched3 (中文名, 日文名, 首播日期, 集数, 原作, 导演, 动画制作, Bangumi页面, 封面链接)'
    #                 f' VALUES ("{chineseName}", "{japaneseName}", "{Tools.toDate(date)}", "{episodes}", "{original}", "{director}", "{studio}", "{bangumiNum}", "{coverUrl}");')
    #db.commit()
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

"""
多进程提取并打印所有番剧页面的信息 
"""
def processAllInfo(resultList):
    global htmls
    htmls = [(x, resultList) for x in htmls] #把htmls重构成（html, 多进程共享list）的形式
    pool = multiprocessing.Pool(multiprocessing.cpu_count())
    pool.starmap(printInfo, htmls)
    pool.close()
    pool.join()


def getAllId():
    ids = []
    getPagesHtmls()
    getAllUrls()
    for url in urls:
        ids.append(int(url.split("/")[-1]))
    return ids

def getAllDbId():
     mycursor.execute("SELECT Bangumi页面 FROM watched2 ORDER BY Bangumi页面 ASC")
     result = mycursor.fetchall()
     dbId = [i[0] for i in result]
     return dbId

def updateDb(resultList):
    ids = getAllId()
    dbId = getAllDbId()
    global urls
    global htmls
    if(len(ids) == len(dbId)):
        print("Database is up to date !")
        return
    if len(ids) > len(dbId):
        urls = ["https://bangumi.tv/subject/" + str(i) for i in set(ids).difference(set(dbId))]
        print(f"found {len(urls)} urls")
        getAllHtmls()
        print("htmls array length："+str(len(htmls)))
        print("inserting into the database...")
        processAllInfo(resultList)
    else:
        id2Delete = [i for i in set(dbId).difference(set(ids))]
        for id in id2Delete:
            mycursor.execute(f"DELETE FROM watched3 WHERE Bangumi页面={id}")
            print(f"{id} deleted")
            db.commit()

if __name__ == "__main__":
    start = time.time()
    manager = multiprocessing.Manager()
    resultList = manager.list()
    #print(len(set(ids).difference(set(dbId))))
    #getPagesHtmls()
    #getAllUrls()
    #getAllHtmls()
    #processAllInfo()
    updateDb(resultList)
    print(*resultList, sep='\n')
    print(len(resultList))
    end = time.time()
    print("Time spent: " + str(end-start) + " s")