"""
Contains functions needed to scrape and parse data from MyAnimeList.
"""

import asyncio
from sys import platform

import lxml.html
import regex

from . import conf_loader

from .http_session import get_client_session

if platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

ANIME_TITLE_LANG = conf_loader.conf.anime_title_lang
EP_TITLE_LANG = conf_loader.conf.ep_title_lang
FIRST_100 = True  # to be used in the future


def clean_title(title: str) -> str:
    """
    Removes whitespaces and non-breaking space from the an English title.
    """

    return (title.strip()).replace("\xa0", " ")


def clean_jp_title(title: str) -> str:
    """
    Removes whitespaces, non-breaking space and brackets from a Japanese title.
    """

    return (title.strip().strip("()")).replace("\xa0", " ")


async def fetch(url, mal_id=None):
    """
    Fetch data from url.
    """

    session = await get_client_session()

    async with session.get(url) as response:
        html = await response.text()

        if mal_id is not None:
            data = {mal_id: lxml.html.fromstring(html)}
        else:
            data = lxml.html.fromstring(html)

    return data


def parse_anime(html, mal_id):
    """
    Parses results from the fetch_anime() function
    """

    title_romanji = (html.xpath("//meta[@property='og:title']/@content")[0]).strip()

    title_english = html.xpath('//span[text()="English:"]/following-sibling::text()')

    title_japanese = html.xpath('//span[text()="Japanese:"]/following-sibling::text()')

    if title_english != []:
        title_english = title_english[0].strip()
    else:
        title_english = title_romanji

    if title_japanese != []:
        title_japanese = title_japanese[0].strip()
    else:
        title_japanese = title_romanji

    anime_type = html.xpath('//span[text()="Type:"]/following-sibling::a/text()')[0]

    total_episodes = (
        html.xpath('//span[text()="Episodes:"]/following-sibling::text()')[0]
    ).strip()

    last_page = html.xpath('//div[@class="pagination ac"]/a[last()]/@href')

    ep_pages = None

    if len(last_page) != 0:
        max_offset = int(regex.findall(r"\?offset=(\d+)$", last_page[0])[0])
        ep_pages = [
            f"https://myanimelist.net/anime/{mal_id}/_/episode?offset={i}"
            for i in range(0, max_offset + 100, 100)
        ]

    anime_title = title_english

    if ANIME_TITLE_LANG == "japanese":
        anime_title = title_japanese

    if ANIME_TITLE_LANG == "romanji":
        anime_title = title_romanji

    data = {
        "mal_id": mal_id,
        "title": anime_title,
        "type": anime_type,
        "total_eps": total_episodes,
        "ep_pages": ep_pages,
    }

    if FIRST_100 == True:
        # Parses the first 100 or less episode titles from the already loaded HTML
        episode_titles = parse_episodes([html])
        data["ep_titles"] = episode_titles

    return data


def parse_episodes(htmls):
    """
    Parses results from the fetch_episodes() function
    """

    data = {"english": {}, "romanji": {}, "japanese": {}}

    for html in htmls:
        episode_numbers = html.xpath('//td[@class="episode-number nowrap"]/text()')

        titles = html.xpath('//td[@class="episode-title fs12"]')

        titles_english = []
        title_rj = []

        for i, title in enumerate(titles):
            titles_english.append("")

            titles_english[i] = title.xpath('a[@class="fl-l fw-b "]/text()')[0]

            t_rj = title.xpath('span[@class="di-ib"]/text()')

            if t_rj != []:
                title_rj.append(t_rj[0])

            else:
                title_rj.append(f"{titles_english[i]}\xa0{titles_english[i]}")

        titles_romanji, titles_japanese = map(
            list, zip(*[regex.split(r"\n+|\xa0+", ele) for ele in title_rj])
        )

        for title_en, title_ro, title_jp, ep_no in zip(
            titles_english, titles_romanji, titles_japanese, episode_numbers
        ):
            data["english"].update({ep_no: (title_en)})
            data["romanji"].update({ep_no: (title_ro)})
            data["japanese"].update({ep_no: (title_jp)})

    return data[EP_TITLE_LANG]
