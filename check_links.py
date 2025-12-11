#!/usr/bin/env python3
"""
Script to check all links in the README.md file
"""
import re
import requests
from urllib.parse import urlparse
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

def extract_urls_from_markdown(file_path):
    """Extract all URLs from markdown file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find all markdown links [text](url)
    markdown_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
    urls = re.findall(markdown_pattern, content)

    # Extract just the URLs (second group)
    url_list = []
    for text, url in urls:
        # Skip anchor links
        if not url.startswith('#'):
            url_list.append((text, url))

    return url_list

def check_url(url_info, timeout=10):
    """Check if a URL is accessible"""
    text, url = url_info

    # Skip app store and play store links (they often block automated requests)
    if 'apps.apple.com' in url or 'play.google.com' in url:
        return {
            'url': url,
            'text': text,
            'status': 'skipped',
            'reason': 'App store link (often blocks bots)'
        }

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.head(url, headers=headers, timeout=timeout, allow_redirects=True)

        # If HEAD doesn't work, try GET
        if response.status_code >= 400:
            response = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)

        return {
            'url': url,
            'text': text,
            'status': 'working' if response.status_code < 400 else 'broken',
            'status_code': response.status_code
        }
    except requests.exceptions.Timeout:
        return {
            'url': url,
            'text': text,
            'status': 'timeout',
            'reason': 'Request timed out'
        }
    except requests.exceptions.ConnectionError:
        return {
            'url': url,
            'text': text,
            'status': 'broken',
            'reason': 'Connection error'
        }
    except requests.exceptions.RequestException as e:
        return {
            'url': url,
            'text': text,
            'status': 'error',
            'reason': str(e)
        }

def main():
    print("Extracting URLs from README.md...")
    urls = extract_urls_from_markdown('/home/user/Student-Success-Kit/README.md')

    print(f"Found {len(urls)} URLs to check\n")

    # Remove duplicates while preserving order
    seen = set()
    unique_urls = []
    for url_info in urls:
        if url_info[1] not in seen:
            seen.add(url_info[1])
            unique_urls.append(url_info)

    print(f"Checking {len(unique_urls)} unique URLs...\n")

    results = {
        'working': [],
        'broken': [],
        'timeout': [],
        'error': [],
        'skipped': []
    }

    # Check URLs with threading for faster execution
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_url = {executor.submit(check_url, url_info): url_info for url_info in unique_urls}

        completed = 0
        for future in as_completed(future_to_url):
            result = future.result()
            results[result['status']].append(result)
            completed += 1

            if completed % 10 == 0:
                print(f"Progress: {completed}/{len(unique_urls)} URLs checked")

    # Print results
    print("\n" + "="*80)
    print("LINK CHECK RESULTS")
    print("="*80)

    print(f"\n✅ Working: {len(results['working'])}")
    print(f"❌ Broken: {len(results['broken'])}")
    print(f"⏱️  Timeout: {len(results['timeout'])}")
    print(f"⚠️  Error: {len(results['error'])}")
    print(f"⏭️  Skipped: {len(results['skipped'])}")

    if results['broken']:
        print("\n" + "="*80)
        print("BROKEN LINKS:")
        print("="*80)
        for item in results['broken']:
            print(f"\n❌ {item['text']}")
            print(f"   URL: {item['url']}")
            if 'status_code' in item:
                print(f"   Status: {item['status_code']}")
            if 'reason' in item:
                print(f"   Reason: {item['reason']}")

    if results['timeout']:
        print("\n" + "="*80)
        print("TIMEOUT LINKS:")
        print("="*80)
        for item in results['timeout']:
            print(f"\n⏱️  {item['text']}")
            print(f"   URL: {item['url']}")

    if results['error']:
        print("\n" + "="*80)
        print("ERROR LINKS:")
        print("="*80)
        for item in results['error']:
            print(f"\n⚠️  {item['text']}")
            print(f"   URL: {item['url']}")
            print(f"   Reason: {item['reason']}")

    # Save detailed report
    with open('/home/user/Student-Success-Kit/link_check_report.txt', 'w', encoding='utf-8') as f:
        f.write("LINK CHECK REPORT\n")
        f.write("="*80 + "\n\n")
        f.write(f"Total URLs checked: {len(unique_urls)}\n")
        f.write(f"Working: {len(results['working'])}\n")
        f.write(f"Broken: {len(results['broken'])}\n")
        f.write(f"Timeout: {len(results['timeout'])}\n")
        f.write(f"Error: {len(results['error'])}\n")
        f.write(f"Skipped: {len(results['skipped'])}\n\n")

        for status in ['broken', 'timeout', 'error', 'skipped']:
            if results[status]:
                f.write(f"\n{status.upper()} LINKS:\n")
                f.write("="*80 + "\n")
                for item in results[status]:
                    f.write(f"\nText: {item['text']}\n")
                    f.write(f"URL: {item['url']}\n")
                    if 'status_code' in item:
                        f.write(f"Status Code: {item['status_code']}\n")
                    if 'reason' in item:
                        f.write(f"Reason: {item['reason']}\n")

    print("\n\nDetailed report saved to: link_check_report.txt")

if __name__ == "__main__":
    main()
