from bs4 import BeautifulSoup
import requests, re, pdb

PROXY_IP_SOURCE_URL = "http://ip84.com"

class proxy(object):
    def __init__(self, ip_address: str, port: str, location: str, anonymous: str, https: str, speed: str):
        if proxy.isValidIpFormat(ip_address) == False:
            raise ValueError()

        if not port.isdigit():
            raise ValueError()
        else:
            p = int(port)
            if p <= 0 or p > 65535:
                raise ValueError()

        self.__ip_addr = ip_address
        self.__port_number = port
        self.__location = location
        self.__anonymous = anonymous
        self.__http_protocal = https.lower()
        self.__speed = speed

    def __str__(self):
        return str("%s://%s:%s" %(self.__http_protocal, self.__ip_addr, self.__port_number))

    def isHttps(self):
        if self.__http_protocal.upper() == 'HTTPS':
            return True
        else:
            return False

    @classmethod
    def isValidIpFormat(cls, ip_str: str):
        matchobj = re.search(r"((?:(?:25[0-5]|2[0-4]\d|((1\d{2})|([1-9]?\d)))\.){3}(?:25[0-5]|2[0-4]\d|((1\d{2})|([1-9]?\d))))", ip_str)
        if matchobj == None:
            return False
        else:
            s = matchobj.group(0)
            if s == ip_str:
                return True
            else:
                return False


def getLatestProxys():
    r = requests.get(PROXY_IP_SOURCE_URL)
    if not r.status_code == requests.codes["ok"]:
        return None

    content = r.text
    soup = BeautifulSoup(content,"html.parser")
    # Retrieve the h2 tag with the text as "最新代理"
    h2_latest_tag = soup.find(h2_with_text_latest)    
    sibling = h2_latest_tag.find_next_sibling("table",class_ = "list")
    table = sibling
    retList = []

    ListTr = table.find_all("tr")
    for tr in ListTr:
        ListTd = tr.find_all("td")
        if len(ListTd) == 0:
            continue

        ipaddr = str(ListTd[0].get_text()).strip()
        port = str(ListTd[1].get_text()).strip()
        zone = str(ListTd[2].get_text()).strip().replace("\n","")
        nmd = str(ListTd[3].get_text()).strip()
        xy = str(ListTd[4].get_text()).strip()
        speed = str(ListTd[5].get_text()).strip()
        #time = str(ListTd[6].get_text()).strip()
        p = proxy(ipaddr, port, zone, nmd, xy, speed)
        retList.append(p)
    else:
        return retList


def h2_with_text_latest(tag):
        return tag.name == 'h2' and tag.get_text() == '最新代理'

if __name__  == '__main__':
    ret = getLatestProxys()
    if ret == None:
        print("Nothing retrieved.")
    else:
        for item in ret:
            print(item)

