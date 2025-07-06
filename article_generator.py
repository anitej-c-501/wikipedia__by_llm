from search_scraper import scrape_snippets
import re
from collections import defaultdict
import textwrap
import time

class ArticleGenerator:
    def __init__(self):
        self.min_section_length = 100
        self.max_section_length = 500
        self.wrap_width = 80
        self.reference_counter = 1
        self.references = {}  # Stores all references with unique IDs

    def generate_article(self, topic):
        """Main function to generate a Wikipedia-style article"""
        print(f"\nGenerating article about: {topic}")
        self.reference_counter = 1  # Reset counter for each new article
        self.references = {}

        print("\n[Phase 1] Researching topic...")
        queries = self._generate_search_queries(topic)
        all_snippets = self._gather_information(queries)
        
        print("\n[Phase 2] Organizing content...")
        categorized = self._categorize_snippets(topic, all_snippets)
        outline = self._create_outline(categorized)

        print("\n[Phase 3] Writing article...")
        article = self._write_article(topic, outline, categorized)
        
        return article

    def _generate_search_queries(self, topic):
        """Generate search queries for different aspects of the topic"""
        return [
            f"what is {topic}",
            f"history of {topic}",
            f"importance of {topic}",
            f"key facts about {topic}",
            f"recent developments in {topic}"
        ]

    def _gather_information(self, queries):
        """Gather information from search engines"""
        all_snippets = []
        for query in queries:
            print(f"  Searching: '{query}'")
            snippets = scrape_snippets(query)
            
            # Store snippets with reference information
            for snippet in snippets:
                ref_id = self.reference_counter
                self.references[ref_id] = {
                    'text': snippet['text'],
                    'url': snippet['url'],
                    'domain': snippet['domain'],
                    'query': query
                }
                self.reference_counter += 1
                all_snippets.append(f"{snippet['text']} [{ref_id}]")
            
            time.sleep(1)
            
        return all_snippets

    def _categorize_snippets(self, topic, snippets):
        """Categorize snippets into sections"""
        categories = defaultdict(list)
        
        for snippet in snippets:
            # Simple categorization based on content
            if "history" in snippet.lower():
                categories["History"].append(snippet)
            elif "importance" in snippet.lower() or "significance" in snippet.lower():
                categories["Significance"].append(snippet)
            elif "recent" in snippet.lower() or "new" in snippet.lower():
                categories["Recent Developments"].append(snippet)
            elif "how" in snippet.lower() or "work" in snippet.lower():
                categories["How It Works"].append(snippet)
            else:
                categories["Overview"].append(snippet)
                
        return categories

    def _create_outline(self, categorized):
        """Create a basic article outline"""
        outline = [
            "Introduction",
            *[section for section in categorized.keys()],
            "References"
        ]
        return outline

    def _write_article(self, topic, outline, categorized):
        """Compile the final article"""
        article_lines = []

        article_lines.append(f"== {topic} ==")
        article_lines.append("")

        intro = self._write_section("Overview", categorized.get("Overview", []))
        article_lines.append(intro)
        article_lines.append("")

        for section in outline[1:-2]: 
            if section == "Overview":
                continue
            if section in categorized and categorized[section]:
                content = self._write_section(section, categorized[section])
                article_lines.append(f"== {section} ==")
                article_lines.append("")
                article_lines.append(content)
                article_lines.append("")

        article_lines.append("== References ==")
        article_lines.append("")
        article_lines.extend(self._format_references())
        
        return "\n".join(article_lines)

    def _write_section(self, section_title, snippets):
        """Write a single section of the article"""
        content = []

        if section_title == "Overview":
            content.append(f"{section_title} section introduces the topic.")
        else:
            content.append(f"This section covers {section_title.lower()}.")
        
        for snippet in snippets[:5]:
            clean_text = re.sub(r'\[.*?\]', '', snippet.split('[')[0])
            clean_text = re.sub(r'\s+', ' ', clean_text).strip()
            
            # Get reference number
            ref_match = re.search(r'\[(\d+)\]$', snippet)
            if ref_match:
                ref_num = ref_match.group(1)
                clean_text += f" [{ref_num}]"  # Add reference back
            
            wrapped = textwrap.fill(clean_text, width=self.wrap_width)
            content.append(wrapped)
            content.append("")
        
        return "\n".join(content)

    def _format_references(self):
        """Format all references in Wikipedia style with simplified URL display"""
        ref_lines = []
        for ref_id, ref_data in sorted(self.references.items()):
            url = ref_data['url']
            text = ref_data['text'].strip()

            clean_text = re.sub(r'https?://\S+', '', text).strip()
            
            title_part = clean_text.split(':')[0] if ':' in clean_text else clean_text
            
            if url:
                clean_url = url.split('?')[0]
                clean_url = clean_url.split('#')[0]
                ref_lines.append(f"{ref_id}. ^ \"{title_part}\": {clean_url}")
            else:
                ref_lines.append(f"{ref_id}. ^ \"{title_part}\"")
        
        return ref_lines

if __name__ == "__main__":
    generator = ArticleGenerator()
    
    while True:
        topic = input("\nEnter a topic to research (or 'quit' to exit): ")
        if topic.lower() == 'quit':
            break
            
        article = generator.generate_article(topic)
        print("\n=== Generated Article ===\n")
        print(article)
        
        save = input("\nSave to file? (y/n): ")
        if save.lower() == 'y':
            filename = f"{topic.replace(' ', '_')}_article.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(article)
            print(f"Article saved to {filename}")