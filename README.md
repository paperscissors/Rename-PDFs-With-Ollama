# PDF Renamer

PDF Renamer is a Python script that automatically renames PDF files based on their content, extracting the author and title information using AI-powered text analysis. It handles encrypted PDFs and provides a colorful, informative CLI output with a progress bar and results table.

## Features

- Extracts author and title information from PDF content using AI (Llama 3.1)
- Handles encrypted PDFs
- Provides colorful CLI output with progress bar and results table
- Renames PDFs based on extracted information
- Handles naming conflicts

## Requirements

- Python 3.6+
- See `requirements.txt` for required libraries

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/pdf-renamer.git
   cd pdf-renamer
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Ensure you have Ollama installed and the Llama 3.1 model available. Follow the instructions on the [Ollama website](https://ollama.ai/) for installation.

## Usage

Run the script from the command line, providing the path to the folder containing the PDFs you want to rename:

```
python rename_pdfs.py <pdf_folder>
```

Replace `<pdf_folder>` with the path to your PDF directory.

## Output

The script will display a progress bar as it processes the PDFs and then show a table with the following information for each file:

- Original Filename
- Extracted Author
- Extracted Title
- New Filename

## Notes

- The script uses the Llama 3.1 AI model through Ollama for text analysis. Ensure you have this set up correctly.
- Encrypted PDFs will be identified but not renamed.
- If the script can't extract meaningful information, the original filename will be kept.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

Created by Assistant on August 26, 2024.

## Version

1.1
