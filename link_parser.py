import requests
import re
from bs4 import BeautifulSoup
from bs4.element import Tag, ResultSet
from typing import List, Union, Dict


def load_page(url: str) -> str:
    response = requests.get(url)
    if response.status_code == requests.codes.ok:
        return response.text
    else:
        response.raise_for_status()


def get_articles(page_str: str) -> List[Tag]:
    parsed_page = BeautifulSoup(page_str, 'html.parser')
    top_headers = find_top_headers(1, parsed_page)
    return top_headers


def find_top_headers(header_level: int, parsed_page: BeautifulSoup) -> ResultSet:
    headers = parsed_page.find_all("h{}".format(header_level))
    if not headers and header_level < 6:
        return find_top_headers(header_level + 1, parsed_page)
    else:
        return headers


def find_links_for_article(tag: Tag) -> List[Tag]:
    links = tag.find_all(href=re.compile(".*"))
    valid_links = list(filter(lambda l: is_link_valid(l), links))
    return valid_links


def is_link_valid(link: Tag) -> bool:
    return link is not None and \
           re.compile("^https?://.+$").fullmatch(link["href"]) is not None


def find_nearest_header_for_link(link: Tag) -> Union[Tag, None]:
    return find_nearest_header(link, 6)


def find_nearest_header(tag: Tag, header_level: int) -> Union[Tag, None]:
    sibling_header = None
    for parent in tag.parents:
        sibling_header = parent.find_previous_siblings("h{}".format(header_level))
        if len(sibling_header) != 0:
            break

    if not sibling_header and header_level > 0:
        return find_nearest_header(tag, header_level - 1)
    elif not sibling_header:
        return None
    else:
        return sibling_header[0]


def get_links_tree(url: str) -> dict:
    page = load_page(url)
    articles_of_page = get_articles(page)
    links_by_article = get_links_by_articles(articles_of_page)
    result = build_links_tree_for_articles(links_by_article)
    return result


def make_links_tree_file(link: str, path: str):
    save_as_md(links_tree_to_markdown(get_links_tree(link)), path)


def build_links_tree_for_articles(links_by_article: Dict[Tag, List[Tag]]) -> Dict[
    Tag, Dict[Tag, List[Tag]]]:
    result = {}
    for article, links in links_by_article.items():
        result[article] = find_nearest_headers_for_links(links)
    return result


def find_nearest_headers_for_links(links: List[Tag]) -> Dict[Tag, List[Tag]]:
    header_links = {}
    for link in links:
        nearest_header = find_nearest_header_for_link(link)
        if header_links.get(nearest_header) is None:
            header_links[nearest_header] = [link]
        else:
            existed_links = header_links[nearest_header]
            existed_links.append(link)
            header_links[nearest_header] = existed_links
    return header_links


def get_links_by_articles(articles_of_page: List[Tag]) -> Dict[Tag, List[Tag]]:
    links = {}
    for article in articles_of_page:
        links[article] = find_links_for_article(article.parent)
    return links


def links_tree_to_markdown(links_tree: dict) -> str:
    return build_md(links_tree, "")


def build_md(links_tree: dict, header_str: str) -> str:
    if type(links_tree) is list:
        for link in links_tree:
            if link.string:
                header_str += '[{}]({})\n\n'.format(format_tag_name(link.string), link['href'])
        return header_str
    else:
        for k, v in links_tree.items():
            if k is None or k.string is None:
                header_str += ''
            elif k.name == 'h1':
                header_str += '# {}\n'.format(format_tag_name(k.string))
            elif k.name == 'h2':
                header_str += '## {}\n'.format(format_tag_name(k.string))
            elif k.name == 'h3':
                header_str += '### {}\n'.format(format_tag_name(k.string))
            elif k.name == 'h4':
                header_str += '#### {}\n'.format(format_tag_name(k.string))
            elif k.name == 'h5':
                header_str += '##### {}\n'.format(format_tag_name(k.string))
            elif k.name == 'h6':
                header_str += '###### {}\n'.format(format_tag_name(k.string))
            header_str = build_md(v, header_str)
        return header_str


def format_tag_name(header: str) -> str:
    if header is None:
        return "Content not found"
    else:
        special_chars_re = re.compile('[\\n\\r]')
        spaces_re = re.compile('[\\s]+')
        header = header.strip()
        header = special_chars_re.sub('', header)
        header = spaces_re.sub(' ', header)
        return header


def save_as_md(text: str, path: str) -> None:
    with open(path, mode="w") as f:
        f.write(text)
