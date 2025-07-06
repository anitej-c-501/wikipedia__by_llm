import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import time
import re

HEADERS = {
    'User-Agent': 'Mozilla/5.0'
}

def truncate_incomplete_sentence(text):
    """
    Truncates text to the last complete sentence that ends with a ., !, or ?
    and is not an ellipsis or cutoff.
    """
    # Normalize spacing in ellipsis (e.g., ". . ." → "…")
    text = re.sub(r'\.\s*\.\s*\.', '…', text)

    # Find sentences ending in ., !, or ? (but not the ellipsis …)
    sentences = re.findall(r'[^.!?…]*[.!?]', text)
    
    # Remove any trailing sentence if it ends with an ellipsis
    complete_sentences = [s.strip() for s in sentences if not s.strip().endswith('…')]

    if complete_sentences:
        return ' '.join(complete_sentences)
    return text.strip()

def scrape_bing(query):
    print("[Bing] Searching...")
    url = f"https://www.bing.com/search?q={query.replace(' ', '+')}"
    res = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(res.text, 'html.parser')

    snippets = []
    results = soup.find_all('li', class_='b_algo')
    for result in results:
        title_tag = result.find('h2')
        desc_tag = result.find('p')
        link_tag = result.find('a')
        if title_tag and desc_tag and link_tag:
            title = title_tag.get_text(strip=True)
            desc = desc_tag.get_text(strip=True)
            url = link_tag.get('href', '')
            domain = urlparse(url).netloc if url else "unknown.source"
            snippets.append({
                'title': title,
                'description': desc,
                'url': url,
                'domain': domain
            })
    return snippets

def scrape_duckduckgo(query):
    print("[DuckDuckGo] Searching...")
    url = f"https://html.duckduckgo.com/html/?q={query.replace(' ', '+')}"
    res = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(res.text, 'html.parser')

    snippets = []
    for result in soup.find_all('div', class_='result__body'):
        title = result.find('a', class_='result__a')
        desc = result.find('a', class_='result__snippet')
        if title and desc:
            # Extract the actual URL from the redirect link
            redirect_link = title.get('href', '')
            if redirect_link.startswith('//duckduckgo.com/l/'):
                # Parse the actual URL from the redirect
                from urllib.parse import unquote, parse_qs
                try:
                    parsed = parse_qs(redirect_link.split('?')[1])
                    actual_url = unquote(parsed['uddg'][0])
                    domain = urlparse(actual_url).netloc
                except:
                    actual_url = ''
                    domain = 'unknown.source'
            else:
                actual_url = redirect_link
                domain = urlparse(actual_url).netloc if actual_url else 'unknown.source'
            
            snippets.append({
                'title': title.text.strip(),
                'description': desc.text.strip(),
                'url': actual_url,
                'domain': domain
            })
    return snippets

def scrape_snippets(query):
    """Combine results from both search engines and remove duplicates"""
    bing_results = scrape_bing(query)
    ddg_results = scrape_duckduckgo(query)
    all_results = bing_results + ddg_results
    
    # Remove duplicates based on URL
    seen_urls = set()
    unique_results = []
    for result in all_results:
        if result['url'] and result['url'] not in seen_urls:
            seen_urls.add(result['url'])
            unique_results.append(result)
    
    # Format as text snippets with source info
    formatted_snippets = []
    for result in unique_results:
        snippet = f"{result['title']}: {result['description']}"
        truncated = truncate_incomplete_sentence(snippet)
        formatted_snippets.append({
            'text': truncated,
            'url': result['url'],
            'domain': result['domain']
        })
    
    return formatted_snippets