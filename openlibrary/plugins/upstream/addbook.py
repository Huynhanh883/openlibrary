"""Handlers for adding and editing books."""

import web
import urllib, urllib2
from infogami.utils import delegate
from infogami import config

from openlibrary.plugins.openlibrary import code as ol_code

from utils import render_template, unflatten


class addbook(delegate.page):
    path = "/books/add"
    
    def GET(self):
        return render_template('books/add')
        
    def POST(self):
        i = web.input(title='')
        print i
        work = web.ctx.site.new('/works/new', {'key': '/works/new', 'type': '/type/work', 'title': ''})
        edition = web.ctx.site.new('/books/new', {'key': '/books/new', 'type': '/type/edition', 'title': ''})
        return render_template('books/edit', work, edition)


class addauthor(ol_code.addauthor):
    path = "/authors/add"    

del delegate.pages['/addbook']
# templates still refers to /addauthor.
#del delegate.pages['/addauthor'] 


def strip_values(values):
    """
        >>> strip_values(["a ", "", " b "])
        ["a", "b"]
    """
    return [v.strip() for v in values if v.strip()]


class book_edit(delegate.page):
    path = "(/books/OL\d+M)/edit"
    
    def GET(self, key):
        edition = web.ctx.site.get(key)
        if edition is None:
            raise web.notfound()
            
        work = edition.works and edition.works[0]
        # HACK: create dummy work when work is not available to make edit form work
        work = work or web.ctx.site.new('/works/new', '/type/work', {'title': edition.title})
        return render_template('books/edit', work, edition)
        
    def POST(self, key):
        book = web.ctx.site.get(key)
        if book is None:
            raise web.notfound()
            
        i = web.input()
        i = self.process_input(i)
        self.save_book(book, i)
        raise web.seeother(key)
        
    def process_input(self, i):
        i = unflatten(i)
        
        book = i.edition
        book.publishers = strip_values(i.get('publishers', '').split(';'))
        book.publish_places = strip_values(i.get('publish_places', '').split(';'))
        
        return i
    
    def save_book(self, book, i):
        book.update(i.edition)
        book._save(comment=i.get('_comment'))

class work_edit(delegate.page):
    path = "(/works/OL\d+W)/edit"
    
    def GET(self, key):
        work = web.ctx.site.get(key)
        if work is None:
            raise web.notfound()
        return render_template('books/edit', work)

class uploadcover(delegate.page):
    def POST(self):
        user = web.ctx.site.get_user()
        i = web.input(file={}, url=None, key="")
        
        olid = i.key and i.key.split("/")[-1]
        
        if i.file is not None:
            data = i.file.value
        else:
            data = None
            
        if i.url and i.url.strip() == "http://":
            i.url = ""

        upload_url = config.get('coverstore_url', 'http://covers.openlibrary.org') + '/b/upload2'
        params = dict(author=user and user.key, data=data, source_url=i.url, olid=olid, ip=web.ctx.ip)
        try:
            response = urllib2.urlopen(upload_url, urllib.urlencode(params))
            out = response.read()
        except urllib2.HTTPError, e:
            out = e.read()
            
        web.header("Content-Type", "text/javascript")
        return delegate.RawText(out)
        