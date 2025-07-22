# Excel to JSON Converter

A powerful Django web application that converts Excel files to comprehensive JSON format, preserving all metadata, formulas, formatting, and structural information.

## Features

- **Comprehensive Excel Processing**: Extracts all available data from Excel files including:
  - Cell values and formulas
  - Formatting (fonts, colors, borders, alignment)
  - Sheet properties (frozen panes, protection, views)
  - Workbook metadata (creator, dates, properties)
  - Merged cells, data validations, conditional formatting
  - Charts, images, and comments

- **Beautiful User Interface**: Modern, responsive web interface with:
  - Drag-and-drop file upload
  - Real-time progress indicators
  - Syntax-highlighted JSON display
  - File information display
  - One-click JSON download

- **Robust API**: RESTful API endpoints for programmatic access

- **File Format Support**: Supports modern Excel formats:
  - `.xlsx` (Excel Workbook)
  - `.xlsm` (Excel Macro-Enabled Workbook)
  - `.xltx` (Excel Template)
  - `.xltm` (Excel Macro-Enabled Template)

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd excel-ingest-convert-to-JSON
   ```

2. **Create a virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run database migrations**
   ```bash
   python manage.py migrate
   ```

5. **Start the development server**
   ```bash
   python manage.py runserver
   ```

6. **Access the application**
   Open your browser and navigate to `http://localhost:8000`

## Usage

### Web Interface

1. **Upload File**: Drag and drop an Excel file onto the upload area or click to browse
2. **Processing**: The application will automatically process the file and display progress
3. **View Results**: The converted JSON will be displayed in a syntax-highlighted format
4. **Download**: Click the "Download JSON" button to save the JSON file locally

### API Usage

#### Upload and Convert Excel File

**Endpoint**: `POST /api/upload/`

**Request**: Multipart form data with Excel file

**Example using curl**:
```bash
curl -X POST -F "file=@your_file.xlsx" http://localhost:8000/api/upload/
```

**Response**:
```json
{
  "success": true,
  "filename": "your_file.xlsx",
  "data": {
    "workbook": {
      "metadata": {...},
      "sheets": [...],
      "properties": {...}
    }
  }
}
```

#### Download JSON File

**Endpoint**: `POST /api/download/`

**Request Body**:
```json
{
  "json_data": {...},
  "filename": "output_filename"
}
```

**Response**: JSON file download

#### Health Check

**Endpoint**: `GET /api/health/`

**Response**:
```json
{
  "status": "healthy",
  "service": "Excel to JSON Converter",
  "version": "1.0.0"
}
```

## JSON Schema

The application generates comprehensive JSON output that includes:

### Workbook Structure
```json
{
  "workbook": {
    "metadata": {
      "filename": "string",
      "file_size": "number",
      "created_date": "ISO 8601 datetime",
      "modified_date": "ISO 8601 datetime",
      "creator": "string",
      "last_modified_by": "string",
      "title": "string",
      "subject": "string",
      "keywords": "string",
      "category": "string",
      "description": "string",
      "language": "string",
      "revision": "number",
      "version": "string",
      "application": "string",
      "app_version": "string",
      "company": "string",
      "manager": "string",
      "hyperlink_base": "string",
      "template": "string",
      "status": "string",
      "total_editing_time": "number",
      "pages": "number",
      "words": "number",
      "characters": "number",
      "characters_with_spaces": "number",
      "application_name": "string",
      "security": {
        "workbook_password": "boolean",
        "revision_password": "boolean",
        "lock_structure": "boolean",
        "lock_windows": "boolean"
      }
    },
    "sheets": [...],
    "properties": {...}
  }
}
```

### Sheet Information
```json
{
  "sheets": [
    {
      "name": "string",
      "index": "number",
      "sheet_id": "string",
      "state": "visible|hidden|very_hidden",
      "sheet_type": "worksheet|chart|macro",
      "properties": {...},
      "dimensions": {
        "min_row": "number",
        "max_row": "number",
        "min_col": "number",
        "max_col": "number"
      },
      "frozen_panes": {
        "frozen_rows": "number",
        "frozen_cols": "number",
        "top_left_cell": "string"
      },
      "views": [...],
      "protection": {...},
      "rows": [...],
      "columns": [...],
      "cells": {...},
      "merged_cells": [...],
      "data_validations": [...],
      "conditional_formatting": [...],
      "charts": [...],
      "images": [...],
      "comments": [...]
    }
  ]
}
```

### Cell Data
```json
{
  "cells": {
    "A1": {
      "coordinate": "string",
      "row": "number",
      "column": "number",
      "column_letter": "string",
      "value": "any",
      "data_type": "string|number|boolean|date|error|null",
      "formula": "string|null",
      "formula_type": "array|shared|normal|null",
      "shared_formula": "string|null",
      "array_formula": "string|null",
      "comment": {...},
      "hyperlink": {...},
      "style": {
        "font": {...},
        "fill": {...},
        "border": {...},
        "alignment": {...},
        "number_format": "string",
        "protection": {...}
      },
      "is_date": "boolean",
      "is_time": "boolean",
      "is_datetime": "boolean",
      "is_number": "boolean",
      "is_string": "boolean",
      "is_boolean": "boolean",
      "is_error": "boolean",
      "is_empty": "boolean"
    }
  }
}
```

For a complete schema documentation, see [excel-json-schema.md](excel-json-schema.md).

## Configuration

### Environment Variables

The application uses Django's settings system. Key configurations:

- `DEBUG`: Set to `False` in production
- `ALLOWED_HOSTS`: Configure for production deployment
- `FILE_UPLOAD_MAX_MEMORY_SIZE`: Maximum file upload size (default: 50MB)
- `DATA_UPLOAD_MAX_MEMORY_SIZE`: Maximum data upload size (default: 50MB)

### File Upload Limits

- **Maximum file size**: 50MB (configurable)
- **Supported formats**: .xlsx, .xlsm, .xltx, .xltm
- **Processing**: Files are processed in memory and cleaned up automatically

## Development

### Project Structure

```
excel-ingest-convert-to-JSON/
├── converter/                 # Main Django app
│   ├── templates/            # HTML templates
│   ├── excel_processor.py    # Excel processing logic
│   ├── views.py             # API views
│   └── urls.py              # URL routing
├── excel_converter/          # Django project settings
├── static/                   # Static files (CSS, JS)
├── media/                    # Uploaded files
├── requirements.txt          # Python dependencies
├── excel-json-schema.md      # JSON schema documentation
└── README.md                # This file
```

### Running Tests

```bash
python manage.py test
```

### Code Style

The project follows PEP 8 style guidelines. Use a linter like `flake8` or `black` for code formatting.

## Deployment

### Production Setup

1. **Set environment variables**:
   ```bash
   export DEBUG=False
   export ALLOWED_HOSTS=your-domain.com
   export SECRET_KEY=your-secret-key
   ```

2. **Collect static files**:
   ```bash
   python manage.py collectstatic
   ```

3. **Configure web server** (e.g., nginx + gunicorn):
   ```bash
   pip install gunicorn
   gunicorn excel_converter.wsgi:application
   ```

### Docker Deployment

Create a `Dockerfile`:
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN python manage.py collectstatic --noinput

EXPOSE 8000
CMD ["gunicorn", "excel_converter.wsgi:application", "--bind", "0.0.0.0:8000"]
```

## Troubleshooting

### Common Issues

1. **File upload fails**: Check file size limits and supported formats
2. **Processing errors**: Ensure Excel file is not corrupted and is in supported format
3. **Memory issues**: Large files may require increased memory limits

### Error Messages

- `"Unsupported file format"`: File extension not in allowed list
- `"File size too large"`: File exceeds maximum upload size
- `"Error processing file"`: Internal processing error, check file integrity

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
- Create an issue in the repository
- Check the troubleshooting section
- Review the JSON schema documentation

## Changelog

### Version 1.0.0
- Initial release
- Comprehensive Excel to JSON conversion
- Web interface with drag-and-drop upload
- RESTful API endpoints
- Complete metadata extraction
- Formula and formatting preservation 