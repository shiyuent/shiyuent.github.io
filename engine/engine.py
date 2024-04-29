# Modified by Xiaowei Xu, 2020 (xuranlai@gmail.com)
# Licensed under GNU GPLv3+
#
# A static site generator inspired by Jekyll and Hakyll

import os
import re
import yaml
import pypandoc
import logging
from lxml import etree
from pyatom import AtomFeed
import datetime

# yaml.warnings({'YAMLLoadWarning': False})

def item_from_path(path):
    with open(path) as f:
        text = f.read()
    p = re.compile(r'---\n(.*?)\n---(.*)', re.DOTALL)
    matchres = p.search(text)
    # res = yaml.load(matchres.group(1))
    res = yaml.load(matchres.group(1), Loader=yaml.FullLoader)
    x, ext = os.path.splitext(path)
    res.setdefault('name', os.path.basename(x))
    if ext in ['.md', '.markdown']:
        logging.info('Converting {}...'.format(path))
        res['body'] = pypandoc.convert_text(matchres.group(2), 'html', format='md', extra_args=['--mathjax', '-s', '--toc'])
    elif ext == '.wiki':
        logging.info('Converting {}...'.format(path))
        res['body'] = pypandoc.convert_text(matchres.group(2), 'html', format='vimwiki')
    elif ext == '.html':
        res['body'] = matchres.group(2)
    res.setdefault('synlen', 1)
    paras = etree.HTML(res['body']).xpath('//p')
    res['synopsis'] = ''.join([etree.tostring(p, encoding='unicode') for p in paras[:res['synlen']]])
    # res['synopsis'] = ''.join([etree.tounicode(p) for p in paras[:res['synlen']]])
    return res

def combine(item, template):
    resbody = template
    for k, v in item.items():
        resbody = resbody.replace('${}$'.format(k), str(v))
    res = dict(item)
    res['body'] = resbody
    return res


def main():
    basedir = os.path.dirname(os.path.realpath(__file__)) + '/../'
    pagesdir = basedir + 'pages/'
    postsdir = basedir + 'posts/'
    micropostsdir = basedir + 'microposts/'
    sitedir = basedir + 'dist/'
    templatesdir = basedir + 'templates/'
    homepostnum = 10

    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

    posts = get_all_items(postsdir)
    posts.sort(key=lambda x: x['date'], reverse=True)
    for post in posts:
        # post.setdefault('url', 'posts/{}.html'.format(post['name']))
        post.setdefault('url', '{}.html'.format(post['name']))
        with open('{}{}.html'.format(templatesdir, post['template'])) as f:
            template = f.read()
        post = combine(post, template)
        save_to_html(post, sitedir)

    with open(templatesdir + 'barepost.html') as f:
        template = f.read()
    #headposts is the list of the first few posts, to be displayed on blog.html
    headposts = {'body' : ''.join([combine(post, template)['body'] for post in posts[:homepostnum]])}
    with open(templatesdir + 'blog.html') as f:
        template = f.read()
        headposts = combine(headposts, template)
        headposts['url'] = 'blog.html'
        save_to_html(headposts, sitedir)

    with open(templatesdir + 'postlistitem.html') as f:
        template = f.read()
    postlist = {'body': ''}
    for post in posts:
        postlist['body'] += combine(post, template)['body']
    with open(templatesdir + 'postlist.html') as f:
        template = f.read()
    postlist = combine(postlist, template)
    postlist['url'] = 'postlist.html'
    save_to_html(postlist, sitedir)

    pages = get_all_items(pagesdir)
    for page in pages:
        page.setdefault('url', page['name'] + '.html')
        with open('{}{}.html'.format(templatesdir, page['template'])) as f:
            template = f.read()
        page = combine(page, template)
        save_to_html(page, sitedir)

    microposts = get_all_items(micropostsdir)
    microposts.sort(key=lambda x: x['date'], reverse=True)
    with open(templatesdir + 'micropost.html') as f:
        template = f.read()
    allmposts = {'body':''}
    for micropost in microposts:
        allmposts['body'] += combine(micropost, template)['body']
    with open(templatesdir + 'microblog.html') as f:
        template = f.read()
    allmposts = combine(allmposts, template)
    allmposts['url'] = 'microblog.html'
    save_to_html(allmposts, sitedir)

    blog_feed = AtomFeed(title="Xiaowei Xu's Blog",
                         feed_url="https://shiyuent.github.io/dist/blog-feed.xml",
                         url="https://shiyuent.github.io",
                         author="Xiaowei Xu")
    for post in posts:
        blog_feed.add(title=post["title"],
                      content=post["body"],
                      content_type="html",
                      author="Xiaowei Xu",
                      url=post["url"],
                      updated=post["date"])
    blog_feed_item = {'body':blog_feed.to_string(), 'url': 'blog-feed.xml'}
    save_to_html(blog_feed_item, sitedir)

    microblog_feed = AtomFeed(title="Xiaowei Xu's Microblog",
                         feed_url="https://shiyuent.github.io/dist/microblog-feed.xml",
                         url="http://shiyuent.github.io",
                         author="Xiaowei Xu")
    for micropost in microposts:
        microblog_feed.add(title=micropost["date"],
                      content=micropost["body"],
                      content_type="html",
                      author="Xiaowei Xu",
                      url="microblog.html",
                      updated=micropost["date"])
    microblog_feed_item = {'body':microblog_feed.to_string(), 'url': 'microblog-feed.xml'}
    save_to_html(microblog_feed_item, sitedir)

def save_to_html(item, sitedir):
    path = sitedir + item['url']
    os.makedirs(os.path.dirname(path), exist_ok=True)
    logging.info('Saving to {}...'.format(path))
    with open(path, 'w') as f:
        f.write(item['body'])

def get_all_items(dir_):
    items = []
    for filename in os.listdir(dir_):
        ext = filename.split('.')[-1]
        path = dir_ + filename
        item = item_from_path(path)
        items.append(item)
    return items

if __name__ == "__main__":
    main()
