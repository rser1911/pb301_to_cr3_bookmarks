import struct
import os
import sys
import chardet
from lxml import etree

DEBUG = 0

if not DEBUG:
    print ('<?xml version="1.0" encoding="utf-8"?>\n<FictionBookMarks>')

from html.parser import HTMLParser
class MyHTMLParser(HTMLParser):
    def __init__(self, bookmarks):
        HTMLParser.__init__(self)
        
        self.para = -1
        self.body = 0
        self.coverpage = 0
        self.annotation = 0
        
        self.insert = 1
        self.paraexists = 0
        self.section = 0
        self.poem = 0
        self.title = 0
        
        self.paragraphsBeforeBodyNumber = -1
        self.coverImageReference = ""
        self.sectionContainsRegularContents = 0
        self.myTextParagraphExists = 0
        
        self.booktitle = ""
        self.bookauthor = ""
        self.bookmarks = bookmarks
        
        self.cur_tags = {}
        self.stack_tags = []
        self.stack_tree = []
    
    
    def handle_starttag(self, tag, attrs):
        global DEBUG
        
        if tag in self.cur_tags:
            self.cur_tags[tag] += 1
        else:
            if tag == 'fictionbook':
                tag = 'FictionBook'
            self.cur_tags[tag] = 1
            
        self.stack_tags.append(self.cur_tags)
        self.stack_tree.append(tag)
        self.cur_tags = {}
        
        if self.body or self.coverpage or self.annotation:
            if tag in ['p', 'v', 'subtitle', 'text-author', 'date']: 
                # beginParagraph
                self.para += 1
                self.insert = 0
                self.paraexists = 1
            elif tag in ['stanza', 'empty-line']: 
                # beginParagraph + endParagraph
                self.para += 1
                self.insert = 0
                self.paraexists = 0
                
                if self.title == 0:
                    self.sectionContainsRegularContents = 1 # ???
            elif tag in ['image']:
                # self.sectionContainsRegularContents = 1 # ???
                ref = ""
                for attr in attrs:
                    if attr[0][-4:] == 'href':
                        ref = attr[1]
                        break

                if ref != "" and ref[0] == "#":
                    if self.para != self.paragraphsBeforeBodyNumber or self.coverImageReference != ref:
                        if self.paraexists == 0: 
                            # addImageReference
                            self.para += 1
                            self.insert = 0
                    if self.coverpage == 1:
                        self.coverImageReference = ref

            elif tag in ['epigraph']:
                self.title = 1
            elif tag in ['title']:
                self.title = 1
                if self.poem == 0 and self.section == 0:
                    # insertEndOfSectionParagraph
                    if self.insert == 0 and self.sectionContainsRegularContents == 1:
                        self.para += 1
                        self.insert = 1
                        self.sectionContainsRegularContents = 0
    
            elif tag == 'section':
                self.section += 1
                # insertEndOfSectionParagraph
                if self.insert == 0  and self.sectionContainsRegularContents == 1:
                    self.para += 1
                    self.insert = 1
                    self.sectionContainsRegularContents = 0
                    
            elif tag == 'poem':
                self.poem = 1

        if tag == 'body':
            if self.booktitle != None and not DEBUG:
                print("      <doc-title>" + self.booktitle + "</doc-title>")
                print("      <doc-author>" + self.bookauthor[1:] + "</doc-author>")
                print("    </file-info>\n    <bookmark-list>")
                self.booktitle = None
            
            self.body = 1
            self.paragraphsBeforeBodyNumber = self.para
        elif tag == 'coverpage':
            self.coverpage = 1
        elif tag == 'annotation':
            self.annotation = 1

        # print(str(self.para) + "\t > " + tag)
        # pass


    def handle_endtag(self, tag):
        self.cur_tags = self.stack_tags.pop()
        self.stack_tree.pop()
        
        if self.body or self.coverpage or self.annotation:
            if tag in ['p', 'v', 'subtitle', 'text-author', 'date']:
                # endParagraph
                self.paraexists = 0
                
            elif tag in ['stanza']:
                # beginParagraph + endParagraph
                self.para += 1
                self.paraexists = 0
            
            elif tag == 'section':
                self.section -= 1
            elif tag == 'poem':
                self.poem = 0
            elif tag in ['title', 'epigraph']:   
                self.title = 0
            
        if tag == 'body':
            self.body = 0
            
        elif tag == 'coverpage':
            self.coverpage = 0
            if self.body == 0:
                # insertEndOfSectionParagraph
                if self.insert == 0 and self.sectionContainsRegularContents == 1:
                    self.para += 1
                    self.insert = 1
                    self.sectionContainsRegularContents = 0
                    
        elif tag == 'annotation':
            self.annotation = 0
            if self.body == 0:
                # insertEndOfSectionParagraph
                if self.insert == 0 and self.sectionContainsRegularContents == 1:
                    self.para += 1
                    self.insert = 1
                    self.sectionContainsRegularContents = 0
                    
        # print(str(self.para) + "\t < " + tag)
        # pass

    
    def handle_data(self, data):
        global DEBUG
        if data == "" or data.isspace():
            return
        
        if len(self.bookmarks) and self.bookmarks[0][0] <= self.para and not DEBUG:
            i = self.bookmarks[0]
            self.bookmarks.remove(i)

            res = ""
            for j in zip(self.stack_tree, self.stack_tags):
                res = res + "/" + j[0] + "[" + str(j[1][j[0]]) + "]"
            # print(res)
            
            print('      <bookmark type="position" shortcut="' + i[1] + '" page="0">')
            print('        <start-point>' + res + '/text()[1].0</start-point>')
            print('        <end-point/>')
            print('        <comment-text>bookmark # ' + i[1] + '</comment-text>')
            print('        <selection-text/>')
            print('        <header-text/>')
            print('      </bookmark>')
            self.xpath = None
            
                        
        if self.stack_tree[1] == "description" and self.stack_tree[2] == "title-info":
            if self.stack_tree[-1] == "book-title":
                self.booktitle = data
                
            if self.stack_tree[-2] == "author":
                if self.stack_tree[-1] in ["first-name", "last-name"]:
                    self.bookauthor += " " + data
                    
        if self.body or self.coverpage or self.annotation:
            if self.paraexists == 1 and self.title == 0:
                self.sectionContainsRegularContents = 1

        if DEBUG:
            for i in self.bookmarks:
                if i[0] == 0 or abs(i[0] - self.para) > 20:
                    continue
                    
                if data[0:len(i[1])] == i[1]:
                    print ("\t" + str(i[0]) + '\t' + str(self.para) + '\t' + str(i[0] - self.para))

        # pass
        
def check(filedir, name, af0):
    if not DEBUG:
        print ("  <file>\n    <file-info>")
        print ("      <doc-filename>" + name + "</doc-filename>")
        print ("      <doc-filepath>" + filedir + "/</doc-filepath>")
        print ("      <doc-filesize>" + str(os.stat(filedir + "/" + name).st_size) + "</doc-filesize>")

    bookmarks = []
    
    if DEBUG:
        print()
        print()
        print("\t" + name)
        print()
        print("\tmark#\tpara\tword\tletter")
        print("\t===\t====\t====\t======")
        
    with open(af0, "rb") as f:
        f.seek(36)
        n = struct.unpack('i', f.read(4))[0]
        i = 1
        while n > 0:
            n = n -1
            pos = struct.unpack('l', f.read(8))[0]
            
            para = (pos >> 40) & 0xffffff;
            word = (pos >> 16) & 0xffffff;
            letter = pos & 0xffff;
            
            if DEBUG:
                print("\t" + (" " if i < 10 else "") + str(i), end='')
                print("\t" + str(para) + "\t" + str(word) + "\t" + str(letter))
            bookmarks.append([para, str(i)]) 
            i += 1
            
        bookmarks.sort()
     
    if DEBUG:
        print()
        print("\tpara\tfound\tdiff")
        print("\t====\t=====\t====")
        bookmarks = testmarks[testbook.index(name)]

    parser = MyHTMLParser(bookmarks)
    encoding = chardet.detect(open(filedir + "/" + name, 'rb').read()[:10000])['encoding']
    parser.feed(open(filedir + "/" + name,'r',encoding=encoding).read())
    
    if not DEBUG:
        print("    </bookmark-list>\n  </file>")
    
if DEBUG:
    testbook = []
    testmarks = []

    # 1
    testbook.append("filename1.fb2")
    test = []
    # Take position from table in col named para
    # Open bookmark on your pocketbook
    # Copy starting of paragraph that you see first (can be on prev page)
    test.append([ 10 , "first words of paragraph 10" ])
    test.append([ 20 , "first words of paragraph 20" ])
    test.append([ 30 , "first words of paragraph 30" ])
    testmarks.append(test)

    # 2
    testbook.append("filename2.fb2")
    test = []
    test.append([ 4 , "first words of paragraph 4" ])
    test.append([ 15 , "first words of paragraph 15" ])
    testmarks.append(test)

mydir = sys.argv[1]

for (dirpath, dirnames, filenames) in os.walk(mydir):
    for fname in filenames:
        path = dirpath + "/" + fname
        if len(fname) < 7 or fname[-7:] != "fb2.af0":
            continue
            
        n = 0
        with open(path, "rb") as f:
            f.seek(36)
            tmp = f.read(4)
            if len(tmp) == 4:
                n  = struct.unpack('i', tmp)[0]

        if n == 0:
            continue
            
        if not os.path.isfile(dirpath.replace("/system/state/", "/") + "/" + fname[:-4]):
            continue
         
        if DEBUG and fname[:-4] not in testbook:
            continue

        # print(path)
        check(dirpath.replace("/system/state/", "/"), fname[:-4], path)
        # break
    
if not DEBUG:    
    print ('</FictionBookMarks>')





    
