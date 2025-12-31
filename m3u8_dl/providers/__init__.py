from m3u8_dl.providers import french_stream as fs

available_providers = [
    ("French Stream",fs.search,fs.find_download_url)
]