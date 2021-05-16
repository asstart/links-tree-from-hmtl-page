import requests
import bs4
from bs4 import BeautifulSoup
import re


def load_page(url: str) -> str:
    return requests.get(url).text


def get_articles(page_str: str):
    parsed = BeautifulSoup(page_str, 'html.parser')
    top_headers = find_top_headers(1, parsed)
    return top_headers


def find_top_headers(header_level: int, parsed_page: BeautifulSoup) -> bs4.element.ResultSet:
    headers = parsed_page.find_all("h{}".format(header_level))
    if headers is None and header_level < 6:
        return find_top_headers(header_level + 1, parsed_page)
    else:
        return headers


def find_links(tag: bs4.Tag):
    return tag.find_all(href=re.compile(".*"))


def find_part_paragraph_for_link(link):
    return find_header(link, 6)


def find_header(tag, header_level):
    sibling_header = None
    for parent in tag.parents:
        sibling_header = parent.find_previous_siblings("h{}".format(header_level))
        if len(sibling_header) != 0:
            break

    if len(sibling_header) == 0 and header_level > 0:
        return find_header(tag, header_level - 1)
    elif len(sibling_header) == 0:
        return None
    else:
        return sibling_header[0]


def get_links_tree(url: str):
    page = load_page(url)
    top_headers = get_articles(page)
    links = {}
    for header in top_headers:
        links[header] = find_links(header.parent)

    result = {}
    for k, v in links.items():
        header_links = {}
        result[k] = header_links
        for link in v:
            nearest_header = find_part_paragraph_for_link(link)
            if header_links.get(nearest_header) is None:
                header_links[nearest_header] = [link]
            else:
                existed_links = header_links[nearest_header]
                existed_links.append(link)
                header_links[nearest_header] = existed_links
    return result


def links_tree_to_markdown(links_tree):
    return build_md(links_tree, "")


def build_md(links_tree, header_str):
    if type(links_tree) is list:
        for link in links_tree:
            header_str += '[{}]({})\n\n'.format(format_tag_name(link.string), link['href'])
        return header_str
    else:
        for k, v in links_tree.items():
            if k.name == 'h1':
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


def format_tag_name(header):
    if header is None:
        return "Content not found"
    else:
        return header.strip()
