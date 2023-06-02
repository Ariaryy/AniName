"""
Contains functions needed to scrape and parse data from MyAnimeList.
"""

import asyncio
from sys import platform
from urllib.parse import quote

import aiohttp
import lxml.html
import regex

if platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


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


async def fetch(session, url, mal_id=None):
    """
    Fetch data from url.
    """
    async with session.get(url) as response:
        html = await response.text()

        if mal_id is not None:
            data = {mal_id: html}
        else:
            data = html

    return data


async def search_anime(titles: list):
    """
    Searches Anime via title on MyAnimeList.
    """

    async with aiohttp.ClientSession() as session:
        tasks = []

        for title in titles:
            url = f"https://myanimelist.net/anime.php?q={quote(title)}&cat=anime"
            tasks.append(asyncio.create_task(fetch(session, url)))

        data = await asyncio.gather(*tasks)

        tasks = []

        for item in data:
            tasks.append(asyncio.create_task(parse_search_results(item)))

        animes = await asyncio.gather(*tasks)

        return animes


async def fetch_animes(
    mal_ids: list, season_title_lang: str, ep_title_lang: str
) -> dict:
    """
    Fetches Anime data from MyAnimeList.
    """

    async with aiohttp.ClientSession() as session:
        tasks = []

        for mal_id in mal_ids:
            url = f"https://myanimelist.net/anime/{mal_id}/_/episode?offset=0"
            tasks.append(asyncio.create_task(fetch(session, url, mal_id)))

        data = await asyncio.gather(*tasks)

    tasks = []

    for item in data:
        for mal_id in item:
            tasks.append(
                asyncio.create_task(
                    parse_anime(item[mal_id], mal_id, season_title_lang, ep_title_lang)
                )
            )

    animes = await asyncio.gather(*tasks)

    return animes


async def fetch_episodes(
    mal_id: int, ep_pages: list, min_ep: int, max_ep: int, ep_title_language: str
):
    """
    Fetches episode titles from MyAnimeList.
    """

    async with aiohttp.ClientSession() as session:
        tasks = []

        if min_ep <= 100:
            min_ep += 100
        min_ep_slice = (min_ep - 1) // 100
        max_ep_slice = ((max_ep - 1) // 100) + 1

        tasks = [
            asyncio.create_task(fetch(session, page, mal_id))
            for page in ep_pages[min_ep_slice:max_ep_slice]
        ]

        data = await asyncio.gather(*tasks)

    data_clean = {
        k: [d.get(k) for d in data if d.get(k) is not None] for k in set().union(*data)
    }

    tasks = [
        asyncio.create_task(parse_episodes(data_clean[id], ep_title_language))
        for id in data_clean
    ]

    episodes = await asyncio.gather(*tasks)

    return episodes


async def parse_search_results(html):
    """
    Parses results from the search_anime() function
    """

    html = lxml.html.fromstring(html)

    table = html.xpath(
        '//div[@class="js-categories-seasonal js-block-list list"]/table'
    )

    anime_urls = []
    anime_titles = []
    mal_ids = []
    anime_types = []

    for row in table[0].xpath("./tr")[1:]:
        anime_titles.append(
            row.xpath('./td/div[@class="title"]/a/strong/text()')[0].strip()
        )
        anime_types.append(row.xpath("./td[3]/text()")[0].strip())
        anime_urls.append(row.xpath('./td/div[@class="title"]/a/@href')[0].strip())

    mal_ids = [regex.findall(r"\/anime\/(\d+)", link)[0] for link in anime_urls]

    data = []

    for mal_id, url, title, type in zip(mal_ids, anime_urls, anime_titles, anime_types):
        if type == "TV":
            data.append({"mal_id": mal_id, "title": title.strip(), "url": url})

    return data[:5]


async def parse_anime(html, mal_id, season_title_lang, ep_title_lang):
    """
    Parses results from the fetch_anime() function
    """

    episode_titles = await parse_episodes([html], ep_title_lang)

    html = lxml.html.fromstring(html)

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

    if season_title_lang == "japanese":
        anime_title = title_japanese

    if season_title_lang == "romanji":
        anime_title = title_romanji

    data = {
        "mal_id": mal_id,
        "title": anime_title,
        "type": anime_type,
        "total_eps": total_episodes,
        "ep_pages": ep_pages,
    }

    # Parses the first 100 or less episode titles from the already loaded HTML
    data["ep_titles"] = episode_titles

    return data


async def parse_episodes(htmls, ep_title_lang):
    """
    Parses results from the fetch_episodes() function
    """

    data = {"english": {}, "romanji": {}, "japanese": {}}

    for html in htmls:
        html = lxml.html.fromstring(html)

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

    return data[ep_title_lang]
