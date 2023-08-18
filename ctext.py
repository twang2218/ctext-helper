# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import sys
import argparse
import streamlit as st

LINK_S2T = 'https://raw.githubusercontent.com/BYVoid/OpenCC/master/data/dictionary/STCharacters.txt'
LINK_T2S = 'https://raw.githubusercontent.com/BYVoid/OpenCC/master/data/dictionary/TSCharacters.txt'

@st.cache_data
def get_dict(url, with_single_match=True):
    content = requests.get(url, timeout=60).content.decode('utf-8')
    dic = {}
    for line in content.split('\n'):
        if line.startswith('#'):
            continue
        if line.strip() == '':
            continue
        s, t = line.split('\t')
        ts  = t.split(' ')
        t = ''.join(ts)
        if len(t) > 1:
            # 多余一个字的映射
            dic[s] = t
        elif with_single_match:
            # 单字映射
            dic[s] = t
    return dic

s2tm = get_dict(LINK_S2T, with_single_match=False)
t2s = get_dict(LINK_T2S, with_single_match=True)

def get_book_chapters(url):
    print(f'正在获取章节列表……')
    content = requests.get(url, timeout=60).content.decode('utf-8')
    # 只获取到域名为止的部分
    base_parts = url.rstrip('/').split('/')
    baseurl = '/'.join(base_parts[:3])

    html = BeautifulSoup(content, 'html.parser')
    chapters = html.select('div.ctext span a')
    print(chapters)
    if len(chapters) == 0:
        # 可能是「原典全文」中的内容
        chapters = html.select('div#content3 > a')
        if len(chapters) == 0:
            chapters = html.select('div#content2 > a')
    chapters = {a.get_text(): urljoin(baseurl, a['href']) for a in chapters}
    print(f"共有 {len(chapters)} 章节")
    return chapters

def get_chapter_paragraphs(url):
    print(f'正在获取段落列表……')
    content = requests.get(url, timeout=60).content.decode('utf-8')
    html = BeautifulSoup(content, 'html.parser')
    paragraphs = html.select('tr.result')
    if len(paragraphs) > 0:
        paragraphs = {p['id']: p.find_all('td', {'class': 'ctext'})[1].get_text() for p in paragraphs}
    else:
        # 「原典全文」中的内容
        paragraphs = html.select('div#content3 tr')
        new_paragraphs = {}
        for p in paragraphs:
            if p.has_attr('id'):
                new_paragraphs[p['id']] = p.get_text()
        paragraphs = new_paragraphs
    return paragraphs

def check_s2t_multiple(paragraph, chapter='', link='', paragraph_id='', ignore=''):
    candidates = []
    for i, c in enumerate(paragraph):
        if c in t2s:
            # 将繁体字转换为简体字
            s = t2s[c]
            if s in s2tm:
                # 寻找简体字对应的多个繁体字（如果存在的话）
                t2 = s2tm[s]
                if c in ignore:
                    # 忽略的字
                    continue
                candidates.append({
                    'c': c,
                    't': t2,
                    'context': paragraph[max(0, i-15):i+15],
                    'chapter': chapter,
                    'link': link,
                    'paragraph_id': paragraph_id,
                })
    print(f">    {len(candidates)} 个可能存在错误的繁简转换段落")
    return candidates

def summary(all_candidates):
    candidates = {}
    for candidate in all_candidates:
        if candidate['c'] not in candidates:
            candidates[candidate['c']] = {
                'c': candidate['c'],
                't': candidate['t'],
                'items': []
            }
        candidates[candidate['c']]['items'].append({
            'chapter': candidate['chapter'],
            'context': candidate['context'],
            'link': f"{candidate['link']}#{candidate['paragraph_id']}",
        })
    # 按照汉字排序
    keys = list(candidates.keys())
    keys.sort()
    candidates = {k: candidates[k] for k in keys}
    print(f">    共有 {len(candidates)} 个可能存在错误的繁简对")
    return candidates

def find_error_candidates_in_book(url:str, ignore:str=''):
    if not url.startswith('http'):
        print(f"Invalid url: {url}")
        sys.exit(1)
    print(f'正在获取章节列表……')
    chapters = get_book_chapters(url)
    print(f"共有 {len(chapters)} 章节")
    all_candidates = []
    for chapter, link in chapters.items():
        print(f"{chapter:<20} \t {link}")
        paragraphs = get_chapter_paragraphs(link)
        for paragraph_id, paragraph in paragraphs.items():
            candidates = check_s2t_multiple(paragraph, chapter, link, paragraph_id, ignore)
            all_candidates.extend(candidates)
    # 归纳
    return summary(all_candidates)

def find_error_candidates_in_chapter(url:str, ignore:str=''):
    if not url.startswith('http'):
        print(f"Invalid url: {url}")
        sys.exit(1)
    all_candidates = []
    paragraphs = get_chapter_paragraphs(url)
    for paragraph_id, paragraph in paragraphs.items():
        candidates = check_s2t_multiple(paragraph, '', url, paragraph_id, ignore)
        all_candidates.extend(candidates)
    # 归纳
    return summary(all_candidates)


def main():
    args = argparse.ArgumentParser()
    args.add_argument('--url', type=str, help='ctext的书籍链接')
    args.add_argument('--file', type=str, help='用于保存结果的文件名')
    args.add_argument('--ignore', type=str, default='', help='忽略的字')
    args = args.parse_args()

    url = args.url.strip()
    if '&res=' in url or url.endswith('/zh'):
        # 书籍链接
        candidates = find_error_candidates_in_book(url, args.ignore)
    elif 'chapter=' in url:
        # 章节链接
        candidates = find_error_candidates_in_chapter(url, args.ignore)
    else:
        print('无效的链接。请使用 ctext 的书籍链接或者章节链接。如果是确认链接是正确的，请联系作者。 (QQ：2107553024)')
        return

    # 输出
    if args.file:
        with open(args.file, 'w', encoding='utf-8') as f:
            for v in candidates.values():
                f.write(f"{v['c']} -> {v['t']:10}\n")
                for item in v['items']:
                    f.write(f"    {item['chapter']}\t……{item['context']}……\t{item['link']}\n")
    else:
        for v in candidates.values():
            print(f"{v['c']} -> {v['t']:10}")
            for item in v['items']:
                print(f"    {item['chapter']}\t……{item['context']}……\t{item['link']}")

def web():
    with st.sidebar:
        st.title('ctext 繁简转换纠错辅助工具')
        url = st.text_input('ctext 书籍链接')
        ignore = st.text_input('忽略的字')
        st.button('开始检查')
    if url:
        url = url.strip()
        if '&res=' in url or url.endswith('/zh'):
            # 书籍链接
            candidates = find_error_candidates_in_book(url, ignore)
        elif 'chapter=' in url:
            # 章节链接
            candidates = find_error_candidates_in_chapter(url, ignore)
        else:
            st.write('无效的链接。请使用 ctext 的书籍链接或者章节链接。如果是确认链接是正确的，请联系作者。 (QQ：2107553024)')
            return
        if len(candidates) > 0:
            for v in candidates.values():
                # st.divider()
                st.write(f"### {v['c']} => {','.join(v['t']):10}")

                # st.table(v['items'])
                markdown = '| ID | 章节 | 上下文 |\n'
                markdown += '| --- | --- | --- |\n'
                for i, item in enumerate(v['items']):
                    context = item['context'].replace(v['c'], f" **{v['c']}** ")
                    context = context.replace('\n', ' ')
                    print(context)
                    markdown += f"| {i+1} | {item['chapter']} | ...[{context}]({item['link']})... |\n"
                st.markdown(markdown)
        else:
            st.write('没有可能存在错误的繁简转换')
    
if __name__ == '__main__':
    # main()
    web()

