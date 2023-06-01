import asyncio
from urllib.parse import quote

import aiohttp
import lxml.html
import regex

asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

clean_title = lambda title: (title.strip()).replace("\xa0", " ")
clean_jp_title = lambda title: (title.strip().strip("()")).replace("\xa0", " ")


async def fetch(session, url, mal_id=None):
    async with session.get(url) as response:
        html = await response.text()

        if mal_id != None:
            data = {mal_id: html}
        else:
            data = html

    return data


async def search_anime(titles: list):
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


async def fetch_animes(ids: list, season_title_lang: str, ep_title_lang: str) -> dict:
    async with aiohttp.ClientSession() as session:
        tasks = []

        for id in ids:
            url = f"https://myanimelist.net/anime/{id}/_/episode?offset=0"
            tasks.append(asyncio.create_task(fetch(session, url, id)))

        data = await asyncio.gather(*tasks)

    tasks = []

    for item in data:
        for id in item:
            tasks.append(
                asyncio.create_task(
                    parse_anime(item[id], id, season_title_lang, ep_title_lang)
                )
            )

    animes = await asyncio.gather(*tasks)

    return animes


async def fetch_episodes(anime_data: list, ep_title_language: str):
    async with aiohttp.ClientSession() as session:
        tasks = []

        for anime in anime_data:
            id = list(anime.keys())[0]
            min_ep_slice = (anime[id]["local_min_ep"] - 1) // 100
            max_ep_slice = ((anime[id]["local_max_ep"] - 1) // 100) + 1
            pages = anime[id]["ep_pages"][min_ep_slice:max_ep_slice]
            for page in pages:
                tasks.append(asyncio.create_task(fetch(session, page, id)))

        data = await asyncio.gather(*tasks)

    data_clean = {
        k: [d.get(k) for d in data if d.get(k) != None] for k in set().union(*data)
    }

    tasks = []

    for id in data_clean:
        tasks.append(
            asyncio.create_task(parse_episodes(data_clean[id], ep_title_language))
        )

    episodes = await asyncio.gather(*tasks)

    return episodes


async def parse_search_results(html):
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

    for id, url, title, type in zip(mal_ids, anime_urls, anime_titles, anime_types):
        if type == "TV":
            data.append({"mal_id": id, "title": title.strip(), "url": url})

    return data[:5]


async def parse_anime(html, mal_id, season_title_lang, ep_title_lang):

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
            for i in range(1, max_offset + 100, 100)
        ]

    anime_title = title_english

    if season_title_lang == "japanese":
        anime_title = title_japanese
    
    if season_title_lang == "romanji":
        anime_title = title_romanji

    data = {
        mal_id: {
            "anime_title": anime_title,
            "type": anime_type,
            "episodes": total_episodes,
            "ep_pages": ep_pages,
        }
    }

    # Parses the first 100 or less episode titles from the already loaded HTML
    data[mal_id]["episode_titles"] = episode_titles

    return data


async def parse_episodes(htmls, ep_title_lang):
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