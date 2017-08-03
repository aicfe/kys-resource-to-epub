# -*- coding: utf-8 -*-

import json
import mysql.connector
import os
import re
import uuid
from ebooklib import epub

output_dir = os.getcwdu() + '/build'

oid = '100100010007'

sections = ('','首页','小喇叭','识字通','资料城','推荐网址','作者简介','课文学习','拓展资源','习作园地','背景知识','音频材料','教学资料','<!-- 备用 -->','阅读方法指导','文本探究','拓展阅读','拓展写作','主题阅读','口语、写作指导','写作园地','综合学习','活动设计','抛砖引玉','<!-- 备用 -->','Index','Word','Dialogue','Reading','Saying','Song','Rhythm','Game','Practice','Website','<!-- 备用 -->','Share','Listening','Drill','Exam','Grammar','Writing','Other','<!-- 备用 -->','<!-- 备用 -->','<!-- 备用 -->','<!-- 备用 -->','知识统筹','问题情境','实践演练','拓展阅读','园丁资料','探究活动','资源推荐','基础知识')

pattern_style = re.compile(r'\sstyle\s*="[^"]*"', re.I)
pattern_font = re.compile(r'<font[^>]*>', re.I)

def normalize_content(content):
    if content:
        content = pattern_style.sub('', content)
        content = pattern_font.sub('<font>', content)
    return content

def generate_epub(parent_dir, id, sectionId, title, content):
    content = normalize_content(content)
    
    book = epub.EpubBook()
    book.FOLDER_NAME = 'OEBPS'

    # add metadata
    book.set_identifier(str(uuid.uuid4()))
    book.set_title(title)
    book.set_language('zh')

    book.add_author('lcell')

    # defube style
    #style = '''p { text-indent: 2em; }'''
    style = ''
    
    default_css = epub.EpubItem(uid="style_default", file_name="style/default.css", media_type="text/css", content=style)
    book.add_item(default_css)

    c1 = epub.EpubHtml(title=title, file_name='1.xhtml', lang='zh')
    c1.content = content
    c1.add_item(default_css)

    # add chapters to the book
    book.add_item(c1)

    # create table of contents
    book.toc = [ epub.Link('1.xhtml', title, 'content') ]

    # add navigation files
    book.add_item(epub.EpubNcx())
    #book.add_item(epub.EpubNav())

    # create spine
    book.spine = [ c1 ]

    # create epub file
    dir = output_dir + parent_dir + '/' + unicode(sections[int(sectionId)], 'utf8')
    if not os.path.exists(dir):
        os.makedirs(dir)
    file_path = dir + '/' + str(id) + '-' + title + '.epub'
    #file_path = title + '.epub'
    epub.write_epub(file_path, book, {})

def read_outlines(cnx, parent_id):
    cursor = cnx.cursor()
    cursor.execute("SELECT * FROM outline where PARENTID = '" + parent_id + "'")
    result = cursor.fetchall()
    cursor.close()
    return result

def read_contents(cursor, outline_id, dir):
    cursor.execute("select ro.id,rd.sectionId,rd.title,rc.content from resourceoutline ro left join resourcedetail rd on ro.detailID = rd.id left join resourcecontent rc on rd.contentID = rc.id where ro.outlineID='" + outline_id + "'")

    row = cursor.fetchone()
    while row is not None:
        generate_epub(dir, row[0], row[1], row[2], row[3])
        row = cursor.fetchone()
        #break

def main():
    with open('config.json') as json_data:
        cfg = json.load(json_data)
    
    cnx = mysql.connector.connect(user = cfg['mysql']['user'],
                                  password = cfg['mysql']['password'],
                                  host = cfg['mysql']['host'],
                                  port = cfg['mysql']['port'],
                                  database = cfg['mysql']['database'])

    try:
        outlines = read_outlines(cnx, oid)
        cursor = cnx.cursor()
        for ol in outlines:
            read_contents(cursor, ol[0], ol[3])
            #break
    finally:
        cnx.close()

if __name__ == "__main__": main()

