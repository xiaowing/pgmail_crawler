'''
@author:    xiaowing
@license:   MIT License 
'''

import io, sys, shutil, getopt, time, random, queue, urllib.parse, pdb
sys.stdout = io.TextIOWrapper(sys.stdout.buffer,encoding='utf8')  # Change the default encode of stdout.

import requests
import psycopg2

from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from threading import Thread
from bs4 import BeautifulSoup

proxies = {
  "http": "http://192.168.1.200:8080",
  "https": "http://192.168.1.200:8080",
}

class PgmailCrawler:
    __base_url = 'http://www.postgresql.org/'
    __base_maillist_url = 'http://www.postgresql.org/list/'
    #dest_list = ['pgsql-patches/', 'pgsql-hackers/', 'pgsql-cluster-hackers/']
    dest_list = ['pgsql-patches/', 'pgsql-hackers/']

    def __init__(self, start_year, start_month, dest_no=0, host="localhost", port=5432, database="postgres", pguser="postgres", userpwd=""):
        # pretend as a request from browser
        self.headers = [
            {'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:34.0) Gecko/20100101 Firefox/34.0'},
            {'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.1.6) Gecko/20091201 Firefox/3.5.6'},
            {'User-Agent': 'Mozilla/5.0 (Windows NT 6.2) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.12 Safari/535.11'},
            {'User-Agent': 'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.2; Trident/6.0)'},
            {'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:40.0) Gecko/20100101 Firefox/40.0'},
            {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/44.0.2403.89 Chrome/44.0.2403.89 Safari/537.36'}
        ]

        self.link_list = queue.Queue()
        self.info_list = []
        self.pghost = host
        self.pgport = port
        self.database = database
        self.pguser = pguser
        self.password = userpwd
        self.start_time = date(start_year, start_month, 1)
        self.dest_no = dest_no

    def randHeader(self):
        return self.headers[random.randint(0, len(self.headers)-1)]

    def doCrawling(self):
        begin_date = self.start_time
        while True:
            crawling_link = PgmailCrawler.parsingDateToIndexUrl(begin_date, self.dest_no)
            next_link = self.__initLinksInternal(crawling_link, by_next = False)
            self.getMailInfos()
            self.saveMailInfosIntoDB()
            while next_link:
                crawling_link = next_link
                next_link = self.__initLinksInternal(next_link, by_next=True)
                self.getMailInfos()
                self.saveMailInfosIntoDB()
            begin_date = PgmailCrawler.parsingDateFromUrl(crawling_link)

            # Ignore the rest pages of current crawling year-month
            # skip to the next month
            begin_date = begin_date + relativedelta(months=+1)
            
            # The only exit of this infinite loop is the begin_date greater than today.
            if begin_date > date.today():
                #pdb.set_trace()
                return

    def __initLinksInternal(self, index_page_url, by_next = False):
        print(("Crawler %d Retriving mail links from %s..." %(self.dest_no, index_page_url)), flush=True)
        toget_flg = True
        while  toget_flg:
            try:
                #source_code = requests.Session().get(index_page_url, headers = self.randHeader(), proxies=proxies)
                source_code = requests.Session().get(index_page_url, headers = self.randHeader())
                toget_flg = False
                plain_text = source_code.text
                soup = BeautifulSoup(plain_text, "html.parser")

                for ul in soup.find_all('ul', id=False):
                    if ul.parent.name == 'li':
                        continue

                    if ul.parent.name == 'div' and ul.parent.attrs['id'] == 'pgSideNav':
                        continue

                    first_link = True
                    for li in ul.find_all('li'):
                        if by_next and first_link:
                            first_link = False
                        else:
                            self.link_list.put(li.a['href'])
                    else:
                        first_link = True

                # Retrieve the "href" attribute of <a href="xxxxx">Next</a>
                next_link_tag = soup.find(PgmailCrawler.a_with_text_next)
                if next_link_tag != None:
                    next_link = next_link_tag['href']
                    next_link = urllib.parse.urljoin(PgmailCrawler.__base_url, next_link)
                    if next_link != index_page_url:
                        return next_link
                return None

            except requests.exceptions.ConnectionError:
                time.sleep(30)
            except Exception as e:
                print("Crawler %d encountered an error while crawling %s. Error type: %s, Message: %s" %(self.dest_no, index_page_url, type(e),e))
                time.sleep(1)


    def getMailInfos(self):
        cnt = 0
        while not self.link_list.empty():
            link = self.link_list.get()
            mail_link = urllib.parse.urljoin(PgmailCrawler.__base_url, link)
            self.__getMailInfoFromLink(mail_link)

    def saveMailInfosIntoDB(self):
        if len(self.info_list) > 0:
            print("Crawler %d saving data to DB." %self.dest_no)
            self.__insertMailInfoFromList()
            self.info_list = []


    def __getMailInfoFromLink(self, link):
        try:
            #page_source = requests.Session().get(link, headers = self.randHeader(), proxies=proxies)
            page_source = requests.Session().get(link, headers = self.randHeader())
            if not page_source.status_code == requests.codes["ok"]:
                return

            plain_text = page_source.text
            soup = BeautifulSoup(plain_text, "html.parser")
            msgtb = soup.find('table', class_='message')
        
            infodict = { 'sender': "", 'title': "", 'datetime': ""}

            for th in msgtb.find_all('th'):    
                if th.string == 'From:':
                    td = th.find_next_sibling('td')
                    infodict['sender'] = td.get_text()
                if th.string == 'Subject:':
                    td = th.find_next_sibling('td')
                    infodict['title'] = td.get_text()
                if th.string == 'Date:':
                    td = th.find_next_sibling('td')
                    infodict['datetime'] = td.get_text()
            else:
                info = MailInfo(url=link, title_text=infodict['title'], date_text=infodict['datetime'], from_text=infodict['sender'])
                self.info_list.append(info)

        except requests.exceptions.ConnectionError:
                time.sleep(30)
        except Exception as e:
                print("Crawler %d encountered an error while crawling %s. Error type: %s, Message: %s" %(self.dest_no, link, type(e),e))
                time.sleep(1)

    def __insertMailInfoFromList(self):

        if self.password == "":
            conn = psycopg2.connect(host = self.pghost, port = self.pgport, database = self.database, user = self.pguser)
        else:
            conn = psycopg2.connect(host = self.pghost, port = self.pgport, database = self.database, user = self.pguser, password = self.password)

        conn.autocommit = True
        try:
            cur = conn.cursor()
            for mi in self.info_list:
                try:
                    cur.execute("INSERT INTO sch_crawler.mail_info VALUES (%(sender)s, %(title)s, %(time)s, %(url)s);",
                            {'sender': mi.sender, 'title': mi.title, 
                            'time': mi.date, 'url': mi.url})
                except psycopg2.DatabaseError as ex:
                    print("Crawler %d encountered an Database error. SQLSTATE: %s, MESSAGE: %s."  %(self.dest_no, ex.pgcode, ex))
            cur.close()
        except psycopg2.Error as e:
            print("Crawler %d encountered an %s error. SQLSTATE: %s, MESSAGE: %s."  %(self.dest_no, type(e), e.pgcode, e))
        finally:
            conn.close()

    @classmethod
    def a_with_text_next(cls, tag):
        return tag.name == 'a' and tag.get_text() == 'Next'

    @classmethod
    def parsingDateFromUrl(cls, url):
        if not isinstance(url, str):
            raise TypeError()

        url = url.rstrip('/')
        slash_index = url.rfind('/')
        if slash_index == -1:
            raise ValueError()

        timestamp_string = url[(slash_index+1):]

        format_string = ["%Y%m%d%H%M", "%Y-%m"]

        try:
            t = time.strptime(timestamp_string, format_string[0])
            dt = date(*t[:3])
        except ValueError:
            t = time.strptime(timestamp_string, format_string[1])
            dt = date(*t[:3])
        return dt

    @classmethod 
    def parsingDateToIndexUrl(cls, dt, destidx=0):
        if not isinstance(dt, date):
            raise TypeError()
        ym = dt.strftime('%Y-%m')
        url = urllib.parse.urljoin(PgmailCrawler.__base_maillist_url, PgmailCrawler.dest_list[destidx])
        url = urllib.parse.urljoin(url, ym)
        return url

class MailInfo:
    def __init__(self, url, title_text, date_text, from_text):
        self.url = url
        self.title = title_text

        # convert the text format of date into datetime
        try:
            tm = time.strptime(date_text, "%Y-%m-%d %H:%M:%S")
            self.date = datetime(*tm[:6])
        except ValueError as e:
            # since the date_text is incorrect, set the datetime as now
            self.date = datetime.now()
        

        # the from_text is similar to "Tom Lane <tgl(at)sss(dot)pgh(dot)pa(dot)us>"
        lgt_index = from_text.find('<')
        rgt_index = from_text.rfind('>')
        if lgt_index >= 0:
            if rgt_index >= 0:
                new_from_text = from_text[(lgt_index+1):rgt_index]
            else:
                new_from_text = from_text[(lgt_index+1):]
        else:
            if rgt_index >= 0:
                new_from_text = from_text[:rgt_index]
            else:
                new_from_text = from_text
        self.sender = new_from_text.replace('(at)', '@').replace('(dot)', '.')

    def __str__(self):
        return str("%s, %s, %s" %(self.sender, self.title, self.date))


def main(argv):
    # handler the input arguments
    if len(argv) < 2 or len(argv) > 16:
        print("Invalid arguments.")
        sys.exit(1)
    
    format_string = "y:m:h:p:d:u:w:v"
    
    try:
        opts, args = getopt.getopt(sys.argv[1:], format_string, ["version"])
    except getopt.GetoptError as err:
        print(str(err))
        sys.exit(2)
    
    start_year = 0
    start_month = 0
    host = "localhost"
    port = 5432
    database = "postgres"
    username = "postgres"
    password = ""
    
    for op, value in opts:
        if op == "-y":
            try:
                start_year = int(value)
                if start_year < 1997 or start_year > date.today().year:
                    raise ValueError
            except ValueError:
                print("Invalid year number: %s" %value)
                sys.exit(3)
        elif op == "-m":
            try:
                start_month = int(value)
                if start_month < 1 or start_month > 12:
                    raise ValueError
            except ValueError:
                print("Invalid month number: %s" %value)
                sys.exit(3)
        elif op == "-h":
            host = value
        elif op == "-p":
            try:
                port = int(value)
                if port < 0 or port > 65535:
                    raise ValueError
            except ValueError:
                print("Invalid port number: %s" %value)
                sys.exit(3)
        elif op == "-d":
            database = value
        elif op == "-u":
            username = value
        elif op == "-w":
            password = value
        elif op in ("-v", "--version"):
            version()
            sys.exit(0)
        else:
            print("Unhanded option.")
            sys.exit(3)

    if start_year == 0 or start_month == 0:
        print("It's necessary to input start year and start month")
        sys.exit(3)
    
    if(len(args) > 0):
        print("Unrecognised arguments.")
        sys.exit(3)
    
    # ping the PostgreSQL server to make sure the data can be inserted into database
    if not ping_pg_server(host=host, port=port, database=database, user=username, pwd=password):
        print("Connection to PostgreSQL instance(%s:%d %s) failed."  %(host, port, database))
        sys.exit(3)

    # create crawlers and start retrieving data, Thread : Crawler = 1:1
    start_time = datetime.now()
    thread_list = []
    for x in range(0, len(PgmailCrawler.dest_list)):
        crawler = PgmailCrawler(start_year=start_year, start_month=start_month, dest_no=x, host=host, port=port, database=database, pguser=username, userpwd=password)
        t = Thread(target=sub_crawling_job, args=(crawler,))
        t.start()
        thread_list.append(t)

    for element in thread_list:
        if element.is_alive():
            element.join()
    else:
        end_time = datetime.now()
        print("The whole duration is %s" %(end_time - start_time))
        time.sleep(3)

    sys.exit(0)

def ping_pg_server(host, port, database, user, pwd):
    conn = None
    result = True
    try:
        if pwd == "":
            conn = psycopg2.connect(host = host, port = port, database = database, user = user)
        else:
            conn = psycopg2.connect(host = host, port = port, database = database, user = user, password = pwd)

        conn.autocommit = True
        try:
            cur = conn.cursor()
            cur.execute("SELECT 1;")
            cur.fetchone()
            cur.close()
        except psycopg2.Error as e:
            raise e
        finally:
            conn.close()
    except psycopg2.Error as ex:
        print("SQLSTATE: %s, MESSAGE: %s."  %(ex.pgcode, ex))
        result = False

    return result


def sub_crawling_job(crawler):
    if not isinstance(crawler, PgmailCrawler):
        print("Incorrect argument. PgmailCrawler expected.", flush=True)
        return

    start_time = datetime.now()
    print(("Crawler %d Start crawling at %s" %(crawler.dest_no, start_time)), flush=True)
    try:
        crawler.doCrawling()
        end_time = datetime.now()
        print("Crawler %d's crawling ended at %s" %(crawler.dest_no, end_time))
    except Exception as ex:
        end_time = datetime.now()
        print("Crawler %d's encountered an unexpected error and the job was interrupted at %s. Error: %s, Message: %s" 
              %(crawler.dest_no, end_time, type(ex), ex))
    print(("The duration of Crawler %d's crawling is %s" %(crawler.dest_no, (end_time - start_time))), flush=True)

def version():
    print ("PgmailCrawler v0.1.0")

if __name__ == '__main__':
    main(sys.argv)


