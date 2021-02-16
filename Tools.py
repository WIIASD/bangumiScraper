from fake_useragent import UserAgent
from bs4 import BeautifulSoup
import requests

ua = UserAgent()
headers={"User-Agent": ua.random}

class Tools:
    @staticmethod
    def fkSpace(strs):
        """
        把空格都cao飞
        :param strs: 任意字符串数组
        :return: 前后无空格的strs
        """
        for i in range(len(strs)):
            strs[i] = strs[i].strip()
        return strs
    @staticmethod
    def fkDoubleQuote(strs):
        for i in range(len(strs)):
            strs[i] = strs[i].replace('"', '')
        return strs

    @staticmethod
    def toDate(str):
        """
        yyyy年mm月dd日 转 yyyy-mm-dd
        :param str: yyyy年mm月dd日
        :return: yyyy-mm-dd
        """
        str = str.replace("年", "-")
        str = str.replace("月", "-")
        str = str.replace("日", "")
        return str

    @staticmethod
    def getPgNum():
        request = requests.get("https://bangumi.tv/anime/list/556647/collect?page=1", headers=headers)
        request.encoding = "utf-8"
        html = request.text
        pgNumHolder = BeautifulSoup(html, "lxml").find("span", class_="p_edge").text.split("\xa0")
        return int(pgNumHolder[3])

    commands = {"episodes": "话数: ", "studio": "动画制作: ", "original": "原作: ",
                "director": "导演: ", "official": "官方网站: ", "date": "放送开始: ", "chineseName": "中文名: "}
    @staticmethod
    def getData(infoBox, commandArray):
        """
        从infoBox里提取相应的数据并返回
        :param infoBox: Beautiful soup 实例， 包含bangumi番剧页面的信息框
        :param commandArray: 包含需要返回的数据命令的数组
        :return: 返回数据列表
        """
        result = []
        for command in commandArray:
            cmd = Tools.commands.get(command)
            if cmd is None:
                print("Invalid Command!")
                return
            info = infoBox.find("span", string=cmd)

            if info is None:
                if cmd == "导演: ":
                    info = infoBox.find("span", string="总导演: ")
                    if info is not None:
                        result.append(info.parent.text.split(": ")[1])
                        continue
                if cmd == "原作: ":
                    result.append("原创")
                    continue
                if cmd == "放送开始: ":
                    info = infoBox.find("span", string="发售日: ")
                    if info is not None:
                        result.append(info.parent.text.split(": ")[1])
                        continue
                    info = infoBox.find("span", string="上映年度: ")
                    if info is not None:
                        result.append(info.parent.text.split(": ")[1])
                        continue

                result.append("未知")
            else:
                result.append(info.parent.text.split(": ")[1])
        return result