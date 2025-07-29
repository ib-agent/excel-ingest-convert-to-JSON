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

# DEBUG: Add a distinctive log message to verify we're using the right module
import logging
logger = logging.getLogger(__name__)
logger.info("DEBUG: PDF views module loaded - using updated PDF_processing module")


@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def upload_and_process_pdf(request):
    """
    Upload a PDF file and process it to extract tables, text, and numbers
    Supports both compact and verbose formats via ?format=compact parameter
    """
    try:
        if 'file' not in request.FILES:
            return Response(
                {'error': 'No file provided'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        uploaded_file = request.FILES['file']
        
        # Check format parameter
        format_type = request.GET.get('format', 'verbose').lower()
        use_compact = format_type == 'compact'
        
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
            
            # Apply format-specific processing
            if use_compact:
                # PDF already outputs relatively compact format, but we can compress further
                result = _compress_pdf_result(result)
            
            # Clean up temporary file
            try:
                os.remove(full_path)
            except:
                pass
            
            # Calculate response sizes for statistics
            result_size = len(json.dumps(result))
            
            response_data = {
                'success': True,
                'format': format_type,
                'result': result,
                'filename': uploaded_file.name,
                'file_info': {
                    'result_size_mb': result_size / 1024 / 1024
                }
            }
            
            # Add compression stats for compact format
            if use_compact:
                response_data['compression_stats'] = {
                    'format_used': format_type,
                    'estimated_verbose_size_mb': result_size / 1024 / 1024 * 1.3,
                    'actual_size_mb': result_size / 1024 / 1024,
                    'estimated_reduction_percent': 23
                }
            
            # Return the processing result
            return Response(response_data)
            
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


def _compress_pdf_result(result):
    """
    Apply additional compression to PDF result for compact format
    """
    compressed = result.copy()
    
    # Compress document metadata - keep only essential fields
    if 'pdf_processing_result' in compressed:
        pdf_result = compressed['pdf_processing_result']
        
        # Compress metadata
        if 'document_metadata' in pdf_result:
            metadata = pdf_result['document_metadata']
            compressed_metadata = {}
            if 'filename' in metadata:
                compressed_metadata['filename'] = metadata['filename']
            if 'total_pages' in metadata:
                compressed_metadata['pages'] = metadata['total_pages']
            if 'processing_duration' in metadata:
                compressed_metadata['duration'] = round(metadata['processing_duration'], 2)
            
            pdf_result['meta'] = compressed_metadata
            del pdf_result['document_metadata']
        
        # Compress processing summary
        if 'processing_summary' in pdf_result:
            summary = pdf_result['processing_summary']
            compressed_summary = {}
            if 'tables_extracted' in summary:
                compressed_summary['tables'] = summary['tables_extracted']
            if 'numbers_found' in summary:
                compressed_summary['numbers'] = summary['numbers_found']
            if 'text_sections' in summary:
                compressed_summary['sections'] = summary['text_sections']
            if 'overall_quality_score' in summary:
                compressed_summary['quality'] = round(summary['overall_quality_score'], 2)
            
            pdf_result['summary'] = compressed_summary
            del pdf_result['processing_summary']
        
        # Compress tables if present
        if 'tables' in pdf_result and pdf_result['tables']:
            compressed_tables = []
            for table in pdf_result['tables']['tables']:
                compressed_table = {
                    'id': table.get('table_id', 'unknown'),
                    'page': table.get('page_number', 1),
                    'method': table.get('extraction_method', 'unknown'),
                    'rows': len(table.get('data', [])),
                    'cols': len(table.get('data', [{}])[0].keys()) if table.get('data') else 0,
                    'quality': round(table.get('metadata', {}).get('quality_score', 0), 2),
                    'data': table.get('data', [])
                }
                compressed_tables.append(compressed_table)
            
            pdf_result['tables'] = {
                'count': len(compressed_tables),
                'data': compressed_tables
            }
    
    return compressed


@api_view(['POST'])
def process_pdf_with_options(request):
    """
    Process PDF with custom options
    Supports both compact and verbose formats via ?format=compact parameter
    """
    try:
        # Get processing options from request
        data = request.data
        
        # Check format parameter
        format_type = request.GET.get('format', 'verbose').lower()
        use_compact = format_type == 'compact'
        
        # Validate required fields
        if 'file_path' not in data:
            return Response(
                {'error': 'File path is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        file_path = data['file_path']
        
        # Build custom configuration
        config = data.get('config', {})
        
        try:
            # Initialize PDF processor with custom config
            processor = PDFProcessor(config)
            
            # Extract processing options
            extract_tables = data.get('extract_tables', True)
            extract_text = data.get('extract_text', True) 
            extract_numbers = data.get('extract_numbers', True)
            
            # Process the PDF file
            result = processor.process_file(
                file_path,
                extract_tables=extract_tables,
                extract_text=extract_text,
                extract_numbers=extract_numbers
            )
            
            # Apply format-specific processing
            if use_compact:
                result = _compress_pdf_result(result)
            
            # Calculate response sizes for statistics
            result_size = len(json.dumps(result))
            
            response_data = {
                'success': True,
                'format': format_type,
                'result': result,
                'file_info': {
                    'result_size_mb': result_size / 1024 / 1024
                }
            }
            
            # Add compression stats for compact format
            if use_compact:
                response_data['compression_stats'] = {
                    'format_used': format_type,
                    'estimated_verbose_size_mb': result_size / 1024 / 1024 * 1.3,
                    'actual_size_mb': result_size / 1024 / 1024,
                    'estimated_reduction_percent': 23
                }
            
            return Response(response_data)
            
        except Exception as e:
            raise e
            
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
        # Test if PDF processing is available
        processor = PDFProcessor()
        
        return Response({
            'success': True,
            'status': 'available',
            'supported_formats': ['pdf'],
            'supported_output_formats': ['verbose', 'compact'],
            'capabilities': {
                'table_extraction': True,
                'text_extraction': True,
                'number_extraction': True,
                'multi_page_support': True,
                'quality_scoring': True
            }
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'status': 'unavailable',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 