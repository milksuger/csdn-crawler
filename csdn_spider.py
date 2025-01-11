import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
"""
免责声明：
1. 本项目仅供学习和研究使用，禁止用于商业用途
2. 使用本代码产生的任何法律责任由使用者自行承担
3. 请遵守网站的robots.txt规则和使用条款
4. 建议限制爬取频率，避免对目标网站造成压力
"""
def get_article_content(url):
    """
    获取CSDN文章内容
    :param url: CSDN文章链接
    :return: (title, content, metadata, error) 元组
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.encoding = 'utf-8'
        
        if response.status_code != 200:
            return None, None, None, f"请求失败，状态码：{response.status_code}"
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 获取文章标题
        title_element = soup.find('h1', class_='title-article')
        if not title_element:
            return None, None, None, "无法找到文章标题"
        title = title_element.text.strip()
        
        # 获取文章标签
        tags = []
        tag_elements = soup.find_all('a', class_='tag-link')
        if tag_elements:
            tags = [tag.text.strip() for tag in tag_elements]
        
        # 获取发布时间（尝试多种可能的选择器）
        publish_time = None
        # 尝试方法1：查找包含"发布于"的div
        time_div = soup.find('div', string=re.compile(r'发布于'))
        if time_div:
            publish_time = time_div.text.replace('发布于', '').strip()
        
        # 尝试方法2：查找特定class的span
        if not publish_time:
            time_element = soup.find('span', class_='time')
            if time_element:
                publish_time = time_element.text.strip()
        
        # 尝试方法3：查找文章信息区域
        if not publish_time:
            info_box = soup.find('div', class_='article-info-box')
            if info_box:
                time_span = info_box.find('span', class_=re.compile(r'time'))
                if time_span:
                    publish_time = time_span.text.strip()
        
        # 如果所有方法都失败，使用当前时间
        if not publish_time:
            publish_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 获取作者信息
        author_element = soup.find('a', class_='follow-nickName')
        if not author_element:
            author_element = soup.find('a', class_='user-name')
        author = author_element.text.strip() if author_element else "匿名"
        
        # 获取文章内容
        article_content = soup.find('div', id='article_content')
        if not article_content:
            article_content = soup.find('div', class_='article_content')
        if not article_content:
            return None, None, None, "无法找到文章内容"
        
        # 移除不需要的元素
        for element in article_content.find_all(['script', 'style', 'svg']):
            element.decompose()
        
        # 处理代码块
        for code_block in article_content.find_all('pre'):
            code_text = code_block.text.strip()
            language = ''
            if code_block.find('code', class_=True):
                language = code_block.find('code')['class'][0].replace('language-', '')
            code_block.replace_with(f"\n```{language}\n{code_text}\n```\n")
        
        # 处理标题
        for h in article_content.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            level = int(h.name[1])
            h.replace_with(f"\n{'#' * level} {h.text.strip()}\n")
        
        # 处理列表
        for ul in article_content.find_all('ul'):
            for li in ul.find_all('li'):
                li.replace_with(f"* {li.text.strip()}\n")
        
        for ol in article_content.find_all('ol'):
            for i, li in enumerate(ol.find_all('li'), 1):
                li.replace_with(f"{i}. {li.text.strip()}\n")
        
        # 处理链接
        for a in article_content.find_all('a'):
            href = a.get('href', '')
            text = a.text.strip()
            if href and text:
                a.replace_with(f"[{text}]({href})")
        
        # 获取纯文本内容并清理
        content = article_content.get_text(separator='\n').strip()
        content = re.sub(r'\n\s*\n', '\n\n', content)
        
        metadata = {
            'author': author,
            'publish_time': publish_time,
            'tags': tags,
            'source_url': url
        }
        
        return title, content, metadata, None
        
    except Exception as e:
        return None, None, None, f"发生错误：{str(e)}"


# 添加 LOGO
LOGO = """
  _____  _____ ____  _   _    _____                    _           
 / ____|/ ____|  _ \| \ | |  / ____|                  | |          
| |    | (___ | | | |  \| | | |     _ __ __ _ _ __ ___| | ___ _ __ 
| |     \___ \| | | | . ` | | |    | '__/ _` | '__/ __| |/ _ \ '__|
| |____ ____) | |__| | |\  | | |____| | | (_| | | | (__| |  __/ |   
 \_____|_____/|____/|_| \_|  \_____|_|  \__,_|_|  \___|_|\___|_|   
"""

def save_article_as_markdown(title, content, metadata, filename=None):
    """
    将文章保存为Markdown格式
    :param title: 文章标题
    :param content: 文章内容
    :param metadata: 文章元数据
    :param filename: 文件名（可选）
    """
    if not filename:
        # 清理标题中的非法字符，用作文件名
        filename = re.sub(r'[\\/:*?"<>|]', '', title)
        filename = f"{filename}.md"

        # 添加水印信息
    watermark = f"""
---
> 本文由 CSDN Crawler 抓取自CSDN  
> 原文作者: {metadata['author']}  
> 原文链接: {metadata['source_url']}  
> 项目地址: https://github.com/milksuger/csdn-crawler  
> 抓取时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

    markdown_content = f"""# {title}

> 作者：{metadata['author']}  
> 发布时间：{metadata['publish_time']}  
> 来源：[CSDN]({metadata['source_url']})

{''.join([f'`{tag}` ' for tag in metadata['tags']])}

---

{content}

---

{watermark}
"""
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(markdown_content)

def print_logo():
    """打印程序 logo"""
    print(LOGO)
    print("CSDN文章爬虫 v1.0.0")
    print("作者: [CSDN-Crawler]")
    print("=" * 50)

if __name__ == '__main__':
    print_logo()
    url = input("请输入CSDN文章链接：")
    title, content, metadata, error = get_article_content(url)
    
    if title and content and metadata:
        save_article_as_markdown(title, content, metadata)
        print(f"文章《{title}》已保存成功！")
    else:
        print(f"爬取失败：{error}") 