## Description

This tool converts bookmarks from **PocketBook 301** _.af0_ files to **Cool Reader 3** _cr3hist.bmk_ file  
I do this work, because can't found ready-made solution for that.

## Run

` $ python3 pb301_to_cr3_bookmarks.py /home/user/Pocket301 > ~/.cr3/cr3hist.bmk `  
Where ` /home/user/Pocket301 ` is path for backup from your book

If something went wrong you can change `DEBUG = 0` to `DEBUG = 1`  
You also need to find text of the begining of selected _para_.  
_Para_ you take from _para_ col in table.    
Run shows you difference from found positions of bookmarks.  
Success when all diffs are zero ;)

## More info

To do this I looked inside sources of PocketBook fbreader:  
https://sourceforge.net/projects/pocketbook-free/files/fbreader-pocketbook/1.0.0/

This struct describe bookmark in sorces  
```
typedef struct tdocstate_s {  
  int magic;  
  long long position;  
  int reserved1;  
  int reserved2;  
  char encoding[16];  
  int nbmk;  
  long long bmk[30];  
} tdocstate;

static void unpack_position(long long pos, int *para, int *word, int *letter) {
  *para = (pos >> 40) & 0xffffff;
  *word = (pos >> 16) & 0xffffff;
  *letter = pos & 0xffff;
}
```  

But _para_ is not number of p tag in document.  
And you can't take it like `root.xpath("(//*[name()='p'])[" + str(para) + "]")[0]`  
You need to parse xml file to find correspondence between _para_ num and position in xml.  
This sources contains logic for parser:
```
fbreader/src/formats/fb2/FB2BookReader.cpp  
fbreader/src/formats/fb2/FB2Reader.cpp  
fbreader/src/bookmodel/BookReader.cpp
```





