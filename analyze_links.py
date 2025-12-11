#!/usr/bin/env python3
"""
Analyze links in README.md for common issues (without requiring HTTP access)
"""
import re
from urllib.parse import urlparse
from collections import Counter

def extract_urls_from_markdown(file_path):
    """Extract all URLs from markdown file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find all markdown links [text](url)
    markdown_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
    urls = re.findall(markdown_pattern, content)

    return urls

def analyze_urls(urls):
    """Analyze URLs for common issues"""
    issues = {
        'malformed': [],
        'duplicates': [],
        'suspicious': [],
        'mixed_protocols': [],
        'anchor_links': [],
        'long_urls': []
    }

    url_list = [url for text, url in urls if not url.startswith('#')]
    url_counter = Counter(url_list)

    # Find duplicates
    for url, count in url_counter.items():
        if count > 1:
            issues['duplicates'].append((url, count))

    # Analyze each URL
    for text, url in urls:
        # Skip anchor links
        if url.startswith('#'):
            issues['anchor_links'].append((text, url))
            continue

        # Check for malformed URLs
        if ' ' in url:
            issues['malformed'].append((text, url, 'Contains spaces'))

        # Check for suspicious patterns
        if url.endswith('/') and url.count('/') > 3:
            # This might be intentional, but flag it
            pass

        # Check for http (non-secure)
        if url.startswith('http://') and 'localhost' not in url:
            issues['mixed_protocols'].append((text, url))

        # Check for very long URLs
        if len(url) > 200:
            issues['long_urls'].append((text, url, len(url)))

        # Check for common typos
        if 'http://' in url and url.index('http://') > 0:
            issues['malformed'].append((text, url, 'http:// not at start'))

        if 'https://' in url and url.index('https://') > 0:
            issues['malformed'].append((text, url, 'https:// not at start'))

    return issues, url_counter

def main():
    print("Analyzing links in README.md...")
    print("="*80 + "\n")

    urls = extract_urls_from_markdown('/home/user/Student-Success-Kit/README.md')

    print(f"Total links found: {len(urls)}")

    # Separate anchor links from external links
    external_urls = [(text, url) for text, url in urls if not url.startswith('#')]
    anchor_urls = [(text, url) for text, url in urls if url.startswith('#')]

    print(f"External links: {len(external_urls)}")
    print(f"Anchor links (internal): {len(anchor_urls)}")
    print()

    issues, url_counter = analyze_urls(urls)

    # Report findings
    total_issues = sum(len(v) for v in issues.values() if isinstance(v, list))

    if total_issues == 0:
        print("✅ No obvious issues found with the links!")
    else:
        print(f"⚠️  Found {total_issues} potential issues\n")

    # Duplicates
    if issues['duplicates']:
        print("="*80)
        print(f"DUPLICATE URLS ({len(issues['duplicates'])} found):")
        print("="*80)
        for url, count in sorted(issues['duplicates'], key=lambda x: x[1], reverse=True):
            print(f"\n{count}x: {url}")

    # Malformed URLs
    if issues['malformed']:
        print("\n" + "="*80)
        print(f"MALFORMED URLS ({len(issues['malformed'])} found):")
        print("="*80)
        for text, url, reason in issues['malformed']:
            print(f"\n❌ [{text}]({url})")
            print(f"   Reason: {reason}")

    # Mixed protocols
    if issues['mixed_protocols']:
        print("\n" + "="*80)
        print(f"NON-HTTPS URLS ({len(issues['mixed_protocols'])} found):")
        print("="*80)
        print("(Consider using HTTPS for better security)")
        for text, url in issues['mixed_protocols'][:10]:  # Show first 10
            print(f"\n🔓 [{text}]({url})")
        if len(issues['mixed_protocols']) > 10:
            print(f"\n... and {len(issues['mixed_protocols']) - 10} more")

    # Long URLs
    if issues['long_urls']:
        print("\n" + "="*80)
        print(f"LONG URLS ({len(issues['long_urls'])} found):")
        print("="*80)
        print("(Consider using URL shorteners for readability)")
        for text, url, length in issues['long_urls']:
            print(f"\n📏 [{text}]({url[:80]}...)")
            print(f"   Length: {length} characters")

    # Statistics by domain
    print("\n" + "="*80)
    print("LINK STATISTICS BY DOMAIN:")
    print("="*80)

    domains = {}
    for text, url in external_urls:
        try:
            parsed = urlparse(url)
            domain = parsed.netloc or parsed.path.split('/')[0]
            if domain:
                domains[domain] = domains.get(domain, 0) + 1
        except:
            pass

    top_domains = sorted(domains.items(), key=lambda x: x[1], reverse=True)[:15]
    for domain, count in top_domains:
        print(f"{domain:40} {count:3} links")

    # Save detailed report
    with open('/home/user/Student-Success-Kit/link_analysis_report.txt', 'w', encoding='utf-8') as f:
        f.write("LINK ANALYSIS REPORT\n")
        f.write("="*80 + "\n\n")
        f.write(f"Total links: {len(urls)}\n")
        f.write(f"External links: {len(external_urls)}\n")
        f.write(f"Anchor links: {len(anchor_urls)}\n\n")

        if issues['duplicates']:
            f.write("\nDUPLICATE URLS:\n")
            f.write("="*80 + "\n")
            for url, count in sorted(issues['duplicates'], key=lambda x: x[1], reverse=True):
                f.write(f"{count}x: {url}\n")

        if issues['malformed']:
            f.write("\nMALFORMED URLS:\n")
            f.write("="*80 + "\n")
            for text, url, reason in issues['malformed']:
                f.write(f"\n[{text}]({url})\n")
                f.write(f"Reason: {reason}\n")

        f.write("\n\nALL EXTERNAL LINKS:\n")
        f.write("="*80 + "\n")
        for text, url in external_urls:
            f.write(f"[{text}]({url})\n")

    print("\n\nDetailed report saved to: link_analysis_report.txt")

    # Summary
    print("\n" + "="*80)
    print("SUMMARY:")
    print("="*80)
    print(f"✅ Total links analyzed: {len(urls)}")
    print(f"🔗 External links: {len(external_urls)}")
    print(f"⚓ Internal anchor links: {len(anchor_urls)}")
    print(f"⚠️  Duplicate URLs: {len(issues['duplicates'])}")
    print(f"❌ Malformed URLs: {len(issues['malformed'])}")
    print(f"🔓 Non-HTTPS URLs: {len(issues['mixed_protocols'])}")
    print(f"📏 Long URLs: {len(issues['long_urls'])}")

    print("\n" + "="*80)
    print("NOTE: Due to network restrictions, actual link validation")
    print("(checking if URLs are accessible) cannot be performed in this")
    print("environment. Manual testing is recommended for critical links.")
    print("="*80)

if __name__ == "__main__":
    main()
