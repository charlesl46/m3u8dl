import requests
from bs4 import BeautifulSoup
import re
from playwright.sync_api import sync_playwright
from m3u8_dl.cli import CONSOLE
from m3u8_dl.constants import FRENCH_STREAM_BASE_URL
from rich.prompt import IntPrompt

def transform_endpoint_into_readable(endpoint : str):
    endpoint_readable = endpoint.replace("/","").replace(".html","").split("-")[1:]
    endpoint_readable = " ".join(endpoint_readable).capitalize()
    return endpoint_readable
    

def search(query : str,return_first_n : int = 1):
    LOCATION_REGEX = re.compile(r"location\.href\s*=\s*['\"]([^'\"]+)['\"]",)
    
    url = f"{FRENCH_STREAM_BASE_URL}/engine/ajax/search.php"
    
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://fs2.lol/",
        "Origin": "https://fs2.lol",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    
    payload = {
        "query": query,
        "page": 1
    }
    
    response = requests.post(url, data=payload, headers=headers)
    soup = BeautifulSoup(response.text,"html.parser")
    first_results = soup.find_all("div",class_="search-item")[:return_first_n]
    
    urls = []
    for div in first_results:
        location = div["onclick"]
        
        match = LOCATION_REGEX.search(location)
        if match:
            url = match.group(1)
            urls.append(url)
    
    return urls
    
def find_download_url(page_url: str):
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=False)
        
        page = browser.new_page()

        m3u8_urls = set()

        # Fermer automatiquement toute popup qui s'ouvre
        def handle_popup(popup_page):
            print("🚀 Popup détectée, fermeture...")
            popup_page.close()

            # Recliquer sur le bouton play si présent
            try_click_play_and_poster(page)

        page.on("popup", handle_popup)

        # Capturer les réponses m3u8
        def handle_response(response):
            url = response.url
            if url.endswith(".m3u8") or ".m3u8?" in url:
                m3u8_urls.add(url)

        page.on("response", handle_response)

        # Aller sur la page
        page.goto(page_url)
        page.wait_for_load_state("domcontentloaded")

        # Cliquer sur le bouton Play et sur le poster si présents
        try_click_play_and_poster(page)

        # Attendre quelques secondes pour que les requêtes m3u8 arrivent
        page.wait_for_timeout(4000)

        browser.close()

    # Retourner le premier m3u8 "index" trouvé
    urls = []
    for url in m3u8_urls:
        if "index" in url:
            urls.append(url)
    
    if len(urls) == 0:
        return None
    elif len(urls) == 1:
        return urls[0]
    else:
        CONSOLE.print(f"{len(urls)} urls were found")
        for i,url in enumerate(urls):
            CONSOLE.print(f"{i+1} : {url}")
        index = IntPrompt.ask("Enter index of media to download", default=1)
        
        url = urls[index - 1]
        return url

def try_click_play_and_poster(page):
    """
    Clique sur le bouton play et sur le player-poster si présents,
    en laissant quelques secondes au poster pour apparaître.
    """
    # Cliquer sur le bouton play
    try:
        if page.query_selector("button.play-button"):
            page.click("button.play-button", timeout=4000)
            print("▶️ Bouton play cliqué")
    except Exception:
        print("⚠️ Bouton play non trouvé")
        pass

    # Attendre que le poster apparaisse (max 5 secondes)
    try:
        poster = page.wait_for_selector("div.player-poster.clickable", timeout=5000)
        import time 
        time.sleep(2)
        if poster:
            poster.click()
            print("🖼️ Poster cliqué")
    except Exception:
        print("⚠️ Poster non trouvé après attente")
        pass
    