from rich.prompt import IntPrompt
from m3u8_dl.cli import CONSOLE
from m3u8_dl.constants import FRENCH_STREAM_BASE_URL
from m3u8_dl.providers.french_stream import transform_endpoint_into_readable,search as fs_search,find_download_url


def search(query : str,nb_results : int):
    urls = fs_search(query,int(nb_results))
    
    options = [transform_endpoint_into_readable(url) for url in urls]
    
    CONSOLE.print(f"Results found for '{query}' :")
    for i, opt in enumerate(options, 1):
        CONSOLE.print(f"[green]{i}[/green]. {opt}")
    
    index = IntPrompt.ask("Enter index of media to download", default=1)
    url = urls[index - 1]
    full_url = f"{FRENCH_STREAM_BASE_URL}{url}"
    
    print(full_url)

    dl_url = find_download_url(full_url)

    return dl_url