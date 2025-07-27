"""
PDF Processing Views

This module handles PDF processing requests and integrates with the PDF_processing module.
"""

import os
import json
import tempfile
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status

# Import our PDF processing module
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from PDF_processing import PDFProcessor


@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def upload_and_process_pdf(request):
    """
    Upload a PDF file and process it to extract tables, text, and numbers
    """
    try:
        if 'file' not in request.FILES:
            return Response(
                {'error': 'No file provided'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        uploaded_file = request.FILES['file']
        
        # Validate file type
        if not uploaded_file.name.lower().endswith('.pdf'):
            return Response(
                {'error': 'File must be a PDF'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get processing options from request
        extract_tables = request.data.get('extract_tables', 'true').lower() == 'true'
        extract_text = request.data.get('extract_text', 'true').lower() == 'true'
        extract_numbers = request.data.get('extract_numbers', 'true').lower() == 'true'
        
        # Save uploaded file temporarily
        temp_path = default_storage.save(
            f'temp/{uploaded_file.name}', 
            ContentFile(uploaded_file.read())
        )
        full_path = os.path.join(settings.MEDIA_ROOT, temp_path)
        
        try:
            # Initialize PDF processor
            processor = PDFProcessor()
            
            # Process the PDF file
            result = processor.process_file(
                full_path,
                extract_tables=extract_tables,
                extract_text=extract_text,
                extract_numbers=extract_numbers
            )
            
            # Clean up temporary file
            try:
                os.remove(full_path)
            except:
                pass
            
            # Return the processing result
            return Response({
                'success': True,
                'result': result,
                'filename': uploaded_file.name
            })
            
        except Exception as e:
            # Clean up temporary file on error
            try:
                os.remove(full_path)
            except:
                pass
            raise e
            
    except Exception as e:
        return Response(
            {'error': f'Processing failed: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
def process_pdf_with_options(request):
    """
    Process PDF with custom options
    """
    try:
        # Get processing options from request
        data = request.data
        
        # Validate required fields
        if 'file_path' not in data:
            return Response(
                {'error': 'File path is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        file_path = data['file_path']
        if not os.path.exists(file_path):
            return Response(
                {'error': 'File not found'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get processing options
        extract_tables = data.get('extract_tables', True)
        extract_text = data.get('extract_text', True)
        extract_numbers = data.get('extract_numbers', True)
        
        # Get custom configuration
        config = data.get('config', {})
        
        # Initialize PDF processor with custom config
        processor = PDFProcessor(config)
        
        # Process the PDF file
        result = processor.process_file(
            file_path,
            extract_tables=extract_tables,
            extract_text=extract_text,
            extract_numbers=extract_numbers
        )
        
        return Response({
            'success': True,
            'result': result
        })
        
    except Exception as e:
        return Response(
            {'error': f'Processing failed: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def get_processing_status(request):
    """
    Get the status of PDF processing capabilities
    """
    try:
        # Check if required dependencies are available
        dependencies = {
            'camelot_py': False,
            'pymupdf': False,
            'pandas': False
        }
        
        try:
            import camelot
            dependencies['camelot_py'] = True
        except ImportError:
            pass
        
        try:
            import fitz
            dependencies['pymupdf'] = True
        except ImportError:
            pass
        
        try:
            import pandas
            dependencies['pandas'] = True
        except ImportError:
            pass
        
        return Response({
            'success': True,
            'dependencies': dependencies,
            'capabilities': {
                'table_extraction': dependencies['camelot_py'] and dependencies['pandas'],
                'text_extraction': dependencies['pymupdf'],
                'number_extraction': dependencies['pymupdf']
            }
        })
        
    except Exception as e:
        return Response(
            {'error': f'Status check failed: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        ) 