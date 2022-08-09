<h1 align="center">
  <br>
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://user-images.githubusercontent.com/69304096/182015689-b968aabc-1deb-4dd7-b6a5-45554c0f8454.png">
    <img alt="AniName Logo" width=200 src="https://user-images.githubusercontent.com/69304096/182155020-58d38e58-33dc-4688-9f20-a2d68e8dc51e.png">
  </picture>
  <br>
  AniName
  <br>
</h1>

<h4 align="center">Batch rename Anime Episode files with customizable formatting.</h4>

<p align="center">
  <a href="#quick-start">Quick Start</a> •
  <a href="#usage-and-options">Usage and Options</a> •
  <a href="#credits">Credits</a>
</p>

# Quick Start

To clone and run this application, you'll need [Git](https://git-scm.com) and [Python](https://www.python.org/downloads/) installed on your computer. From your command line:

```bash
# Clone this repository
git clone https://github.com/AbhiramH427/AniName

# Go into the repository
cd AniName

# Install dependencies
pip install -r requirements.txt

# Run the app
python rename_utility.py
```
# Usage and Options

* [Pre-requisite](#pre-requisite)
* [Rename Utility](#rename-utility)
* [Config File](#config-file)
* [Restore Utility](#restore-utility)

## Pre-requisite

To run this application you'll need [Python](https://www.python.org/downloads/) installed on your computer.

### Anime Folder Formatting

In order for <b>Rename Utility</b> to recognize your Anime folder, rename it to the following format <b>(without square brackets and spaces)</b>:

`[MyAnimeList ID]` `S[Season Number]` `P[Part Number]`

Replace the text in the square brackets with the appropriate value (remove spaces).

* `[MyAnimeList ID]`: ID of the Anime from [MyAnimeList.net](https://myanimelist.net/)
* `S[Season Number]`: Season number of the Anime
* `P[Part Number]`: Part number of the Anime

`S[Season Number]` and `P[Part Number]` are optional. They are used to identify the season and part of the Anime, and rename the files accordingly.

You can retrieve the <b>MyAnimeList ID</b> by following these steps:
* Visit [MyAnimeList.net](https://myanimelist.net/)
* Use the search bar to search and open your Anime in the site.
* The URL should look something like this (pay attention to the ID):  
`https:​//myanimelist.net/anime/ID/Anime-Name`
* The ID (number) in the URL is the <b>MyAnimeList ID</b>.
* As an example, here is the URL for the anime <b>Attack on Titan</b>:  
https://myanimelist.net/anime/16498/Shingeki_no_Kyojin  
The <b>MyAnimeList ID</b> for the above example is <b>16498</b>

Here are a few examples of Anime folder names:
* Death Note: `1535`
* Attack on Titan Season 1: `16498S01`
* Attack on Titan Season 3 Part 2: `38524S01P02`

![Anime Folder Names Example](https://user-images.githubusercontent.com/69304096/182024189-394074c1-b2e7-4a2a-a1b7-dc858f482c91.png)

### Anime Episodes Formatting

The <b>Rename Utility</b> relies on the episode number to rename Anime episodes, so make sure that the filename of your Anime episodes contains the episode number. In the event that the rename fails, it is recommended that you use the [Bulk Rename Utility](https://www.bulkrenameutility.co.uk/Download.php) or [PowerRename utility](https://docs.microsoft.com/en-us/windows/powertoys/powerrename) that comes with [Microsoft PowerToys](https://docs.microsoft.com/en-us/windows/powertoys/) to remove everything except the episode number from the episode files and then retry.

## Rename Utility

The <b>Rename Utility</b> is used to batch rename Anime episode files.

To use the <b>Rename Utility</b>, open the command line in the app's folder and run:
```bash
python rename_utility.py
```

When you launch the <b>Rename Utility</b>, you are asked to specify the <b>Path of the Anime Directory</b>. It refers to the path of the parent folder containing the Anime(s) the app is to rename.

The path can be obtained by opening the folder containing your Anime(s) using <b>File Explorer</b>, right-clicking on the address bar, and selecting <b>Copy adress</b>. The path will be copied to the clipboard which can be pasted into the app.

The <b>Rename Utility</b> will scan for directories/subdirectories matching the format mentioned in 
[Anime Folder Formatting](#anime-folder-formatting). The process of renaming can be started by confirming the Anime(s) found during the scan by the user.

After the rename, a backup of all previous filenames are stored in a folder called <b>ORIGINAL_EPISODE_FILENAMES</b>. This folder is made outside the path entered while using the <b>Rename Utility</b>. The previous filenames can be restored using the [Restore Utility](#restore-utility).

## Config File

The <b>conf.ini</b> file present in the app folder allows you to customize how your files are renamed.

### Language Options

Available options:

- `season_title_language`: Language of the season/anime title. 
- `episode_title_language`: Language of the episode title.

Available Language values are `english`, `romanji` and `japanese`


Examples of <b>Attack on Titan</b> under different <b>Language</b> values:

- `english`: Attack on Titan
- `romanji`: Shingeki no Kyojin
- `japanese`: 進撃の巨人

### Season & Episode Formatting

The formatting options can contain special sequences that will be replaced when renaming. For example, `{sn}` or `{[S]&sn|}`

The field names themselves (the part inside the `{}`) can also have some special formatting:

- <b>Conjunction:</b> Text, variables, prefixes can be merged by using a `&` separator. Example, `{ - &et}`

- <b>Prefix:</b> A value enclosed in `[]` used before a variable. For example, `{[S]&sn}`. this value will not be used if the varible after it is empty.

- <b>Postfix:</b> A value enclosed in `()` used after a variable. For example, `{sn&( season)}`. this value will not be used if the varible after it is empty.

- <b>Default:</b> A literal default value can be specified for when the field is empty using a `|` separator. Example, `{pn|00}`. By default, the default value is empty.

- The above special formatting can be used as text inside the field by using the escape character `\`. Example, `{sn& \& &pn}`

Available options:

- `episode_format`: The format in which the episode filename will be renamed.
- `season_format`: The format in which the Anime folder will be renamed.

Available fields:

- `sn`: Season number
- `pn`: Part number
- `en`: Episode number
- `st`: Season/Anime title
- `et`: Episode title

### Season & Episode Format Example Templates

```ini
# S01E01 - To You Two Thousand Years Later
# S03P02E01 - The Town Where Everything Began
episode_format = {[S]&sn|}{[P]&pn|}{[E]&en|} - {et|}

# E01 - To You Two Thousand Years Later
episode_format = {[E]&en|} - {et|}

# To You Two Thousand Years Later (E01)
episode_format = {et|} ({[E]&en|})

# 01x01 - To You Two Thousand Years Later
episode_format = {sn&x|}{en|} - {et|}

# S01 - Attack on Titan
# S03P02 - Attack on Titan Season 3 Part 2
season_format = {[S]&sn&[P]&pn& - |}{st|}

# Attack on Titan (S01)
# Attack on Titan Season 3 Part 2 (S03P02)
season_format = {st|} ({[S]&sn|}{[P]&pn|})

# Attack on Titan
# Attack on Titan Season 3 Part 2
season_format = {st|}
```

# Restore Utility

The <b>Rename Utility</b> creates a backup of all previous filenames in a folder called <b>ORIGINAL_EPISODE_FILENAMES</b> outside the path used in the app.

It is done as a measure of safety in case you wish to revert to the previous filenames.

The <b>Restore Utility</b> can be used to revert to previous filenames. To use the <b>Restore Utility</b>, open the command line in the app's folder and run:
```bash
python restore_utility.py
```

Specifiy the path of the  <b>ORIGINAL_EPISODE_FILENAMES</b> folder and select the backup file. Confirm to proceed restoring the filenames.

# Credits

 - [Jikan REST API](https://github.com/jikan-me/jikan-rest)

# Disclaimer

- AniName is not affiliated with MyAnimeList.net
- You are responsible for the usage of this application.
