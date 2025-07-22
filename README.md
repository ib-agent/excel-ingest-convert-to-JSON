# Excel to JSON Converter

A powerful Django web application that converts Excel files to comprehensive JSON format, preserving all metadata, formulas, formatting, and structural information.

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r docs/requirements.txt
   ```

2. **Run the application:**
   ```bash
   python manage.py migrate
   python manage.py runserver
   ```

3. **Access the application:**
   Open your browser and navigate to `http://localhost:8000`

## Documentation

- **[Full Documentation](docs/README.md)** - Complete setup and usage guide
- **[JSON Schema Documentation](docs/excel-json-schema.md)** - Comprehensive schema specification
- **[Requirements](docs/requirements.txt)** - Python dependencies

## Features

- **Comprehensive Excel Processing**: Extracts all available data from Excel files
- **Beautiful User Interface**: Modern, responsive web interface with drag-and-drop upload
- **Robust API**: RESTful API endpoints for programmatic access
- **File Format Support**: Supports .xlsx, .xlsm, .xltx, .xltm formats
- **Complete Metadata Extraction**: Formulas, formatting, structural information, and more

## Project Structure

```
excel-ingest-convert-to-JSON/
├── docs/                    # Documentation and requirements
├── converter/              # Main Django app
├── excel_converter/        # Django project settings
├── static/                 # Static files (CSS, JS)
├── media/                  # Uploaded files
└── manage.py              # Django management script
```

For detailed information, see the [full documentation](docs/README.md). 