#!/usr/bin/env python3
"""
Simple test script for XML generation
"""

import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom

def create_simple_rss():
    """Create a simple RSS feed"""
    # Create root element
    rss = ET.Element("rss", version="2.0")
    rss.set("xmlns:itunes", "http://www.itunes.com/dtds/podcast-1.0.dtd")
    
    # Create channel element
    channel = ET.SubElement(rss, "channel")
    
    # Add channel metadata
    ET.SubElement(channel, "title").text = "Test Podcast Feed"
    ET.SubElement(channel, "description").text = "This is a test podcast feed"
    ET.SubElement(channel, "language").text = "pt-BR"
    
    # Add iTunes specific elements
    ET.SubElement(channel, "itunes:author").text = "Test Author"
    ET.SubElement(channel, "itunes:category", text="Education")
    ET.SubElement(channel, "itunes:explicit").text = "no"
    
    # Add item (episode)
    item = ET.SubElement(channel, "item")
    
    ET.SubElement(item, "title").text = "Test Episode"
    ET.SubElement(item, "description").text = "This is a test episode"
    
    # Add enclosure
    enclosure = ET.SubElement(item, "enclosure")
    enclosure.set("url", "https://example.com/test.mp3")
    enclosure.set("type", "audio/mpeg")
    
    # Convert to string and pretty print
    rough_string = ET.tostring(rss, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    pretty_xml = reparsed.toprettyxml(indent="  ")
    
    # Write to file
    with open("/workspace/test_output/simple_rss.xml", "w", encoding="utf-8") as f:
        f.write(pretty_xml)
    
    print("Created simple RSS feed: /workspace/test_output/simple_rss.xml")
    print(pretty_xml)

if __name__ == "__main__":
    create_simple_rss()