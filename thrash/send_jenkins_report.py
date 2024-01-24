# coding: utf8

import smtplib
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.utils import parseaddr, formataddr
import time as Time
import re
import os
import csv
import requests
import json
from prettytable import PrettyTable
from colorama import init, Fore, Back, Style
import pandas as pd
import subprocess

base_url = "http://59.111.91.248:8080/"
return_type = "api/json"
project_url = {"ut": "job/curve_ut_daily/", \
"robot_normal": "job/curve_robot_interface_daily/",\
"robot_failover": "job/curve_failover_testjob/",\
"pjdtest": "job/curve_fs_pjdtest_daily/",\
"fs_failover": "job/curve_fs_failover_test/",\
"centos_test": "job/curvefs_centos_daily/",\
"ubuntu_test": "job/curvefs_ubuntu_daily/"}

feature_commit = ""
develop_commit = ""



def run_exec(cmd, lock=None):
    '''
    执行指定的命令，在当前进程执行，判断命令是否执行成功，执行失败抛异常

    @param log_id 日志打印的id，暂无
    @param cmd 要执行的命令
    @param lock 参数lock是一个锁，如果不为None，则命令执行过程中是要加锁的
    @return: None

    '''
    try:
        if lock:
            lock.acquire()
        ret_code = subprocess.call(cmd, shell=True)
    except Exception as e:
        raise e
    finally:
        if lock:
            lock.release()

    if ret_code == 0:
        return 0
    else:
        return -1

def run_exec2(cmd, lock=None):
    '''
    执行指定的命令,在当前进程执行，返回输出结果，执行失败为

    @param log_id 日志打印的id，暂无
    @param cmd 要执行的命令
    @param lock 参数lock是一个锁，如果不为None，则命令执行过程中是要加锁的
    @return: 命令输出结果

    '''
    out_msg = ''
    try:
        if lock:
            lock.acquire()
        out_msg = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
    except Exception as e:
        raise e
        #  run_err_msg = traceback.format_exc()

        #  return False
    finally:
        if lock:
            lock.release()
#    return out_msg.readlines()
    return out_msg.strip()

def get_last_builds(project_url, times):
    r = requests.get(base_url + project_url + return_type,auth=('netease','netease'))
    if r.status_code != 200:
        print r.status_code
        return -1
    else:
        #print type(r.content)
        json_r = json.loads(r.content)
        last_build_number = json_r["builds"][times]["number"]
        print "lastbuildnumber is ....."
        print last_build_number
        last_build_url = json_r["builds"][times]["url"]
        #print last_build_number
        #print last_build_url 
        return [last_build_number, last_build_url]


def get_build_info(project_url, times):
    global feature_commit,develop_commit
    build_number = get_last_builds(project_url, times)[0]
    build_url = get_last_builds(project_url, times)[1]
    r = requests.get(build_url + return_type,auth=('netease','netease'))
    if r.status_code != 200:
        print r.status_code
        return -1
    else:
        json_r = json.loads(r.content)
        result = json_r["result"]
	if result == "FAILURE":
	    result = Fore.RED + result
	else:
            result = Fore.GREEN + result
        duration = json_r["duration"]/1000/60
        url = json_r["url"]
        build = json_r["number"]
        action = json_r["actions"]
        cases_total = 0
        if project_url == "view/curve/job/curve/job/braft-jepsen-daily/":
           if int(build) % 2  == 0:
               branch = "feature"
               commit = feature_commit
           else:
               branch = "develop"
               commit = develop_commit
        elif project_url == "job/curvefs_centos_daily/":
            return [build, result, duration, url]
        elif project_url == "job/curvefs_ubuntu_daily/":
            return [build, result, duration, url]
        else:
#           if project_url == "job/curve_fs_pjdtest_daily/":
#               parameters = action[0]["parameters"]
#           else:
           parameters = action[1]["parameters"]
           commit = ""
           for p in parameters:
               if p["name"] == "SHORT_HEAD":
                   commit = p["value"]
               elif p["name"] == "BRANCH":
                   branch = p["value"]
#           if commit == "":
#               commit == "not get commit ID"
           branch = "master"
           if branch == "feature":
               feature_commit = commit
           elif branch == "develop":
               develop_commit = commit
           if action[4].has_key('totalCount'):
               cases_total = action[4]["totalCount"]
           if action[5].has_key('totalCount'):
               cases_total = action[5]["totalCount"]
 

        if project_url == "job/curve_ut_daily/":
           cmd = "curl -u netease:netease %sconsole | grep lines"%url
           print "cmd is %s"%cmd
#           cmd = "curl http://ci.storage.netease.com/view/curve/job/curve/job/curve_build_unittest_and_coverage_daily/917/console | grep lines"
           try:
               out = run_exec2(cmd)
               lines = out.split("\n")
#               print "lines is %s"%lines
               lines_cov = re.search(r'\d+.*%',lines[-1]).group()
           except:
#               print lines_cov
               lines_cov = "fail"
           print "lines_cov is %s"%lines_cov
          
           cmd = "curl -u netease:netease %sconsole | grep branches"%url
#           cmd = "curl http://ci.storage.netease.com/view/curve/job/curve/job/curve_build_unittest_and_coverage_daily/917/console | grep lines"
           try:
               out = run_exec2(cmd)
               branches = out.split("\n")
#               print "lines is %s"%lines
               branches_cov = re.search(r'\d+.*%',branches[-1]).group()
           except:
#               print lines_cov
               branches_cov = "fail"
           print "branches_cov is %s"%branches_cov 
           return [build , branch, commit, lines_cov, branches_cov, result, duration, url]

        elif project_url == "job/curve_fs_pjdtest_daily/":
           cmd = "curl -u netease:netease %sconsole | grep pjdtest_fail_test_num"%url
           print "cmd is %s"%cmd
#           cmd = "curl http://ci.storage.netease.com/view/curve/job/curve/job/curve_fs_pjdtest_daily/917/console | grep pjdtest_fail_test_num"
           try:
               out = run_exec2(cmd)
               fail_num = out.split("\n")
#               print "lines is %s"%lines
               fail_num = re.search(r'\d+',fail_num[-1]).group()
           except:
#               print lines_cov
               fail_num = "fail"
           print "fail_num is %s"%fail_num
           return [build , branch, commit, fail_num, result, duration, url]
#        print commit
#        branch = "feature"
#        n1= build_number % 2
#        if n1 == 0:
#           branch = "feature"
#        else:
#           branch = "develop"
        if cases_total == 0:
           return [build , branch, commit, result, duration, url]
        else:
#           return [build , branch, commit, cases_total, result, duration, url]
           return [build , branch, commit, result, duration, url]

#get_last_build(project_url["robot_failover"])
#print a

def draw_table(project_url):
    list_project = [project_url.split("/")[-2]]
    table = PrettyTable(["Project", "Build_Number", "Branch","commit_id", "Result", "Duration(mins)", "Log_Url"])
    for i in range(0,2):
        list_job_info = get_build_info(project_url, i)
        #table = PrettyTable(["Project", "Build_Number", "Result", "Duration(mins)", "Log_url"])
        new_row = list_project + list_job_info
        table.add_row(new_row)
    print table
    return table

def convertToHtml(project_url):
    #将数据转换为html的table
    #result是list[list1,list2]这样的结构
    #title是list结构；和result一一对应。titleList[0]对应resultList[0]这样的一条数据对应html表格中的一列
    if project_url == "job/curve_ut_daily/":
       title = ["Project", "Build_Number", "Branch","commit_id", "lines_cov","branches_cov","Result", "Duration(mins)", "Log_Url"]
    elif project_url == "view/curve/job/curve/job/braft-jepsen-daily/":
       title = ["Project", "Build_Number", "Branch","commit_id", "Result", "Duration(mins)", "Log_Url"]
    elif project_url == "job/curve_fs_pjdtest_daily/":
       title = ["Project", "Build_Number", "Branch","commit_id", "fail_num", "Result", "Duration(mins)", "Log_Url"]
    elif project_url == "job/curvefs_centos_daily/":
        title = ["Project", "Build_Number", "Result", "Duration(mins)", "Log_Url"]
    elif project_url == "job/curvefs_ubuntu_daily/":
        title = ["Project", "Build_Number", "Result", "Duration(mins)", "Log_Url"]
    else:
#       title = ["Project", "Build_Number", "Branch","commit_id","cases_total", "Result", "Duration(mins)", "Log_Url"]
       title = ["Project", "Build_Number", "Branch","commit_id", "Result", "Duration(mins)", "Log_Url"]
    list_project = [project_url.split("/")[-2]]
    result = [[0 for i in range(3)] for i in range(3)]
    for i in range(0,3):
        result[i] =list_project + get_build_info(project_url, i)
    print result 

    final = [[0 for i in range(len(title))] for i in range(len(title))]
    for i in range(0,len(title)):
        a = []
        for t in result:
            a.append(t[i])
        final[i] = a
    d = {}
    index = 0
    for t in title:
        d[t]=final[index]
        index = index+1
    pd.set_option('display.max_colwidth', -1)
    pd.set_option('colheader_justify', 'center')
    df = pd.DataFrame(d)
    df = df[title]
#    h = df.to_html(index=False)
    h = df.to_html(classes='mystyle')
    return h

def write_to_file(jepsen_table, ut_table, robot_normal_table, robot_failover_table):
    with open("table.txt", 'w+') as f:
         f.write("this is curve ut daily build")
         f.write("\n")
         f.write("\n")
         f.write(str(ut_table))
         f.write("\n")
         f.write("\n")
         f.write("this is robot normal case daily build")
         f.write("\n")
         f.write("\n")
         f.write(str(robot_normal_table))
         f.write("\n")
         f.write("\n")
         f.write("this is robot failover case daily build")
         f.write("\n")
         f.write("\n")
         f.write(str(robot_failover_table))
         f.write("\n")
         f.write("\n")

def change_html_file():
#    cmd = R"sed -i  's/FAILURE/\<font color\=\"\#FF0000\"\>FAILURE\<\/font\>/g' table.html"
    cmd = R"sed -i  's/.[^ ]*FAILURE/\<td bgcolor\=\"\#FF0000\"\>FAILURE/g' table.html"
    ret = run_exec(cmd)
#    cmd = R"sed -i  's/SUCCESS/\<font color\=\"\#00F\"\>SUCCESS\<\/font\>/g' table.html"
    cmd = R"sed -i  's/.[^ ]*SUCCESS/\<td bgcolor\=\"\#87cefa\"\>SUCCESS/g' table.html"
    ret = run_exec(cmd)
    cmd = R"sed -i  's/http.[^ ]*[0-9]\//<a href=&>&<\/a>/g' table.html"
    ret = run_exec(cmd)
def send_mail():
    sender = "storage_mgm@163.com"
    passwd = "storage@Netease"
#    key = "netease163"
    key = "XAGSASBPULRJOVIU"
    receivers = ["curve-dev@list.nie.netease.com","cloud-qa@hz.netease.com"]
#    receivers = ["chenyunhui@corp.netease.com"]
#    receivers2 = ["cloud-qa@hz.netease.com"]
    f = open("table.html")
    content = f.read()
    f.close()
    message = MIMEText(content, 'html', 'utf-8')
    message['From'] = sender
    message['To'] = ",".join(receivers)

    subject = 'curve每日持续集成报表'
    message['Subject'] = Header(subject, 'utf-8')

#try:
    smtpObj = smtplib.SMTP()
    smtpObj.connect('smtp.163.com')
    smtpObj.login(sender, key)
    smtpObj.sendmail(sender, receivers, message.as_string())
#    smtpObj.sendmail(sender, receivers2, message.as_string())
    print "ok"

def main():
#    perf_table = draw_table(project_url["perf"])
    ut_table = convertToHtml(project_url["ut"])
#    normal_table = convertToHtml(project_url["robot_normal"])
#    failover_table = convertToHtml(project_url["robot_failover"])
    fs_failover_table = convertToHtml(project_url["fs_failover"])
    pjdtest_table = convertToHtml(project_url["pjdtest"])
#    centos_table = convertToHtml(project_url["centos_test"])
#    ubuntu_table = convertToHtml(project_url["ubuntu_test"])
#    jepsen_table = convertToHtml(project_url["jepsen"])
    html_string = '''<head>
        <style>
        .mystyle{
             font-size: 11pt;
             border-collapse: collapse;
             border: 1px solid silver;
             font-family:"Trebuchet MS", Arial, Helvetica, sans-serif;
        }
        .mystyle td, th {
             padding:3px 7px 2px 7px;
             text-align: center;
             border:1px solid #98bf21;
        }
        .mystyle thead{
        color:white;
        background-color:#A7C942;
        }
        .mystyle tr.light td {
            background-color:#EAF2D3;
        }
        .mystyle tr:nth-child(even){
            background-color:#EAF2D3;
        }
        .mystyle tr:hover {
             background: silver;
             cursor: pointer;
        }
        h1{
             font-family: Arial, sans-serif;
             font-size: 24px;
             color: #369;
             padding-bottom: 4px;
             border-bottom: 1px solid #999;
        }
        </style>
    </head>
    ''' 
#    write_to_file(perf_table)
    with open("table.html", 'w+') as f:
        f.write(html_string)
        f.write(R"<h1>this unittest table</h1>")
        f.write(ut_table)
#        f.write(R"<h1>this robot interface table</h1>")
#        f.write(normal_table)
#        f.write(R"<h1>this robot failover table</h1>")
#        f.write(failover_table)
        f.write(R"<h1>this fs failover table</h1>")
        f.write(fs_failover_table)
        f.write(R"<h1>this fs pjdtest table</h1>")
        f.write(pjdtest_table)
#        f.write(R"<h1>this centos test table</h1>")
#        f.write(centos_table)
#        f.write(R"<h1>this ubuntu test table</h1>")
#        f.write(ubuntu_table)
#        f.write(R"<h1>this jepsen table</h1>")
#        f.write(jepsen_table)
#    print normal_table
    change_html_file()
    send_mail()
main()
