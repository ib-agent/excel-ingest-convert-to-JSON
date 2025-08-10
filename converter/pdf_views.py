"""
PDF Processing Views

This module handles PDF processing requests and integrates with the PDF_processing module.
"""

import os
import json
import tempfile
import uuid
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
from .storage_service import get_storage_service, StorageService, StorageType
from .processing_registry import processing_registry
from .pdf_ai_failover_pipeline import PDFAIFailoverPipeline

# Import our PDF processing modules
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PDF_processing_pdfplumber import PDFProcessor

# Import the new table removal processor
from pdf_table_removal_processor import PDFTableRemovalProcessor

# DEBUG: Add a distinctive log message to verify we're using the right module
import logging
logger = logging.getLogger(__name__)
logger.info("DEBUG: PDF views module loaded - using ENHANCED PDFPlumber implementation with TABLE REMOVAL support")


@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def upload_and_process_pdf(request):
    """
    Upload a PDF file and process it to extract tables, text, and numbers
    Supports both compact and verbose formats via ?format=compact parameter
    Now supports table removal mode via ?mode=table_removal parameter
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
        
        # Always use table removal mode (traditional mode deprecated)
        processing_mode = 'table_removal'
        use_table_removal = True
        
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
            # Choose processor based on mode
            if use_table_removal:
                # Use new table removal processor
                processor = PDFTableRemovalProcessor()
                result = processor.process(full_path)
                logger.info(f"Processed {uploaded_file.name} using TABLE REMOVAL approach")
            else:
                # Use traditional processor
                processor = PDFProcessor()
                result = processor.process_file(
                    full_path,
                    extract_tables=extract_tables,
                    extract_text=extract_text,
                    extract_numbers=extract_numbers
                )
                logger.info(f"Processed {uploaded_file.name} using TRADITIONAL approach")
            
            # Apply format-specific processing
            if use_compact:
                if use_table_removal:
                    result = _compress_table_removal_result(result)
                else:
                    result = _compress_pdf_result(result)
            
            # Optional storage of original and results
            use_storage_service = os.getenv('USE_STORAGE_SERVICE', 'false').lower() == 'true'
            storage: StorageService | None = get_storage_service() if use_storage_service else None
            processing_id = str(uuid.uuid4()) if use_storage_service else None
            response_storage = None
            if storage is not None and processing_id is not None:
                try:
                    # Store original
                    with open(full_path, 'rb') as f:
                        original_bytes = f.read()
                    original_ref = storage.store_file(
                        data=original_bytes,
                        storage_type=StorageType.ORIGINAL_FILE,
                        filename=uploaded_file.name,
                        metadata={'processing_id': processing_id, 'type': 'pdf'}
                    )
                    # Store result JSON
                    result_ref = storage.store_json(
                        data=result,
                        storage_type=StorageType.PROCESSED_JSON,
                        key_prefix=f"{processing_id}"
                    )
                    response_storage = {
                        'processing_id': processing_id,
                        'original_file': original_ref.__dict__,
                        'processed_json': result_ref.__dict__,
                        'download_urls': {
                            'original_file': storage.get_download_url(original_ref),
                            'processed_json': storage.get_download_url(result_ref),
                        }
                    }
                except Exception:
                    response_storage = None

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
                'processing_mode': processing_mode,
                'result': result,
                'filename': uploaded_file.name,
                'file_info': {
                    'result_size_mb': result_size / 1024 / 1024
                },
                'duplicate_prevention': use_table_removal
            }
            
            # Add compression stats for compact format
            if use_compact:
                response_data['compression_stats'] = {
                    'format_used': format_type,
                    'estimated_verbose_size_mb': result_size / 1024 / 1024 * 1.3,
                    'actual_size_mb': result_size / 1024 / 1024,
                    'estimated_reduction_percent': 23
                }
            
            # Add table removal benefits info
            if use_table_removal:
                summary = result.get('pdf_processing_result', {}).get('processing_summary', {})
                response_data['table_removal_benefits'] = {
                    'tables_physically_removed': summary.get('tables_removed_from_pdf', 0),
                    'duplicate_prevention_active': summary.get('duplicate_prevention') == 'table_removal_applied',
                    'quality_score': summary.get('overall_quality_score', 0),
                    'guaranteed_separation': True
                }
            
            # Attach storage references if available
            if response_storage is not None:
                response_data['storage'] = response_storage

            # Register processing record
            if response_storage is not None and processing_id is not None:
                try:
                    processing_registry.register(processing_id, {
                        'filename': uploaded_file.name,
                        'type': 'pdf',
                        'storage': response_storage,
                        'format': format_type,
                        'mode': processing_mode,
                    })
                except Exception:
                    pass

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


@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def upload_and_process_pdf_with_table_removal(request):
    """
    Dedicated endpoint for table removal processing
    Upload a PDF file and process it using the innovative table removal approach
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
        
        # Save uploaded file temporarily
        temp_path = default_storage.save(
            f'temp/{uploaded_file.name}', 
            ContentFile(uploaded_file.read())
        )
        full_path = os.path.join(settings.MEDIA_ROOT, temp_path)
        
        try:
            # Use table removal processor
            processor = PDFTableRemovalProcessor()
            
            # Get custom configuration if provided
            config = request.data.get('config', {})
            if config:
                processor = PDFTableRemovalProcessor(config)
            
            # Process the PDF file
            result = processor.process(full_path)
            
            # Apply format-specific processing
            if use_compact:
                result = _compress_table_removal_result(result)
            
            # Optional storage of original and results
            use_storage_service = os.getenv('USE_STORAGE_SERVICE', 'false').lower() == 'true'
            storage: StorageService | None = get_storage_service() if use_storage_service else None
            processing_id = str(uuid.uuid4()) if use_storage_service else None
            response_storage = None
            if storage is not None and processing_id is not None:
                try:
                    # Store original
                    with open(full_path, 'rb') as f:
                        original_bytes = f.read()
                    original_ref = storage.store_file(
                        data=original_bytes,
                        storage_type=StorageType.ORIGINAL_FILE,
                        filename=uploaded_file.name,
                        metadata={'processing_id': processing_id, 'type': 'pdf'}
                    )
                    # Store result JSON
                    result_ref = storage.store_json(
                        data=result,
                        storage_type=StorageType.PROCESSED_JSON,
                        key_prefix=f"{processing_id}"
                    )
                    response_storage = {
                        'processing_id': processing_id,
                        'original_file': original_ref.__dict__,
                        'processed_json': result_ref.__dict__,
                        'download_urls': {
                            'original_file': storage.get_download_url(original_ref),
                            'processed_json': storage.get_download_url(result_ref),
                        }
                    }
                except Exception:
                    response_storage = None

            # Clean up temporary file
            try:
                os.remove(full_path)
            except:
                pass
            
            # Calculate response sizes for statistics
            result_size = len(json.dumps(result))
            
            # Extract processing summary
            summary = result.get('pdf_processing_result', {}).get('processing_summary', {})
            
            response_data = {
                'success': True,
                'format': format_type,
                'processing_mode': 'table_removal',
                'result': result,
                'filename': uploaded_file.name,
                'file_info': {
                    'result_size_mb': result_size / 1024 / 1024
                },
                'table_removal_metrics': {
                    'tables_extracted': summary.get('tables_extracted', 0),
                    'tables_removed_from_pdf': summary.get('tables_removed_from_pdf', 0),
                    'text_sections': summary.get('text_sections', 0),
                    'numbers_found': summary.get('numbers_found', 0),
                    'quality_score': summary.get('overall_quality_score', 0),
                    'duplicate_prevention': summary.get('duplicate_prevention'),
                    'processing_duration': result.get('pdf_processing_result', {}).get('document_metadata', {}).get('processing_duration', 0)
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
            
            # Attach storage references if available
            if response_storage is not None:
                response_data['storage'] = response_storage

            # Register processing record
            if response_storage is not None and processing_id is not None:
                try:
                    processing_registry.register(processing_id, {
                        'filename': uploaded_file.name,
                        'type': 'pdf',
                        'storage': response_storage,
                        'format': format_type,
                        'mode': 'table_removal',
                    })
                except Exception:
                    pass

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


def _compress_table_removal_result(result):
    """
    Apply compression to table removal result for compact format
    """
    compressed = result.copy()
    
    if 'pdf_processing_result' in compressed:
        pdf_result = compressed['pdf_processing_result']
        
        # Compress metadata
        if 'document_metadata' in pdf_result:
            metadata = pdf_result['document_metadata']
            compressed_metadata = {
                'filename': metadata.get('filename', ''),
                'pages': metadata.get('total_pages', 0),
                'duration': round(metadata.get('processing_duration', 0), 2),
                'methods': metadata.get('extraction_methods', []),
                'table_removal_applied': metadata.get('table_removal_applied', False)
            }
            pdf_result['meta'] = compressed_metadata
            del pdf_result['document_metadata']
        
        # Compress processing summary
        if 'processing_summary' in pdf_result:
            summary = pdf_result['processing_summary']
            compressed_summary = {
                'tables': summary.get('tables_extracted', 0),
                'tables_removed': summary.get('tables_removed_from_pdf', 0),
                'sections': summary.get('text_sections', 0),
                'numbers': summary.get('numbers_found', 0),
                'quality': round(summary.get('overall_quality_score', 0), 2),
                'duplicate_prevention': summary.get('duplicate_prevention', ''),
                'errors': summary.get('processing_errors', [])
            }
            pdf_result['summary'] = compressed_summary
            del pdf_result['processing_summary']
        
        # Compress tables structure
        if 'tables' in pdf_result and pdf_result['tables']:
            tables_data = pdf_result['tables']
            if 'tables' in tables_data:
                compressed_tables = []
                for table in tables_data['tables']:
                    compressed_table = {
                        'id': table.get('table_id', 'unknown'),
                        'name': table.get('name', ''),
                        'page': table.get('region', {}).get('page_number', 1),
                        'bbox': table.get('region', {}).get('bbox', []),
                        'rows': len(table.get('rows', [])),
                        'cols': len(table.get('columns', [])),
                        'confidence': table.get('metadata', {}).get('confidence', 0),
                        'method': table.get('region', {}).get('detection_method', 'unknown')
                    }
                    
                    # Include simplified row data
                    if 'rows' in table:
                        compressed_table['data'] = []
                        for row in table['rows'][:10]:  # Limit to first 10 rows for compact
                            row_data = {}
                            for cell_key, cell_data in row.get('cells', {}).items():
                                row_data[cell_key] = cell_data.get('value', '')
                            compressed_table['data'].append(row_data)
                    
                    compressed_tables.append(compressed_table)
                
                pdf_result['tables'] = {
                    'count': len(compressed_tables),
                    'data': compressed_tables
                }
        
        # Compress text content structure
        if 'text_content' in pdf_result:
            text_content = pdf_result['text_content']
            compressed_text = {
                'pages': text_content.get('document_metadata', {}).get('total_pages', 0),
                'total_sections': text_content.get('summary', {}).get('total_sections', 0),
                'total_words': text_content.get('summary', {}).get('total_words', 0),
                'total_numbers': text_content.get('summary', {}).get('total_numbers_found', 0),
                'llm_ready_sections': text_content.get('summary', {}).get('llm_ready_sections', 0)
            }
            
            # Include sample sections (first 3)
            if 'pages' in text_content:
                sample_sections = []
                section_count = 0
                for page in text_content['pages']:
                    for section in page.get('sections', []):
                        if section_count < 3:
                            sample_sections.append({
                                'type': section.get('section_type', ''),
                                'content': section.get('content', '')[:200] + '...' if len(section.get('content', '')) > 200 else section.get('content', ''),
                                'word_count': section.get('word_count', 0),
                                'numbers_count': len(section.get('numbers', []))
                            })
                            section_count += 1
                        else:
                            break
                    if section_count >= 3:
                        break
                
                compressed_text['sample_sections'] = sample_sections
            
            pdf_result['text_content'] = compressed_text
    
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
            
            # Optional storage of results (no original file bytes in this endpoint)
            use_storage_service = os.getenv('USE_STORAGE_SERVICE', 'false').lower() == 'true'
            storage: StorageService | None = get_storage_service() if use_storage_service else None
            processing_id = str(uuid.uuid4()) if use_storage_service else None
            response_storage = None
            if storage is not None and processing_id is not None:
                try:
                    result_ref = storage.store_json(
                        data=result,
                        storage_type=StorageType.PROCESSED_JSON,
                        key_prefix=f"{processing_id}"
                    )
                    response_storage = {
                        'processing_id': processing_id,
                        'processed_json': result_ref.__dict__,
                        'download_urls': {
                            'processed_json': storage.get_download_url(result_ref),
                        }
                    }
                except Exception:
                    response_storage = None

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
            
            # Attach storage references if available
            if response_storage is not None:
                response_data['storage'] = response_storage
                try:
                    processing_registry.register(processing_id, {
                        'filename': file_path,
                        'type': 'pdf',
                        'storage': response_storage,
                        'format': format_type,
                        'mode': 'options',
                    })
                except Exception:
                    pass
            
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


@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def upload_and_process_pdf_ai_failover(request):
    """
    Upload a PDF and process it using the AI failover routing pipeline.
    Only numeric page groups are routed to AI; other pages are code-extracted.
    """
    try:
        if 'file' not in request.FILES:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)

        uploaded_file = request.FILES['file']
        if not uploaded_file.name.lower().endswith('.pdf'):
            return Response({'error': 'File must be a PDF'}, status=status.HTTP_400_BAD_REQUEST)

        # Save uploaded file temporarily
        temp_path = default_storage.save(
            f'temp/{uploaded_file.name}',
            ContentFile(uploaded_file.read())
        )
        full_path = os.path.join(settings.MEDIA_ROOT, temp_path)

        try:
            pipeline = PDFAIFailoverPipeline()
            result = pipeline.process(full_path)

            # Optional storage
            use_storage_service = os.getenv('USE_STORAGE_SERVICE', 'false').lower() == 'true'
            storage: StorageService | None = get_storage_service() if use_storage_service else None
            processing_id = str(uuid.uuid4()) if use_storage_service else None
            response_storage = None
            if storage is not None and processing_id is not None:
                try:
                    with open(full_path, 'rb') as f:
                        original_bytes = f.read()
                    original_ref = storage.store_file(
                        data=original_bytes,
                        storage_type=StorageType.ORIGINAL_FILE,
                        filename=uploaded_file.name,
                        metadata={'processing_id': processing_id, 'type': 'pdf'}
                    )
                    result_ref = storage.store_json(
                        data=result,
                        storage_type=StorageType.PROCESSED_JSON,
                        key_prefix=f"{processing_id}"
                    )
                    response_storage = {
                        'processing_id': processing_id,
                        'original_file': original_ref.__dict__,
                        'processed_json': result_ref.__dict__,
                        'download_urls': {
                            'original_file': storage.get_download_url(original_ref),
                            'processed_json': storage.get_download_url(result_ref),
                        }
                    }
                except Exception:
                    response_storage = None

            try:
                os.remove(full_path)
            except:
                pass

            response_data = {
                'success': True,
                'processing_mode': 'ai_failover_routing',
                'result': result,
                'filename': uploaded_file.name,
            }
            if response_storage is not None and processing_id is not None:
                response_data['storage'] = response_storage
                try:
                    processing_registry.register(processing_id, {
                        'filename': uploaded_file.name,
                        'type': 'pdf',
                        'storage': response_storage,
                        'mode': 'ai_failover_routing',
                    })
                except Exception:
                    pass

            return Response(response_data)

        except Exception as e:
            try:
                os.remove(full_path)
            except:
                pass
            raise e

    except Exception as e:
        return Response({'error': f'Processing failed: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)