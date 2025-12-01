"""
Technical Documentation Search Tool

This module provides keyword and TF-IDF based search capabilities for the
technical documentation corpus. Supports both fast keyword search and
higher-quality TF-IDF semantic search.

Author: Predictive Maintenance Agent
Date: December 1, 2025
"""

import os
import re
from typing import List, Dict, Set
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


def load_documents(docs_dir: str = "data/manuals") -> Dict[str, str]:
    """
    Load all markdown documents from directory.

    Parameters:
    -----------
    docs_dir : str
        Directory containing markdown files

    Returns:
    --------
    dict
        Document name -> full text content
    """
    documents = {}

    if not os.path.exists(docs_dir):
        print(f"Warning: Directory {docs_dir} does not exist")
        return documents

    for filename in os.listdir(docs_dir):
        if filename.endswith('.md'):
            filepath = os.path.join(docs_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    documents[filename] = f.read()
            except Exception as e:
                print(f"Error reading {filename}: {e}")

    return documents


def extract_sections(markdown_text: str) -> Dict[str, str]:
    """
    Extract sections from markdown document based on ## headings.

    Parameters:
    -----------
    markdown_text : str
        Full markdown document text

    Returns:
    --------
    dict
        Section title -> section content
    """
    sections = {}
    current_section = "Introduction"
    current_content = []

    lines = markdown_text.split('\n')

    for line in lines:
        # Check if line is a heading (## but not ###)
        if re.match(r'^##\s+', line) and not re.match(r'^###', line):
            # Save previous section
            if current_content:
                sections[current_section] = '\n'.join(current_content)

            # Start new section
            current_section = re.sub(r'^##\s+', '', line).strip()
            # Remove any markdown links from section title
            current_section = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', current_section)
            current_content = []
        else:
            current_content.append(line)

    # Save last section
    if current_content:
        sections[current_section] = '\n'.join(current_content)

    return sections


def extract_snippet(content: str, query_terms: Set[str], snippet_length: int = 300) -> str:
    """
    Extract a snippet around the first matching term.

    Parameters:
    -----------
    content : str
        Full content to extract from
    query_terms : set
        Set of search terms
    snippet_length : int
        Maximum snippet length

    Returns:
    --------
    str
        Content snippet
    """
    content_lower = content.lower()

    # Find first matching term
    first_match_pos = len(content)
    for term in query_terms:
        pos = content_lower.find(term.lower())
        if pos != -1 and pos < first_match_pos:
            first_match_pos = pos

    if first_match_pos == len(content):
        # No match found, return beginning
        snippet = content[:snippet_length]
        if len(content) > snippet_length:
            snippet += "..."
        return snippet

    # Extract snippet centered on match
    start = max(0, first_match_pos - snippet_length // 2)
    end = min(len(content), first_match_pos + snippet_length // 2)

    snippet = content[start:end]

    # Add ellipsis if truncated
    if start > 0:
        snippet = "..." + snippet
    if end < len(content):
        snippet = snippet + "..."

    return snippet


def keyword_search(
    query: str,
    documents: Dict[str, str],
    top_n: int
) -> List[Dict]:
    """
    Simple keyword-based search.

    Parameters:
    -----------
    query : str
        Search query
    documents : dict
        Document name -> content mapping
    top_n : int
        Number of results to return

    Returns:
    --------
    list[dict]
        Search results
    """
    query_lower = query.lower()
    query_terms = set(query_lower.split())

    results = []

    for doc_name, content in documents.items():
        sections = extract_sections(content)

        for section_title, section_content in sections.items():
            content_lower = section_content.lower()

            # Count matching terms
            matches = sum(1 for term in query_terms if term in content_lower)

            if matches > 0:
                # Calculate simple relevance score
                relevance = matches / len(query_terms)

                # Extract snippet around first match
                snippet = extract_snippet(section_content, query_terms)

                results.append({
                    'document_name': doc_name,
                    'section_title': section_title,
                    'content_snippet': snippet,
                    'relevance_score': relevance,
                    'full_section_content': section_content
                })

    # Sort by relevance and return top N
    results.sort(key=lambda x: x['relevance_score'], reverse=True)
    return results[:top_n]


def tfidf_search(
    query: str,
    documents: Dict[str, str],
    top_n: int
) -> List[Dict]:
    """
    TF-IDF based search for better semantic matching.

    Parameters:
    -----------
    query : str
        Search query
    documents : dict
        Document name -> content mapping
    top_n : int
        Number of results to return

    Returns:
    --------
    list[dict]
        Search results with relevance scores
    """
    # Prepare corpus
    doc_sections = []
    section_metadata = []

    for doc_name, content in documents.items():
        sections = extract_sections(content)
        for section_title, section_content in sections.items():
            doc_sections.append(section_content)
            section_metadata.append({
                'document_name': doc_name,
                'section_title': section_title,
                'full_content': section_content
            })

    if not doc_sections:
        return []

    # Create TF-IDF vectors
    try:
        vectorizer = TfidfVectorizer(
            stop_words='english',
            max_features=1000,
            ngram_range=(1, 2)  # Include bigrams for better matching
        )
        tfidf_matrix = vectorizer.fit_transform(doc_sections)

        # Vectorize query
        query_vector = vectorizer.transform([query])

        # Calculate cosine similarity
        similarities = cosine_similarity(query_vector, tfidf_matrix)[0]

        # Get top N results
        top_indices = np.argsort(similarities)[-top_n:][::-1]

        results = []
        query_terms = set(query.lower().split())

        for idx in top_indices:
            if similarities[idx] > 0:  # Only include if similarity > 0
                metadata = section_metadata[idx]
                snippet = extract_snippet(metadata['full_content'], query_terms)

                results.append({
                    'document_name': metadata['document_name'],
                    'section_title': metadata['section_title'],
                    'content_snippet': snippet,
                    'relevance_score': float(similarities[idx]),
                    'full_section_content': metadata['full_content']
                })

        return results

    except Exception as e:
        print(f"TF-IDF search error: {e}")
        # Fall back to keyword search
        return keyword_search(query, documents, top_n)


def search_documents(
    query: str,
    docs_dir: str = "data/manuals",
    top_n: int = 5,
    search_method: str = "tfidf"
) -> List[Dict]:
    """
    Search technical documentation for relevant information.

    Parameters:
    -----------
    query : str
        Search query
    docs_dir : str
        Directory containing documentation
    top_n : int
        Number of results to return
    search_method : str
        "keyword" (fast) or "tfidf" (better quality)

    Returns:
    --------
    list[dict]
        Results containing document_name, section_title, content_snippet,
        relevance_score, full_section_content
    """
    documents = load_documents(docs_dir)

    if not documents:
        print("No documents found to search")
        return []

    if search_method == "keyword":
        return keyword_search(query, documents, top_n)
    else:
        return tfidf_search(query, documents, top_n)


def load_document(
    document_name: str,
    section: str = None,
    docs_dir: str = "data/manuals"
) -> str:
    """
    Load full document or specific section.

    Parameters:
    -----------
    document_name : str
        Name of markdown file
    section : str, optional
        Specific section heading to retrieve
    docs_dir : str
        Directory containing documents

    Returns:
    --------
    str
        Full document text or section content
    """
    filepath = os.path.join(docs_dir, document_name)

    if not os.path.exists(filepath):
        return f"Document '{document_name}' not found"

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        if section is None:
            return content

        sections = extract_sections(content)
        if section in sections:
            return sections[section]
        else:
            available = ', '.join(sections.keys())
            return f"Section '{section}' not found. Available sections: {available}"

    except Exception as e:
        return f"Error reading document: {e}"


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description='Search technical documentation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python document_search.py "bearing failure"
  python document_search.py "high temperature sensor" --method keyword
  python document_search.py "overheating" --top-n 10
  python document_search.py "vibration analysis" --method tfidf
        """
    )

    parser.add_argument('query', type=str, help='Search query')
    parser.add_argument('--method', type=str, default='tfidf',
                        choices=['keyword', 'tfidf'],
                        help='Search method (default: tfidf)')
    parser.add_argument('--top-n', type=int, default=5,
                        help='Number of results (default: 5)')
    parser.add_argument('--docs-dir', type=str, default='data/manuals',
                        help='Documentation directory')

    args = parser.parse_args()

    print(f"\n{'='*70}")
    print(f"Searching for: '{args.query}'")
    print(f"Method: {args.method}")
    print(f"{'='*70}\n")

    results = search_documents(
        args.query,
        docs_dir=args.docs_dir,
        search_method=args.method,
        top_n=args.top_n
    )

    if not results:
        print("No results found.")
    else:
        for i, result in enumerate(results, 1):
            print(f"{i}. [{result['document_name']}] {result['section_title']}")
            print(f"   Relevance: {result['relevance_score']:.3f}")
            print(f"   Snippet: {result['content_snippet'][:200]}")
            if len(result['content_snippet']) > 200:
                print("   ...")
            print()

    print(f"{'='*70}")
    print(f"Found {len(results)} results")
    print(f"{'='*70}\n")
