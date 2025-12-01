"""
Documentation Validation Tool

This module validates the technical documentation corpus for completeness,
proper formatting, and quality standards.

Author: Predictive Maintenance Agent
Date: December 1, 2025
"""

import os
import re
from typing import Dict, List


def validate_documentation(docs_dir: str = "data/manuals") -> Dict:
    """
    Validate documentation corpus for completeness and quality.

    Parameters:
    -----------
    docs_dir : str
        Directory containing documentation files

    Returns:
    --------
    dict
        Validation results with pass/fail status
    """
    results = {
        'minimum_files': False,
        'proper_markdown': True,
        'minimum_word_count': True,
        'heading_hierarchy': True,
        'errors': [],
        'warnings': [],
        'file_details': []
    }

    if not os.path.exists(docs_dir):
        results['errors'].append(f"Directory {docs_dir} does not exist")
        return results

    # Check minimum 5 files
    md_files = [f for f in os.listdir(docs_dir) if f.endswith('.md')]

    if len(md_files) < 5:
        results['minimum_files'] = False
        results['errors'].append(f"Only {len(md_files)} markdown files found, need 5")
    else:
        results['minimum_files'] = True

    total_words = 0
    file_stats = []

    for filename in md_files:
        filepath = os.path.join(docs_dir, filename)
        file_result = validate_single_document(filepath, filename)

        file_stats.append(file_result)
        total_words += file_result['word_count']

        # Aggregate errors
        if file_result['word_count'] < 1000:
            results['minimum_word_count'] = False
            results['errors'].append(
                f"{filename}: Only {file_result['word_count']} words (need 1000+)"
            )

        if file_result['heading_count'] < 3:
            results['heading_hierarchy'] = False
            results['errors'].append(
                f"{filename}: Only {file_result['heading_count']} headings (need 3+)"
            )

        if not file_result['has_title']:
            results['proper_markdown'] = False
            results['warnings'].append(
                f"{filename}: Missing top-level title (# heading)"
            )

        if not file_result['has_sections']:
            results['proper_markdown'] = False
            results['warnings'].append(
                f"{filename}: Missing section headings (## headings)"
            )

    results['file_details'] = file_stats

    # Summary statistics
    results['total_files'] = len(md_files)
    results['total_words'] = total_words
    results['average_words'] = total_words // len(md_files) if md_files else 0

    return results


def validate_single_document(filepath: str, filename: str) -> Dict:
    """
    Validate a single markdown document.

    Parameters:
    -----------
    filepath : str
        Full path to document
    filename : str
        Filename for reporting

    Returns:
    --------
    dict
        Document statistics and validation results
    """
    result = {
        'filename': filename,
        'word_count': 0,
        'heading_count': 0,
        'has_title': False,
        'has_sections': False,
        'has_tables': False,
        'has_code_blocks': False,
        'section_titles': []
    }

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Count words (excluding markdown syntax)
        # Remove code blocks
        content_no_code = re.sub(r'```.*?```', '', content, flags=re.DOTALL)
        # Remove markdown links
        content_no_links = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', content_no_code)
        # Count words
        words = content_no_links.split()
        result['word_count'] = len(words)

        # Check for title (# heading)
        result['has_title'] = bool(re.search(r'^#\s+', content, re.MULTILINE))

        # Find all headings
        headings = re.findall(r'^#+\s+.+$', content, re.MULTILINE)
        result['heading_count'] = len(headings)

        # Check for sections (## headings)
        sections = re.findall(r'^##\s+(.+)$', content, re.MULTILINE)
        result['has_sections'] = len(sections) > 0
        result['section_titles'] = sections

        # Check for tables
        result['has_tables'] = bool(re.search(r'\|.*\|', content))

        # Check for code blocks
        result['has_code_blocks'] = bool(re.search(r'```', content))

    except Exception as e:
        result['error'] = str(e)

    return result


def print_validation_report(results: Dict) -> None:
    """
    Print formatted validation report.

    Parameters:
    -----------
    results : dict
        Validation results from validate_documentation()
    """
    print("\n" + "="*70)
    print("DOCUMENTATION VALIDATION REPORT")
    print("="*70)

    # Summary
    print(f"\nSummary:")
    print(f"  Files found: {results['total_files']}")
    print(f"  Total words: {results['total_words']:,}")
    print(f"  Average words per file: {results['average_words']:,}")

    # Overall status
    print(f"\nValidation Results:")

    checks = [
        ('Minimum 5 files', results['minimum_files']),
        ('Proper markdown formatting', results['proper_markdown']),
        ('Minimum word counts', results['minimum_word_count']),
        ('Heading hierarchy', results['heading_hierarchy'])
    ]

    all_passed = True
    for check_name, passed in checks:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"  {status} {check_name}")
        if not passed:
            all_passed = False

    # File details
    if results.get('file_details'):
        print(f"\nFile Details:")
        print(f"  {'Filename':<50} {'Words':>10} {'Headings':>10}")
        print(f"  {'-'*70}")

        for file_stat in results['file_details']:
            print(f"  {file_stat['filename']:<50} "
                  f"{file_stat['word_count']:>10,} "
                  f"{file_stat['heading_count']:>10}")

    # Errors
    if results['errors']:
        print(f"\nErrors:")
        for error in results['errors']:
            print(f"  [ERROR] {error}")

    # Warnings
    if results.get('warnings'):
        print(f"\nWarnings:")
        for warning in results['warnings']:
            print(f"  [WARN] {warning}")

    # Final verdict
    print(f"\n{'='*70}")
    if all_passed and not results['errors']:
        print("[SUCCESS] All validation checks passed!")
    else:
        print("[FAILED] Some validation checks failed - see errors above")
    print("="*70 + "\n")


def check_content_quality(docs_dir: str = "data/manuals") -> Dict:
    """
    Check documentation for content quality indicators.

    Parameters:
    -----------
    docs_dir : str
        Directory containing documentation

    Returns:
    --------
    dict
        Content quality metrics
    """
    results = {
        'has_examples': {},
        'has_procedures': {},
        'has_tables': {},
        'has_references': {},
        'sensor_references': {}
    }

    md_files = [f for f in os.listdir(docs_dir) if f.endswith('.md')]

    for filename in md_files:
        filepath = os.path.join(docs_dir, filename)

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            # Check for examples
            has_examples = bool(
                re.search(r'(example|Example|EXAMPLE)', content) or
                re.search(r'```', content)  # Code blocks often contain examples
            )
            results['has_examples'][filename] = has_examples

            # Check for procedures
            has_procedures = bool(
                re.search(r'(procedure|Procedure|steps|Steps)', content, re.IGNORECASE) or
                re.search(r'^\d+\.\s+', content, re.MULTILINE)  # Numbered lists
            )
            results['has_procedures'][filename] = has_procedures

            # Check for tables
            has_tables = bool(re.search(r'\|.*\|', content))
            results['has_tables'][filename] = has_tables

            # Check for references section
            has_references = bool(
                re.search(r'##\s+References', content) or
                re.search(r'##\s+Related Documents', content)
            )
            results['has_references'][filename] = has_references

            # Count sensor references (sensor_1 through sensor_21)
            sensor_matches = re.findall(r'sensor_\d+', content)
            results['sensor_references'][filename] = len(sensor_matches)

        except Exception as e:
            print(f"Error checking {filename}: {e}")

    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description='Validate technical documentation corpus',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('--docs-dir', type=str, default='data/manuals',
                        help='Documentation directory (default: data/manuals)')
    parser.add_argument('--quality-check', action='store_true',
                        help='Run additional content quality checks')

    args = parser.parse_args()

    # Run validation
    results = validate_documentation(args.docs_dir)
    print_validation_report(results)

    # Run quality checks if requested
    if args.quality_check:
        print("\n" + "="*70)
        print("CONTENT QUALITY CHECKS")
        print("="*70)

        quality = check_content_quality(args.docs_dir)

        print(f"\nQuality Indicators:")
        print(f"  {'Filename':<50} {'Examples':<10} {'Procedures':<12} {'Tables':<8} {'Sensors':>8}")
        print(f"  {'-'*88}")

        all_files = set(quality['has_examples'].keys())
        for filename in sorted(all_files):
            examples = "Yes" if quality['has_examples'].get(filename, False) else "No"
            procedures = "Yes" if quality['has_procedures'].get(filename, False) else "No"
            tables = "Yes" if quality['has_tables'].get(filename, False) else "No"
            sensors = quality['sensor_references'].get(filename, 0)

            print(f"  {filename:<50} {examples:<10} {procedures:<12} {tables:<8} {sensors:>8}")

        print(f"\n{'='*70}\n")
