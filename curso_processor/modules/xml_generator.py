"""
XML Generator module for Curso Processor
Generates podcast XML feeds from processed courses
"""

import os
import re
import json
import uuid
import time
import logging
import datetime
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Any
import xml.dom.minidom as minidom
import xml.etree.ElementTree as ET

from rich.console import Console
from rich.progress import Progress, TaskID
from rich.table import Table
from rich.syntax import Syntax

from utils import file_manager, ui_components
from modules import timestamp_generator

# Configure logging
logger = logging.getLogger("xml_generator")

def generate_podcast_xml(title: str, description: str, author: str, 
                       language: str, image_url: str, audio_url: str,
                       duration: str, pub_date: Optional[str] = None,
                       episode_number: int = 1, season_number: int = 1,
                       explicit: bool = False, keywords: List[str] = None) -> str:
    """
    Generate podcast XML for a single episode
    
    Args:
        title: Episode title
        description: Episode description
        author: Author name
        language: Language code
        image_url: URL to episode image
        audio_url: URL to audio file
        duration: Duration in format HH:MM:SS
        pub_date: Publication date (if None, use current date)
        episode_number: Episode number
        season_number: Season number
        explicit: Whether the episode contains explicit content
        keywords: List of keywords
        
    Returns:
        str: XML string
    """
    # Set default values
    if pub_date is None:
        pub_date = datetime.datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0000")
    
    if keywords is None:
        keywords = []
    
    # Create XML structure
    rss = ET.Element("rss")
    rss.set("version", "2.0")
    rss.set("xmlns:itunes", "http://www.itunes.com/dtds/podcast-1.0.dtd")
    rss.set("xmlns:content", "http://purl.org/rss/1.0/modules/content/")
    rss.set("xmlns:googleplay", "http://www.google.com/schemas/play-podcasts/1.0")
    
    channel = ET.SubElement(rss, "channel")
    
    # Add channel elements
    ET.SubElement(channel, "title").text = title
    ET.SubElement(channel, "description").text = description
    ET.SubElement(channel, "language").text = language
    ET.SubElement(channel, "pubDate").text = pub_date
    ET.SubElement(channel, "itunes:author").text = author
    ET.SubElement(channel, "itunes:explicit").text = "yes" if explicit else "no"
    
    # Add image
    image = ET.SubElement(channel, "itunes:image")
    image.set("href", image_url)
    
    # Add keywords
    if keywords:
        ET.SubElement(channel, "itunes:keywords").text = ",".join(keywords)
    
    # Add item (episode)
    item = ET.SubElement(channel, "item")
    
    ET.SubElement(item, "title").text = title
    ET.SubElement(item, "description").text = description
    ET.SubElement(item, "pubDate").text = pub_date
    ET.SubElement(item, "itunes:author").text = author
    ET.SubElement(item, "itunes:duration").text = duration
    ET.SubElement(item, "itunes:explicit").text = "yes" if explicit else "no"
    
    # Add episode number and season
    ET.SubElement(item, "itunes:episode").text = str(episode_number)
    ET.SubElement(item, "itunes:season").text = str(season_number)
    
    # Add enclosure (audio file)
    enclosure = ET.SubElement(item, "enclosure")
    enclosure.set("url", audio_url)
    enclosure.set("type", "audio/mpeg")
    enclosure.set("length", "0")  # File size, set to 0 as placeholder
    
    # Add image to item
    item_image = ET.SubElement(item, "itunes:image")
    item_image.set("href", image_url)
    
    # Convert to string and pretty print
    rough_string = ET.tostring(rss, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")

def generate_xml_from_data(data_path: str, output_dir: str,
                         audio_url_prefix: str = "https://example.com/podcasts/",
                         image_url: str = "https://example.com/podcast-image.jpg",
                         progress: Optional[Progress] = None,
                         task_id: Optional[int] = None) -> Tuple[bool, str]:
    """
    Generate podcast XML from data file
    
    Args:
        data_path: Path to the data file (JSON)
        output_dir: Directory to save the XML file
        audio_url_prefix: Prefix for audio URLs
        image_url: URL to podcast image
        progress: Rich progress object
        task_id: Task ID for progress tracking
        
    Returns:
        Tuple[bool, str]: Success status and output file path or error message
    """
    try:
        # Update progress if provided
        if progress and task_id is not None:
            progress.update(task_id, description=f"Gerando XML para {os.path.basename(data_path)}")
        
        # Load data
        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Extract metadata
        title = data.get("title", os.path.splitext(os.path.basename(data_path))[0])
        description = data.get("description", "")
        author = data.get("author", "Curso Processor")
        language = data.get("language", "pt-br")
        duration = data.get("duration", "00:30:00")
        episode_number = data.get("episode_number", 1)
        season_number = data.get("season_number", 1)
        explicit = data.get("explicit", False)
        keywords = data.get("keywords", [])
        
        # Generate audio URL
        audio_filename = f"{os.path.splitext(os.path.basename(data_path))[0]}.mp3"
        audio_url = f"{audio_url_prefix.rstrip('/')}/{audio_filename}"
        
        # Generate XML
        xml_content = generate_podcast_xml(
            title=title,
            description=description,
            author=author,
            language=language,
            image_url=image_url,
            audio_url=audio_url,
            duration=duration,
            episode_number=episode_number,
            season_number=season_number,
            explicit=explicit,
            keywords=keywords
        )
        
        # Create output filename
        output_filename = f"{os.path.splitext(os.path.basename(data_path))[0]}.xml"
        output_path = os.path.join(output_dir, output_filename)
        
        # Save XML
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(xml_content)
        
        # Update progress if provided
        if progress and task_id is not None:
            progress.update(task_id, advance=1)
        
        return True, output_path
    
    except Exception as e:
        error_message = f"Erro ao gerar XML para {data_path}: {str(e)}"
        return False, error_message

def batch_generate_xml(data_paths: List[str], output_dir: str,
                     audio_url_prefix: str = "https://example.com/podcasts/",
                     image_url: str = "https://example.com/podcast-image.jpg") -> List[Tuple[bool, str]]:
    """
    Generate podcast XML for multiple data files
    
    Args:
        data_paths: List of data file paths
        output_dir: Directory to save the XML files
        audio_url_prefix: Prefix for audio URLs
        image_url: URL to podcast image
        
    Returns:
        List[Tuple[bool, str]]: List of results (success status and output path or error message)
    """
    results = []
    
    # Create progress bar
    progress = ui_components.create_progress_bar("Gerando XML para podcast")
    
    with progress:
        # Add task
        task = progress.add_task("Iniciando geração de XML...", total=len(data_paths))
        
        # Process each data file
        for data_path in data_paths:
            result = generate_xml_from_data(
                data_path=data_path,
                output_dir=output_dir,
                audio_url_prefix=audio_url_prefix,
                image_url=image_url,
                progress=progress,
                task_id=task
            )
            
            results.append(result)
    
    # Count successful generations
    successful = sum(1 for result in results if result[0])
    
    # Print summary
    ui_components.print_success(f"Geração de XML concluída: {successful}/{len(data_paths)} arquivos processados com sucesso")
    
    return results


class PodcastXMLGenerator:
    """Class for generating podcast XML feeds"""
    
    def __init__(
        self,
        xml_dir: Optional[Union[str, Path]] = None,
        console: Optional[Console] = None
    ):
        """
        Initialize PodcastXMLGenerator
        
        Args:
            xml_dir: Directory to store XML files
            console: Rich console for output
        """
        self.console = console or Console()
        
        # Set XML directory
        if xml_dir:
            self.xml_dir = Path(xml_dir)
        else:
            self.xml_dir = Path(__file__).parent.parent / "data"
        
        # Create directory if it doesn't exist
        self.xml_dir.mkdir(parents=True, exist_ok=True)
        
        # Create backup directory
        self.backup_dir = self.xml_dir / "backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Set timestamps directory
        self.timestamps_dir = self.xml_dir / "timestamps"
        self.timestamps_dir.mkdir(parents=True, exist_ok=True)
        
        # XML namespaces
        self.namespaces = {
            "itunes": "http://www.itunes.com/dtds/podcast-1.0.dtd"
        }
        
        # Register namespaces for pretty printing
        for prefix, uri in self.namespaces.items():
            ET.register_namespace(prefix, uri)
    
    def create_rss_feed(
        self,
        title: str,
        description: str,
        language: str = "pt-BR",
        category: str = "Education",
        author: str = "Curso Processor",
        email: str = "curso@processor.com",
        image_url: Optional[str] = None,
        output_path: Optional[Union[str, Path]] = None
    ) -> Tuple[bool, str]:
        """
        Create a new RSS feed
        
        Args:
            title: Feed title
            description: Feed description
            language: Feed language
            category: iTunes category
            author: Feed author
            email: Author email
            image_url: Feed image URL
            output_path: Path to save the XML file
            
        Returns:
            Tuple[bool, str]: Success status and output path or error message
        """
        try:
            # Create root element
            rss = ET.Element("rss", version="2.0")
            rss.set("xmlns:itunes", "http://www.itunes.com/dtds/podcast-1.0.dtd")
            
            # Create channel element
            channel = ET.SubElement(rss, "channel")
            
            # Add channel metadata
            ET.SubElement(channel, "title").text = title
            ET.SubElement(channel, "description").text = description
            ET.SubElement(channel, "language").text = language
            ET.SubElement(channel, "lastBuildDate").text = self.format_rfc2822_date(datetime.datetime.now())
            ET.SubElement(channel, "generator").text = "Curso Processor XML Generator"
            
            # Add iTunes specific elements
            ET.SubElement(channel, "itunes:author").text = author
            ET.SubElement(channel, "itunes:category", text=category)
            ET.SubElement(channel, "itunes:explicit").text = "no"
            
            # Add owner information
            owner = ET.SubElement(channel, "itunes:owner")
            ET.SubElement(owner, "itunes:name").text = author
            ET.SubElement(owner, "itunes:email").text = email
            
            # Add image if provided
            if image_url:
                image = ET.SubElement(channel, "image")
                ET.SubElement(image, "url").text = image_url
                ET.SubElement(image, "title").text = title
                ET.SubElement(image, "link").text = "#"
                
                # iTunes image
                ET.SubElement(channel, "itunes:image", href=image_url)
            
            # Determine output path if not provided
            if output_path is None:
                output_path = self.xml_dir / "cursos.xml"
            else:
                output_path = Path(output_path)
            
            # Create XML string with pretty formatting
            xml_string = self._pretty_xml(rss)
            
            # Write to file
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(xml_string)
            
            return True, str(output_path)
        
        except Exception as e:
            error_message = f"Error creating RSS feed: {str(e)}"
            logger.error(error_message)
            return False, error_message
    
    def add_course_episode(
        self,
        xml_path: Union[str, Path],
        course_name: str,
        audio_url: str,
        timestamps_content: Optional[str] = None,
        timestamps_path: Optional[Union[str, Path]] = None,
        duration: Optional[str] = None,
        pub_date: Optional[datetime.datetime] = None,
        description: Optional[str] = None,
        author: Optional[str] = None,
        course_id: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Add a course episode to an existing RSS feed
        
        Args:
            xml_path: Path to the XML file
            course_name: Course name
            audio_url: URL to the audio file
            timestamps_content: Timestamps content
            timestamps_path: Path to the timestamps file
            duration: Course duration (HH:MM:SS)
            pub_date: Publication date
            description: Course description
            author: Course author
            course_id: Course ID (if None, will generate a UUID)
            
        Returns:
            Tuple[bool, str]: Success status and output path or error message
        """
        try:
            # Convert paths to Path objects
            xml_path = Path(xml_path)
            
            # Create backup
            self._create_backup(xml_path)
            
            # Parse XML
            tree = ET.parse(xml_path)
            root = tree.getroot()
            
            # Find channel element
            channel = root.find("channel")
            if channel is None:
                return False, "Invalid XML: channel element not found"
            
            # Get timestamps content if path is provided
            if timestamps_content is None and timestamps_path is not None:
                timestamps_path = Path(timestamps_path)
                if timestamps_path.exists():
                    with open(timestamps_path, "r", encoding="utf-8") as f:
                        timestamps_content = f.read()
            
            # Set default values
            if pub_date is None:
                pub_date = datetime.datetime.now()
            
            if course_id is None:
                course_id = self.generate_guid(course_name)
            
            # Create item element
            item = ET.SubElement(channel, "item")
            
            # Add item metadata
            ET.SubElement(item, "title").text = course_name
            
            # Add description with timestamps if available
            if description is None:
                if timestamps_content:
                    description = f"<![CDATA[{timestamps_content}]]>"
                else:
                    description = course_name
            
            ET.SubElement(item, "description").text = description
            
            # Add enclosure
            ET.SubElement(item, "enclosure", url=audio_url, type="audio/mpeg")
            
            # Add guid
            guid = ET.SubElement(item, "guid")
            guid.text = course_id
            guid.set("isPermaLink", "false")
            
            # Add publication date
            ET.SubElement(item, "pubDate").text = self.format_rfc2822_date(pub_date)
            
            # Add iTunes specific elements
            if duration:
                ET.SubElement(item, "itunes:duration").text = duration
            
            if author:
                ET.SubElement(item, "itunes:author").text = author
            
            # Update lastBuildDate
            last_build_date = channel.find("lastBuildDate")
            if last_build_date is not None:
                last_build_date.text = self.format_rfc2822_date(datetime.datetime.now())
            
            # Create XML string with pretty formatting
            xml_string = self._pretty_xml(root)
            
            # Write to file
            with open(xml_path, "w", encoding="utf-8") as f:
                f.write(xml_string)
            
            return True, str(xml_path)
        
        except Exception as e:
            error_message = f"Error adding course episode: {str(e)}"
            logger.error(error_message)
            return False, error_message
    
    def update_existing_feed(
        self,
        xml_path: Union[str, Path],
        title: Optional[str] = None,
        description: Optional[str] = None,
        language: Optional[str] = None,
        category: Optional[str] = None,
        author: Optional[str] = None,
        email: Optional[str] = None,
        image_url: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Update an existing RSS feed
        
        Args:
            xml_path: Path to the XML file
            title: Feed title
            description: Feed description
            language: Feed language
            category: iTunes category
            author: Feed author
            email: Author email
            image_url: Feed image URL
            
        Returns:
            Tuple[bool, str]: Success status and output path or error message
        """
        try:
            # Convert paths to Path objects
            xml_path = Path(xml_path)
            
            # Create backup
            self._create_backup(xml_path)
            
            # Parse XML
            tree = ET.parse(xml_path)
            root = tree.getroot()
            
            # Find channel element
            channel = root.find("channel")
            if channel is None:
                return False, "Invalid XML: channel element not found"
            
            # Update channel metadata
            if title:
                title_elem = channel.find("title")
                if title_elem is not None:
                    title_elem.text = title
            
            if description:
                desc_elem = channel.find("description")
                if desc_elem is not None:
                    desc_elem.text = description
            
            if language:
                lang_elem = channel.find("language")
                if lang_elem is not None:
                    lang_elem.text = language
            
            # Update lastBuildDate
            last_build_date = channel.find("lastBuildDate")
            if last_build_date is not None:
                last_build_date.text = self.format_rfc2822_date(datetime.datetime.now())
            
            # Update iTunes specific elements
            if author:
                author_elem = channel.find("itunes:author")
                if author_elem is not None:
                    author_elem.text = author
            
            if category:
                category_elem = channel.find("itunes:category")
                if category_elem is not None:
                    category_elem.set("text", category)
            
            # Update owner information
            if author or email:
                owner = channel.find("itunes:owner")
                if owner is not None:
                    if author:
                        name_elem = owner.find("itunes:name")
                        if name_elem is not None:
                            name_elem.text = author
                    
                    if email:
                        email_elem = owner.find("itunes:email")
                        if email_elem is not None:
                            email_elem.text = email
            
            # Update image if provided
            if image_url:
                image = channel.find("image")
                if image is not None:
                    url_elem = image.find("url")
                    if url_elem is not None:
                        url_elem.text = image_url
                    
                    if title:
                        img_title_elem = image.find("title")
                        if img_title_elem is not None:
                            img_title_elem.text = title
                
                # Update iTunes image
                itunes_image = channel.find("itunes:image")
                if itunes_image is not None:
                    itunes_image.set("href", image_url)
            
            # Create XML string with pretty formatting
            xml_string = self._pretty_xml(root)
            
            # Write to file
            with open(xml_path, "w", encoding="utf-8") as f:
                f.write(xml_string)
            
            return True, str(xml_path)
        
        except Exception as e:
            error_message = f"Error updating RSS feed: {str(e)}"
            logger.error(error_message)
            return False, error_message
    
    def validate_xml(self, xml_path: Union[str, Path]) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate XML file
        
        Args:
            xml_path: Path to the XML file
            
        Returns:
            Tuple[bool, Dict[str, Any]]: Success status and validation results
        """
        try:
            # Convert paths to Path objects
            xml_path = Path(xml_path)
            
            # Parse XML
            tree = ET.parse(xml_path)
            root = tree.getroot()
            
            # Check if root is rss
            if root.tag != "rss":
                return False, {"error": "Root element is not rss"}
            
            # Check if version is 2.0
            if root.get("version") != "2.0":
                return False, {"error": f"RSS version is not 2.0: {root.get('version')}"}
            
            # Find channel element
            channel = root.find("channel")
            if channel is None:
                return False, {"error": "Channel element not found"}
            
            # Check required channel elements
            required_channel_elements = ["title", "description", "language"]
            missing_elements = []
            
            for element in required_channel_elements:
                if channel.find(element) is None:
                    missing_elements.append(element)
            
            if missing_elements:
                return False, {"error": f"Missing required channel elements: {', '.join(missing_elements)}"}
            
            # Check items
            items = channel.findall("item")
            
            # Validate each item
            invalid_items = []
            
            for i, item in enumerate(items):
                # Check required item elements
                required_item_elements = ["title", "description", "guid"]
                missing_item_elements = []
                
                for element in required_item_elements:
                    if item.find(element) is None:
                        missing_item_elements.append(element)
                
                # Check enclosure
                enclosure = item.find("enclosure")
                if enclosure is None:
                    missing_item_elements.append("enclosure")
                else:
                    # Check enclosure attributes
                    if enclosure.get("url") is None:
                        missing_item_elements.append("enclosure.url")
                    
                    if enclosure.get("type") is None:
                        missing_item_elements.append("enclosure.type")
                
                if missing_item_elements:
                    invalid_items.append({
                        "index": i,
                        "title": item.find("title").text if item.find("title") is not None else f"Item {i}",
                        "missing_elements": missing_item_elements
                    })
            
            if invalid_items:
                return False, {"error": "Invalid items", "invalid_items": invalid_items}
            
            # Validation successful
            return True, {
                "items_count": len(items),
                "channel_title": channel.find("title").text,
                "channel_description": channel.find("description").text,
                "channel_language": channel.find("language").text
            }
        
        except Exception as e:
            error_message = f"Error validating XML: {str(e)}"
            logger.error(error_message)
            return False, {"error": error_message}
    
    def generate_guid(self, course_name: str) -> str:
        """
        Generate a GUID for a course
        
        Args:
            course_name: Course name
            
        Returns:
            str: GUID
        """
        # Create a UUID based on the course name and current time
        namespace = uuid.NAMESPACE_URL
        name = f"curso-processor:{course_name}:{time.time()}"
        return str(uuid.uuid5(namespace, name))
    
    def format_rfc2822_date(self, date: datetime.datetime) -> str:
        """
        Format date in RFC 2822 format
        
        Args:
            date: Date to format
            
        Returns:
            str: Formatted date
        """
        return date.strftime("%a, %d %b %Y %H:%M:%S %z")
    
    def calculate_total_duration(self, durations: List[str]) -> str:
        """
        Calculate total duration from a list of durations
        
        Args:
            durations: List of durations in HH:MM:SS format
            
        Returns:
            str: Total duration in HH:MM:SS format
        """
        total_seconds = 0
        
        for duration in durations:
            # Parse duration
            parts = duration.split(":")
            
            if len(parts) == 3:
                # HH:MM:SS
                hours, minutes, seconds = map(int, parts)
                total_seconds += hours * 3600 + minutes * 60 + seconds
            elif len(parts) == 2:
                # MM:SS
                minutes, seconds = map(int, parts)
                total_seconds += minutes * 60 + seconds
        
        # Format total duration
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    def escape_xml_content(self, content: str) -> str:
        """
        Escape special characters in XML content
        
        Args:
            content: Content to escape
            
        Returns:
            str: Escaped content
        """
        # Replace special characters
        content = content.replace("&", "&amp;")
        content = content.replace("<", "&lt;")
        content = content.replace(">", "&gt;")
        content = content.replace("\"", "&quot;")
        content = content.replace("'", "&apos;")
        
        return content
    
    def _create_backup(self, xml_path: Path) -> Path:
        """
        Create backup of XML file
        
        Args:
            xml_path: Path to XML file
            
        Returns:
            Path: Path to backup file
        """
        # Create timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create backup filename
        backup_filename = f"{xml_path.stem}_backup_{timestamp}{xml_path.suffix}"
        backup_path = self.backup_dir / backup_filename
        
        # Copy file to backup
        try:
            shutil.copy2(xml_path, backup_path)
            logger.info(f"Created backup: {backup_path}")
            return backup_path
        
        except Exception as e:
            logger.error(f"Error creating backup: {str(e)}")
            return xml_path
    
    def _pretty_xml(self, element: ET.Element) -> str:
        """
        Create pretty formatted XML string
        
        Args:
            element: XML element
            
        Returns:
            str: Pretty formatted XML string
        """
        # Convert element to string
        xml_string = ET.tostring(element, encoding="utf-8", method="xml")
        
        # Parse with minidom for pretty printing
        dom = minidom.parseString(xml_string)
        pretty_xml = dom.toprettyxml(indent="  ")
        
        # Remove empty lines
        pretty_xml = "\n".join([line for line in pretty_xml.split("\n") if line.strip()])
        
        return pretty_xml
    
    def preview_xml(self, xml_path: Union[str, Path]) -> None:
        """
        Preview XML file in console
        
        Args:
            xml_path: Path to XML file
        """
        try:
            # Convert paths to Path objects
            xml_path = Path(xml_path)
            
            # Read XML file
            with open(xml_path, "r", encoding="utf-8") as f:
                xml_content = f.read()
            
            # Create syntax object
            syntax = Syntax(xml_content, "xml", theme="nord", line_numbers=True)
            
            # Print to console
            self.console.print(f"[cyan]XML Preview: {xml_path}[/cyan]")
            self.console.print(syntax)
        
        except Exception as e:
            self.console.print(f"[red]Error previewing XML: {str(e)}[/red]")
    
    def generate_timestamps_markdown(
        self,
        course_name: str,
        audio_files: List[Union[str, Path]],
        output_path: Optional[Union[str, Path]] = None
    ) -> Tuple[bool, str]:
        """
        Generate timestamps markdown file
        
        Args:
            course_name: Course name
            audio_files: List of audio files
            output_path: Path to save the markdown file
            
        Returns:
            Tuple[bool, str]: Success status and output path or error message
        """
        try:
            # Convert paths to Path objects
            audio_files = [Path(f) for f in audio_files]
            
            # Determine output path if not provided
            if output_path is None:
                # Create a sanitized filename
                sanitized_name = re.sub(r'[^\w\s-]', '', course_name).strip().lower()
                sanitized_name = re.sub(r'[-\s]+', '_', sanitized_name)
                output_path = self.timestamps_dir / f"{sanitized_name}_timestamps.md"
            else:
                output_path = Path(output_path)
            
            # Ensure parent directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Calculate timestamps
            timestamps = self.calculate_hierarchy_timestamps(audio_files)
            
            # Generate markdown content
            markdown_content = f"# Timestamps - {course_name}\n\n"
            
            # Group by directory
            grouped_timestamps = {}
            
            for file_path, timestamp in timestamps.items():
                # Get parent directory
                parent_dir = file_path.parent.name
                
                if parent_dir not in grouped_timestamps:
                    grouped_timestamps[parent_dir] = []
                
                grouped_timestamps[parent_dir].append((file_path, timestamp))
            
            # Sort groups
            sorted_groups = sorted(grouped_timestamps.items())
            
            # Add timestamps to markdown
            for i, (group_name, group_timestamps) in enumerate(sorted_groups):
                markdown_content += f"## {i+1}. {group_name.title()}\n"
                
                # Sort files within group
                sorted_files = sorted(group_timestamps, key=lambda x: x[0].name)
                
                for file_path, timestamp in sorted_files:
                    markdown_content += f"   {timestamp} {file_path.name}\n"
                
                markdown_content += "\n"
            
            # Write to file
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(markdown_content)
            
            return True, str(output_path)
        
        except Exception as e:
            error_message = f"Error generating timestamps markdown: {str(e)}"
            logger.error(error_message)
            return False, error_message
    
    def calculate_hierarchy_timestamps(
        self,
        audio_files: List[Path]
    ) -> Dict[Path, str]:
        """
        Calculate timestamps based on audio file durations
        
        Args:
            audio_files: List of audio files
            
        Returns:
            Dict[Path, str]: Dictionary mapping file paths to timestamps
        """
        # Get durations
        durations = {}
        total_seconds = 0
        timestamps = {}
        
        # Sort files by directory and then by name
        sorted_files = sorted(audio_files, key=lambda x: (x.parent.name, x.name))
        
        for file_path in sorted_files:
            try:
                # Get duration
                duration = self._get_audio_duration(file_path)
                durations[file_path] = duration
                
                # Calculate timestamp
                timestamp = self.format_timestamp(total_seconds)
                timestamps[file_path] = timestamp
                
                # Add duration to total
                total_seconds += duration
            
            except Exception as e:
                logger.error(f"Error calculating timestamp for {file_path}: {str(e)}")
        
        return timestamps
    
    def format_timestamp(self, seconds: int) -> str:
        """
        Format timestamp
        
        Args:
            seconds: Seconds
            
        Returns:
            str: Formatted timestamp
        """
        # Format timestamp
        minutes = seconds // 60
        hours = minutes // 60
        minutes = minutes % 60
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:00"
        else:
            return f"{minutes:02d}:00"
    
    def _get_audio_duration(self, audio_path: Path) -> int:
        """
        Get audio duration in seconds
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            int: Duration in seconds
        """
        try:
            # Try to use mutagen
            import mutagen
            audio = mutagen.File(audio_path)
            
            if audio is not None and hasattr(audio, "info") and hasattr(audio.info, "length"):
                return int(audio.info.length)
        
        except ImportError:
            logger.warning("Mutagen not installed, using fallback method")
        
        except Exception as e:
            logger.warning(f"Error getting duration with mutagen: {str(e)}")
        
        try:
            # Try to use ffprobe
            import subprocess
            
            cmd = [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(audio_path)
            ]
            
            output = subprocess.check_output(cmd).decode("utf-8").strip()
            return int(float(output))
        
        except Exception as e:
            logger.warning(f"Error getting duration with ffprobe: {str(e)}")
        
        # Fallback to a default duration
        logger.warning(f"Using default duration for {audio_path}")
        return 300  # 5 minutes


def create_podcast_feed(
    title: str,
    description: str,
    output_path: Optional[Union[str, Path]] = None,
    language: str = "pt-BR",
    category: str = "Education",
    author: str = "Curso Processor",
    email: str = "curso@processor.com",
    image_url: Optional[str] = None,
    console: Optional[Console] = None
) -> Tuple[bool, str]:
    """
    Create a new podcast feed
    
    Args:
        title: Feed title
        description: Feed description
        output_path: Path to save the XML file
        language: Feed language
        category: iTunes category
        author: Feed author
        email: Author email
        image_url: Feed image URL
        console: Rich console for output
        
    Returns:
        Tuple[bool, str]: Success status and output path or error message
    """
    generator = PodcastXMLGenerator(console=console)
    return generator.create_rss_feed(
        title=title,
        description=description,
        language=language,
        category=category,
        author=author,
        email=email,
        image_url=image_url,
        output_path=output_path
    )


def add_course_to_feed(
    xml_path: Union[str, Path],
    course_name: str,
    audio_url: str,
    timestamps_path: Optional[Union[str, Path]] = None,
    duration: Optional[str] = None,
    description: Optional[str] = None,
    author: Optional[str] = None,
    console: Optional[Console] = None
) -> Tuple[bool, str]:
    """
    Add a course to an existing podcast feed
    
    Args:
        xml_path: Path to the XML file
        course_name: Course name
        audio_url: URL to the audio file
        timestamps_path: Path to the timestamps file
        duration: Course duration (HH:MM:SS)
        description: Course description
        author: Course author
        console: Rich console for output
        
    Returns:
        Tuple[bool, str]: Success status and output path or error message
    """
    generator = PodcastXMLGenerator(console=console)
    
    # Get timestamps content if path is provided
    timestamps_content = None
    if timestamps_path:
        timestamps_path = Path(timestamps_path)
        if timestamps_path.exists():
            with open(timestamps_path, "r", encoding="utf-8") as f:
                timestamps_content = f.read()
    
    return generator.add_course_episode(
        xml_path=xml_path,
        course_name=course_name,
        audio_url=audio_url,
        timestamps_content=timestamps_content,
        duration=duration,
        author=author,
        description=description
    )


def validate_podcast_feed(
    xml_path: Union[str, Path],
    console: Optional[Console] = None
) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate a podcast feed
    
    Args:
        xml_path: Path to the XML file
        console: Rich console for output
        
    Returns:
        Tuple[bool, Dict[str, Any]]: Success status and validation results
    """
    generator = PodcastXMLGenerator(console=console)
    return generator.validate_xml(xml_path)


def generate_timestamps_markdown(
    course_name: str,
    audio_files: List[Union[str, Path]],
    output_path: Optional[Union[str, Path]] = None,
    console: Optional[Console] = None
) -> Tuple[bool, str]:
    """
    Generate timestamps markdown file
    
    Args:
        course_name: Course name
        audio_files: List of audio files
        output_path: Path to save the markdown file
        console: Rich console for output
        
    Returns:
        Tuple[bool, str]: Success status and output path or error message
    """
    generator = PodcastXMLGenerator(console=console)
    return generator.generate_timestamps_markdown(
        course_name=course_name,
        audio_files=audio_files,
        output_path=output_path
    )

# Helper functions for easier integration with main.py
def create_podcast_feed(
    title: str,
    description: str,
    language: str = "pt-BR",
    category: str = "Education",
    author: str = "Curso Processor",
    email: str = "curso@processor.com",
    image_url: Optional[str] = None,
    output_path: Optional[Union[str, Path]] = None,
    console: Optional[Console] = None
) -> Tuple[bool, str]:
    """
    Create a new podcast RSS feed
    
    Args:
        title: Feed title
        description: Feed description
        language: Feed language
        category: iTunes category
        author: Feed author
        email: Author email
        image_url: Feed image URL
        output_path: Path to save the XML file
        console: Rich console for output
        
    Returns:
        Tuple[bool, str]: Success status and output path or error message
    """
    generator = PodcastXMLGenerator(console=console)
    return generator.create_rss_feed(
        title=title,
        description=description,
        language=language,
        category=category,
        author=author,
        email=email,
        image_url=image_url,
        output_path=output_path
    )

def add_course_to_feed(
    xml_path: Union[str, Path],
    course_name: str,
    audio_url: str,
    timestamps_path: Optional[Union[str, Path]] = None,
    duration: Optional[str] = None,
    author: Optional[str] = None,
    console: Optional[Console] = None
) -> Tuple[bool, str]:
    """
    Add a course episode to an existing podcast feed
    
    Args:
        xml_path: Path to the XML file
        course_name: Course name (episode title)
        audio_url: URL to the audio file
        timestamps_path: Path to the timestamps file
        duration: Audio duration in HH:MM:SS format
        author: Episode author
        console: Rich console for output
        
    Returns:
        Tuple[bool, str]: Success status and output path or error message
    """
    generator = PodcastXMLGenerator(console=console)
    
    # Get timestamps content if provided
    timestamps_content = None
    if timestamps_path and os.path.exists(timestamps_path):
        with open(timestamps_path, "r", encoding="utf-8") as f:
            timestamps_content = f.read()
    
    return generator.add_course_episode(
        xml_path=xml_path,
        course_name=course_name,
        audio_url=audio_url,
        description=timestamps_content,
        duration=duration,
        author=author
    )