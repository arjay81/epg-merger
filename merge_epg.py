import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import sys

# Configuration
EPG_URLS = [
    'https://epg.pw/xmltv/epg_PH.xml',
    'https://epg.pw/api/epg.xml?lang=en&timezone=VVMvRWFzdGVybg%3D%3D&date=20250517&channel_id=405058',
    'https://epg.pw/api/epg.xml?lang=en&timezone=VVMvRWFzdGVybg%3D%3D&date=20250517&channel_id=412143',
    'https://epg.pw/api/epg.xml?lang=en&timezone=VVMvRWFzdGVybg%3D%3D&date=20250517&channel_id=404926',
    'https://epg.pw/api/epg.xml?lang=en&timezone=VVMvRWFzdGVybg%3D%3D&date=20250517&channel_id=405132',
    'https://epg.pw/api/epg.xml?lang=en&timezone=VVMvRWFzdGVybg%3D%3D&date=20250517&channel_id=369842',
    'https://epg.pw/api/epg.xml?lang=en&timezone=VVMvRWFzdGVybg%3D%3D&date=20250517&channel_id=403813',
    'https://epg.pw/api/epg.xml?lang=en&timezone=VVMvRWFzdGVybg%3D%3D&date=20250517&channel_id=404871',
    'https://epg.pw/api/epg.xml?lang=en&timezone=VVMvRWFzdGVybg%3D%3D&date=20250518&channel_id=429570',
    'https://epg.pw/api/epg.xml?lang=en&timezone=VVMvRWFzdGVybg%3D%3D&date=20250518&channel_id=403541'
]
OUTPUT_FILE = 'merged_guide.xml'

# Update API URLs with current date
def update_api_urls():
    today = datetime.utcnow().strftime('%Y%m%d')
    return [url.replace('date=20250517', f'date={today}') if 'epg.xml?' in url else url for url in EPG_URLS]

# Fetch XML from a URL
def fetch_epg(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        print(f"Fetched {url} successfully")
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}", file=sys.stderr)
        return None

# Merge EPG files
def merge_epgs():
    channels = {}
    programmes = set()
    programme_list = []

    # Fetch all EPGs
    urls = update_api_urls()
    for url in urls:
        xml = fetch_epg(url)
        if not xml:
            continue

        # Parse XML
        try:
            root = ET.fromstring(xml)
            if root.tag != 'tv':
                print(f"Invalid XMLTV format in {url}", file=sys.stderr)
                continue

            # Merge channels
            for channel in root.findall('channel'):
                channel_id = channel.get('id')
                if channel_id:
                    channels[channel_id] = channel

            # Merge programmes
            for programme in root.findall('programme'):
                channel = programme.get('channel')
                start = programme.get('start')
                title_elem = programme.find('title')
                title = title_elem.text if title_elem is not None and title_elem.text else ''
                key = f"{channel}|{start}|{title}"
                if key not in programmes:
                    programmes.add(key)
                    programme_list.append(programme)
        except ET.ParseError as e:
            print(f"Error parsing XML from {url}: {e}", file=sys.stderr)

    # Create new XMLTV structure
    new_root = ET.Element('tv', attrib={'generator-info-name': 'EPG Merger'})
    for channel in channels.values():
        new_root.append(channel)
    for programme in programme_list:
        new_root.append(programme)

    # Save to file
    tree = ET.ElementTree(new_root)
    try:
        tree.write(OUTPUT_FILE, encoding='utf-8', xml_declaration=True)
        print(f"Merged EPG saved to {OUTPUT_FILE} with {len(channels)} channels and {len(programme_list)} programs")
    except IOError as e:
        print(f"Error writing merged EPG: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    merge_epgs()
