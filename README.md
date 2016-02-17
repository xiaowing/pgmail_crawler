PgmailCrawler
=============

###Summary
我的第一个Python爬虫，作用是从PostgreSQL官网的邮件归档页面中扒取所需信息(邮件标题，送信人，送信时间，邮件的归档地址)，并将这些信息记录在指定的PostgreSQL数据库中.

###Usage (Current version)

该爬虫的启动方式如下：
````
$python3 PgmailCrawler.py -y 年份 -m 月份 -h PostgreSQL服务器域名 -p PostgreSQL实例端口 -d 数据库名 -u PostgreSQL用户名 -w 密码
````

下面两个选项用于指定从哪年哪月的归档邮件开始扒取信息
* -y:  年份(大于1996. 毕竟PostgreSQL这个名字是从1996年才有).必须选项.
* -m:  月份.必须选项.

下面的选项用于指定用于保存数据的PostgreSQL数据源(风格与psql尽量保持一致).
* -h:  PostgreSQL服务器的域名(或ip地址). 非必须选项, 默认值为"localhost"
* -m:  PostgreSQL实例所监听的端口号.     非必须选项, 默认值为"5432"
* -d:  所连接的PostgreSQL数据库名.       非必须选项, 默认值为"postgres"
* -u:  PostgreSQL的数据库用户名.         非必须选项, 默认值为"postgres"
* -w:  PostgreSQL的数据库用户的密码.     非必须选项(如在pg_hda中设置的认证级别为"trust"，该选项可省略)

###Dependencies
* requests (2.7+)
* beautifulsoup4 (4.4+)
* psycopg2 (2.6+)

###TODO
眼下考虑待改进的项目如下:
- [ ] 加入连接池(优化).
- [ ] 加入线程池将一个爬虫内部扒取邮件信息的动作也予以多线程化(优化).

