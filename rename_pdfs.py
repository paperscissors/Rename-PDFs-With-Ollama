#!/usr/bin/env python3
"""
PDF Renamer Script

This script renames PDF files based on their content, extracting the author and title
information using AI-powered text analysis. It handles encrypted PDFs and provides
a colorful, informative CLI output with a progress bar and results table.

Usage:
    python rename_pdfs.py <pdf_folder>

Requirements:
    - Python 3.6+
    - Libraries: pdfplumber, PyPDF2, ollama, rich

Author: Assistant
Date: August 26, 2024
Version: 1.1
"""

import os
import sys
import pdfplumber
import ollama
import json
import re
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich.panel import Panel
from PyPDF2 import PdfReader

console = Console()

def is_pdf_encrypted(pdf_path: str) -> bool:
    """
    Check if a PDF file is encrypted.

    Args:
        pdf_path (str): Path to the PDF file.

    Returns:
        bool: True if the PDF is encrypted, False otherwise.
    """
    try:
        with pdfplumber.open(pdf_path) as pdf:
            return False
    except:
        try:
            with open(pdf_path, 'rb') as file:
                reader = PdfReader(file)
                return reader.is_encrypted
        except:
            return True

def extract_text_from_pdf(pdf_path: str) -> str | None:
    """
    Extract text from a PDF file.

    Args:
        pdf_path (str): Path to the PDF file.

    Returns:
        str | None: Extracted text from the PDF, or None if the PDF is encrypted.
    """
    if is_pdf_encrypted(pdf_path):
        return None

    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = ""
            for page in pdf.pages[:2]:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            return text.strip() or "No text could be extracted from the PDF."
    except Exception as e:
        console.print(f"[bold yellow]pdfplumber failed: {e}. Trying PyPDF2...[/bold yellow]")

    try:
        with open(pdf_path, 'rb') as file:
            reader = PdfReader(file)
            text = ""
            for page in reader.pages[:2]:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            return text.strip() or "No text could be extracted from the PDF."
    except Exception as e:
        console.print(f"[bold red]Error extracting text from {pdf_path}: {e}[/bold red]")
        return "Error extracting text from PDF."

def refine_with_llama3(text: str) -> tuple[str | None, str | None]:
    """
    Use Llama3.1 AI model to extract title and author from text.

    Args:
        text (str): The text to analyze.

    Returns:
        tuple[str | None, str | None]: A tuple containing the title and author,
        or (None, None) if extraction failed.
    """
    if not text:
        return None, None
    prompt = f"Given the following text, extract the title and author. If you can't determine either, return null. Respond in JSON format with 'title' and 'author' keys:\n\n{text[:500]}"
    try:
        response = ollama.chat(model="llama3.1", messages=[{"role": "user", "content": prompt}])
        json_match = re.search(r'\{.*\}', response['message']['content'], re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            # Clean up the JSON string
            json_str = re.sub(r'(?<!\\)"([^"]*?)"(?=\s*:)', r'"\1"', json_str)
            json_str = json_str.replace("'", '"')
            json_str = re.sub(r'(\w+):', r'"\1":', json_str)  # Ensure all keys are quoted
            json_str = re.sub(r',\s*}', '}', json_str)  # Remove trailing commas
            
            result = json.loads(json_str)
            title = result.get('title')
            author = result.get('author')
            
            # Ensure title and author are strings or None
            title = str(title) if title and title != "null" else None
            author = str(author) if author and author != "null" else None
            
            return title_case(title) if title else None, title_case(author) if author else None
        return None, None
    except Exception as e:
        console.print(f"[bold red]Error in Ollama call: {e}[/bold red]")
        return None, None

def title_case(s: str) -> str:
    """
    Convert a string to title case, handling exceptions for common words.

    Args:
        s (str): The string to convert.

    Returns:
        str: The string in title case.
    """
    if not s:
        return s
    exceptions = {'a', 'an', 'and', 'as', 'at', 'but', 'by', 'for', 'if', 'in', 'of', 'on', 'or', 'the', 'to', 'with'}
    word_list = re.findall(r"[\w']+|[.,!?;]", s.lower())
    return " ".join(word.capitalize() if i == 0 or word not in exceptions else word for i, word in enumerate(word_list))

def clean_filename(text: str) -> str:
    """
    Clean up a string to be used as a filename.

    Args:
        text (str): The text to clean.

    Returns:
        str: The cleaned text suitable for use in a filename.
    """
    return ''.join(c for c in text if c.isalnum() or c in ' -_')[:100].strip() if text else "Unknown"

def rename_pdf(pdf_path: str) -> tuple[str, str | None, str | None, str]:
    """
    Rename a PDF file based on its content.

    Args:
        pdf_path (str): Path to the PDF file.

    Returns:
        tuple[str, str | None, str | None, str]: A tuple containing the original filename,
        extracted author, extracted title, and new filename.
    """
    text = extract_text_from_pdf(pdf_path)
    if text is None:
        return os.path.basename(pdf_path), "Encrypted", "Encrypted", os.path.basename(pdf_path)
    
    title, author = refine_with_llama3(text)
    clean_title = clean_filename(title) or "Unknown Title"
    clean_author = clean_filename(author) or "Unknown Author"
    new_name = f"{clean_author} - {clean_title}.pdf"
    new_path = os.path.join(os.path.dirname(pdf_path), new_name)
    if os.path.exists(new_path):
        base, ext = os.path.splitext(new_path)
        counter = 1
        while os.path.exists(f"{base}_{counter}{ext}"):
            counter += 1
        new_path = f"{base}_{counter}{ext}"
    
    if clean_author != "Unknown" or clean_title != "Unknown Title":
        os.rename(pdf_path, new_path)
    else:
        new_path = pdf_path  # Keep the original name if we couldn't extract meaningful info
    
    return os.path.basename(pdf_path), author, title, os.path.basename(new_path)

def main(pdf_folder: str):
    """
    Main function to process all PDFs in a folder.

    Args:
        pdf_folder (str): Path to the folder containing PDF files.
    """
    if not os.path.isdir(pdf_folder):
        console.print(f"[bold red]Error: {pdf_folder} is not a valid directory.[/bold red]")
        sys.exit(1)
    
    pdf_files = [f for f in os.listdir(pdf_folder) if f.endswith('.pdf')]
    results = []
    
    with Progress(SpinnerColumn(), "[progress.percentage]{task.percentage:>3.0f}%",
                  BarColumn(), "{task.completed}/{task.total}",
                  TextColumn("[bold blue]{task.description}"),
                  console=console, transient=True) as progress:
        task = progress.add_task("[cyan]Processing PDFs...", total=len(pdf_files))
        for filename in pdf_files:
            pdf_path = os.path.join(pdf_folder, filename)
            result = rename_pdf(pdf_path)
            results.append(result)
            progress.update(task, advance=1, description=f"[cyan]Processing: {filename}")
    
    table = Table(title="PDF Renaming Results")
    table.add_column("Original Filename", style="cyan")
    table.add_column("Author", style="magenta")
    table.add_column("Title", style="green")
    table.add_column("New Filename", style="yellow")
    
    for result in results:
        table.add_row(*result)
    
    console.print(Panel(table, expand=False))

if __name__ == "__main__":
    if len(sys.argv) != 2:
        console.print("[bold red]Usage: python rename_pdfs.py <pdf_folder>[/bold red]")
        sys.exit(1)
    
    pdf_folder = sys.argv[1]
    main(pdf_folder)
