import arxiv
import json
import os
from typing import List
from fastmcp import FastMCP
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


PAPER_DIR = "papers"

# Initialize FastMCP server
mcp = FastMCP("research")

@mcp.tool()
def search_papers(topic: str, max_results: int = 5) -> List[str]:
    """
    Search for relevant arXiv based on a topic and store their information.

    Args:
        topic (str): The topic to search for.
        max_results (int, optional): The maximum number of results to retrieve. Defaults to 5.

    Returns:
        List of paper IDs found in the search
    """
    logger.info(f"🔧 TOOL CALLED: search_papers")
    logger.info(f"   Topic: {topic}")
    logger.info(f"   Max: {max_results}")

    # Use arXiv to find the papers
    logger.info("Connecting to ArXiv...")
    client = arxiv.Client()
    logger.info("✅ ArXiv connected...")

    # Search for the most relevant articles matching the queried topic
    logger.info("Search starts...")
    search = arxiv.Search(
        query=topic
        ,max_results=max_results
        ,sort_by=arxiv.SortCriterion.Relevance
    )

    logger.info("Fetching results...")
    papers = client.results(search)

    papers_list = []
    for p in papers:
        papers_list.append(p)

    logger.info(f"✅ Got {len(papers_list)} papers")

    # Create directory for this topic
    path = os.path.join(PAPER_DIR, topic.lower().replace(" ", "_"))
    os.makedirs(path, exist_ok=True)

    file_path = os.path.join(path, "papers_info.json")

    # Try to load existing papers info
    try:
      with open(file_path, "r") as json_file:
        papers_info = json.load(json_file)
    except (FileNotFoundError, json.JSONDecodeError):
      papers_info = {}

    # Process each paper and add to papers_info
    paper_ids = []
    results = []

    for paper in papers_list:
        paper_id = paper.get_short_id()
        paper_ids.append(paper_id)

        paper_info = {
            "title": paper.title
            ,"authors": [author.name for author in paper.authors]
            ,"summary": paper.summary
            ,"pdf_url": paper.pdf_url
            ,"published": str(paper.published.date())
        }
        papers_info[paper_id] = paper_info

    # track return
    results.append(f"{paper_id} - {paper_info['title']}")

    # Save updated papers_info to json file
    with open(file_path, "w", encoding="utf-8") as json_file:
        json.dump(papers_info, json_file, indent=2, ensure_ascii=False)

    logger.info(f"Results are saved in :{file_path}")

    return results


@mcp.tool()
def extract_info(paper_id: str) -> str:
    """
    Search for information about a specific paper across all topic directories.

    Args :
      paper_id : The ID of the paper to look for

    Returns:
      JSON string with paper information if found, error message if not found
    """

    for item in os.listdir(PAPER_DIR):
        item_path = os.path.join(PAPER_DIR, item)
        if os.path.isdir(item_path):
          file_path = os.path.join(item_path, "papers_info.json")
          if os.path.isfile(file_path):
            try:
              with open(file_path, "r") as json_file:
                papers_info = json.load(json_file)
                if paper_id in papers_info:
                  return json.dumps(papers_info[paper_id], indent=2)
            except (FileNotFoundError, json.JSONDecodeError) as e:
              print(f"Error reading {file_path} : {str(e)}")
              continue

    return f"There's no saved information related to paper {paper_id}."

@mcp.resource("papers://folders")
def get_available_folders() -> str:
    """
    List all available topic folders in the papers directory.

    This resource provides a simple list of all available topic folders.
    """
    folders = []

    # Get all topic directories
    if os.path.exists(PAPER_DIR):
        for topic_dir in os.listdir(PAPER_DIR):
            topic_path = os.path.join(PAPER_DIR, topic_dir)
            if os.path.isdir(topic_path):
                papers_file = os.path.join(topic_path, "papers_info.json")
                if os.path.exists(papers_file):
                    folders.append(topic_dir)

    # Create a simple markdown list
    content = "# Available Topics\n\n"
    if folders:
        for folder in folders:
            content += f"- {folder}\n"
        content += f"\nUse @{folder} to access papers in that topic.\n"
    else:
        content += "No topics found.\n"

    return content

@mcp.resource("papers://{topic}")
def get_topic_papers(topic: str) -> str:
    """
    Get detailed information about papers on a specific topic.

    Args:
        topic: The research topic to retrieve papers for
    """
    topic_dir = topic.lower().replace(" ", "_")
    papers_file = os.path.join(PAPER_DIR, topic_dir, "papers_info.json")

    if not os.path.exists(papers_file):
        return f"# No papers found for topic: {topic}\n\nTry searching for papers on this topic first."

    try:
        with open(papers_file, 'r') as f:
            papers_data = json.load(f)

        # Create markdown content with paper details
        content = f"# Papers on {topic.replace('_', ' ').title()}\n\n"
        content += f"Total papers: {len(papers_data)}\n\n"

        for paper_id, paper_info in papers_data.items():
            content += f"## {paper_info['title']}\n"
            content += f"- **Paper ID**: {paper_id}\n"
            content += f"- **Authors**: {', '.join(paper_info['authors'])}\n"
            content += f"- **Published**: {paper_info['published']}\n"
            content += f"- **PDF URL**: [{paper_info['pdf_url']}]({paper_info['pdf_url']})\n\n"
            content += f"### Summary\n{paper_info['summary'][:500]}...\n\n"
            content += "---\n\n"

        return content
    except json.JSONDecodeError:
        return f"# Error reading papers data for {topic}\n\nThe papers data file is corrupted."



@mcp.prompt()
def generate_search_prompt(topic: str, num_papers: int = 5) -> str:
    """Generate a prompt to find and discuss academic papers on a specific topic."""

    return f"""Search for {num_papers} academic papers about '{topic}' using the search_papers tool.

Follow these instructions:
1. Search for papers using search_papers(topic='{topic}', max_results={num_papers})
2. For each paper found, extract and organize:
   - Paper title
   - Authors
   - Publication date
   - Key findings summary
   - Main contributions/innovations
   - Methodologies used
   - Relevance to '{topic}' (justify in 1 sentence why this paper matters)

3. Provide a comprehensive summary:
   - Most impactful papers (justify each choice in 1 sentence)
   - Overview of research state in '{topic}'
   - Common themes and trends
   - Research gaps/future directions


4. Organize findings clearly with headings and bullets.

Present both detailed paper info and high-level synthesis of the research landscape."""


if __name__ == "__main__":
    import os
    # Initialize and run sse
    mcp.run(
        transport="sse",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8001))
    )
