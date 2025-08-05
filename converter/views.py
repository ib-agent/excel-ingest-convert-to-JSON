import json
import os
import tempfile
import uuid
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from .excel_processor import ExcelProcessor
from .table_processor import TableProcessor
from .header_resolver import HeaderResolver
from .compact_excel_processor import CompactExcelProcessor
from .compact_table_processor import CompactTableProcessor

# Temporary storage for processed data (in production, use Redis or database)
processed_data_cache = {}


def main_landing(request):
    """
    Main landing page with navigation to Excel and PDF processing
    """
    return render(request, 'converter/main_landing.html')


def excel_processor(request):
    """
    Excel processing page
    """
    return render(request, 'converter/excel_processor.html')


def pdf_processor(request):
    """
    PDF processing page
    """
    return render(request, 'converter/pdf_processor.html')


@csrf_exempt
@require_http_methods(["POST"])
def upload_and_convert(request):
    """
    Upload an Excel file and convert it to JSON with table-oriented format
    Supports both compact and verbose formats via ?format=compact parameter
    """
    print(f"DEBUG: upload_and_convert called with method: {request.method}")
    print(f"DEBUG: Format parameter: {request.GET.get('format', 'not_provided')}")
    print(f"DEBUG: Files in request: {list(request.FILES.keys())}")
    
    try:
        if 'file' not in request.FILES:
            return JsonResponse(
                {'error': 'No file provided'}, 
                status=400
            )
        
        uploaded_file = request.FILES['file']
        
        # Check format parameter
        format_type = request.GET.get('format', 'verbose').lower()
        use_compact = format_type == 'compact'
        
        # Validate file type
        allowed_extensions = ['.xlsx', '.xlsm', '.xltx', '.xltm']
        file_extension = os.path.splitext(uploaded_file.name)[1].lower()
        
        if file_extension not in allowed_extensions:
            return JsonResponse(
                {'error': f'Unsupported file format. Allowed formats: {", ".join(allowed_extensions)}'}, 
                status=400
            )
        
        # Save uploaded file temporarily
        temp_path = default_storage.save(
            f'temp/{uploaded_file.name}', 
            ContentFile(uploaded_file.read())
        )
        full_path = os.path.join(settings.MEDIA_ROOT, temp_path)
        
        # Process the Excel file to get JSON using appropriate processor
        if use_compact:
            processor = CompactExcelProcessor()
            json_data = processor.process_file(full_path)
            
            # Transform to compact table-oriented format
            table_processor = CompactTableProcessor()
            table_data = table_processor.transform_to_compact_table_format(json_data, {})
            
            # No header resolver needed for compact format (labels are built-in)
            enhanced_table_data = table_data
        else:
            processor = ExcelProcessor()
            json_data = processor.process_file(full_path)
            
            # Transform to table-oriented format
            table_processor = TableProcessor()
            table_data = table_processor.transform_to_table_format(json_data, {})
            
            # Resolve headers for enhanced table data
            header_resolver = HeaderResolver()
            enhanced_table_data = header_resolver.resolve_headers(table_data, {})
        
        # Quick size estimation to avoid expensive JSON serialization for large files
        # Estimate based on cell count and sheet structure
        total_cells = sum(len(sheet.get('cells', {})) for sheet in json_data.get('workbook', {}).get('sheets', []))
        estimated_size = total_cells * 200  # Rough estimate: 200 bytes per cell
        
        # Check if response would be too large (>5MB estimated = likely >10MB actual)
        LARGE_FILE_THRESHOLD = 5 * 1024 * 1024  # 5MB estimated threshold
        
        print(f"Debug - File: {uploaded_file.name}")
        print(f"Debug - Format: {format_type}")
        print(f"Debug - Total cells: {total_cells}")
        print(f"Debug - Estimated size: {estimated_size / 1024 / 1024:.2f} MB")
        print(f"Debug - Large file threshold: {LARGE_FILE_THRESHOLD / 1024 / 1024:.2f} MB")
        
        if estimated_size > LARGE_FILE_THRESHOLD:
            print(f"Debug - Processing as large file")
            # For large files, return summary and download links
            if use_compact:
                summary_data = {
                    'workbook': {
                        'meta': json_data.get('workbook', {}).get('meta', {}),
                        'sheets': []
                    }
                }
            else:
                summary_data = {
                    'workbook': {
                        'metadata': json_data.get('workbook', {}).get('metadata', {}),
                        'properties': json_data.get('workbook', {}).get('properties', {}),
                        'sheets': []
                    }
                }
            
            # Add sheet summaries
            sheets = json_data.get('workbook', {}).get('sheets', [])
            print(f"Debug - Number of sheets: {len(sheets)}")
            
            for i, sheet in enumerate(sheets):
                print(f"Debug - Processing sheet {i}: {sheet.get('name', 'Unknown')}")
                print(f"Debug - Sheet keys: {list(sheet.keys())}")
                
                # Check if sheet has tables
                tables = sheet.get('tables', [])
                print(f"Debug - Sheet {i} has {len(tables)} tables")
                
                if use_compact:
                    sheet_summary = {
                        'name': sheet.get('name', 'Unknown'),
                        'table_count': len(tables),
                        'total_rows': sum(len(table.get('labels', {}).get('rows', [])) for table in tables),
                        'total_columns': sum(len(table.get('labels', {}).get('cols', [])) for table in tables)
                    }
                else:
                    sheet_summary = {
                        'name': sheet.get('name', 'Unknown'),
                        'table_count': len(tables),
                        'total_rows': sum(len(table.get('rows', [])) for table in tables),
                        'total_columns': sum(len(table.get('columns', [])) for table in tables)
                    }
                summary_data['workbook']['sheets'].append(sheet_summary)
            
            # Generate a unique identifier for this file
            file_id = str(uuid.uuid4())
            
            # Store the processed data for download
            processed_data_cache[file_id] = {
                'full_data': json_data,
                'table_data': enhanced_table_data,
                'filename': uploaded_file.name,
                'format': format_type
            }
            
            # Clean up old entries (keep only last 10)
            if len(processed_data_cache) > 10:
                oldest_key = next(iter(processed_data_cache))
                del processed_data_cache[oldest_key]
            
            # Clean up temporary file
            default_storage.delete(temp_path)
            
            return JsonResponse({
                'success': True,
                'format': format_type,
                'filename': uploaded_file.name,
                'large_file': True,
                'warning': f'File is very large (estimated {estimated_size / 1024 / 1024:.1f} MB). Use download links below.',
                'summary': summary_data,
                'download_urls': {
                    'full_data': f'/api/download/?type=full&file_id={file_id}',
                    'table_data': f'/api/download/?type=table&file_id={file_id}'
                },
                'file_info': {
                    'estimated_size_mb': estimated_size / 1024 / 1024,
                    'total_cells': total_cells,
                    'sheet_count': len(json_data.get('workbook', {}).get('sheets', [])),
                    'total_tables': sum(len(sheet.get('tables', [])) for sheet in json_data.get('workbook', {}).get('sheets', []))
                },
                'compression_stats': {
                    'format_used': format_type,
                    'estimated_verbose_size_mb': estimated_size / 1024 / 1024 * (3.5 if use_compact else 1.0),
                    'estimated_reduction_percent': 70 if use_compact else 0
                } if use_compact else None
            }, status=200)
        else:
            # For smaller files, calculate actual sizes and return full data
            print(f"Debug - Calculating actual sizes for small file")
            json_data_size = len(json.dumps(json_data, default=str))
            table_data_size = len(json.dumps(enhanced_table_data, default=str))
            total_size = json_data_size + table_data_size
            
            print(f"Debug - Actual JSON data size: {json_data_size / 1024 / 1024:.2f} MB")
            print(f"Debug - Actual table data size: {table_data_size / 1024 / 1024:.2f} MB")
            print(f"Debug - Actual total size: {total_size / 1024 / 1024:.2f} MB")
            
            # Clean up temporary file
            default_storage.delete(temp_path)
            
            response_data = {
                'success': True,
                'format': format_type,
                'filename': uploaded_file.name,
                'large_file': False,
                'data': json_data,
                'table_data': enhanced_table_data,
                'size_metadata': {
                    'full_json_size_bytes': json_data_size,
                    'full_json_size_kb': json_data_size / 1024,
                    'table_data_size_bytes': table_data_size,
                    'table_data_size_kb': table_data_size / 1024,
                    'total_size_bytes': total_size,
                    'total_size_kb': total_size / 1024
                }
            }
            
            # Add compression stats for compact format
            if use_compact:
                response_data['compression_stats'] = {
                    'format_used': format_type,
                    'estimated_verbose_size_mb': total_size / 1024 / 1024 * 3.5,
                    'actual_size_mb': total_size / 1024 / 1024,
                    'estimated_reduction_percent': 70
                }
            
            print(f"Debug - Returning small file response")
            print(f"Debug - Response keys: {list(response_data.keys())}")
            print(f"Debug - Has data key: {'data' in response_data}")
            print(f"Debug - Data structure: {type(response_data['data'])}")
            
            return JsonResponse(response_data, status=200)
        
    except Exception as e:
        return JsonResponse(
            {'error': f'Error processing file: {str(e)}'}, 
            status=500
        )


@api_view(['GET'])
def download_json(request):
    """
    Download the processed JSON data as a file
    """
    try:
        download_type = request.GET.get('type', 'full')
        file_id = request.GET.get('file_id')
        
        if not file_id or file_id not in processed_data_cache:
            return Response(
                {'error': 'File not found or expired'}, 
                status=404
            )
        
        cached_data = processed_data_cache[file_id]
        filename = cached_data['filename']
        format_type = cached_data.get('format', 'verbose')
        
        if download_type == 'full':
            content = json.dumps(cached_data['full_data'], indent=2)
            download_filename = f"{os.path.splitext(filename)[0]}_full_data_{format_type}.json"
        else:  # table
            content = json.dumps(cached_data['table_data'], indent=2)
            download_filename = f"{os.path.splitext(filename)[0]}_table_data_{format_type}.json"
        
        # Create JSON response with proper headers for download
        response = HttpResponse(
            content,
            content_type='application/json'
        )
        response['Content-Disposition'] = f'attachment; filename="{download_filename}"'
        
        return response
        
    except Exception as e:
        return Response(
            {'error': f'Error downloading file: {str(e)}'}, 
            status=500
        )


@csrf_exempt
@require_http_methods(["GET"])
def health_check(request):
    """
    Health check endpoint
    """
    return JsonResponse({
        'status': 'healthy',
        'service': 'Excel to JSON Converter',
        'version': '1.0.0'
    })


def index(request):
    """
    Main page view
    """
    return render(request, 'converter/index.html')


@api_view(['POST'])
def transform_to_tables(request):
    """
    Transform Excel JSON to table-oriented format
    Supports both compact and verbose formats via ?format=compact parameter
    """
    try:
        json_data = request.data.get('json_data')
        
        if not json_data:
            return Response(
                {'error': 'No JSON data provided'}, 
                status=400
            )
        
        # Check format parameter
        format_type = request.GET.get('format', 'verbose').lower()
        use_compact = format_type == 'compact'
        
        # Get options from request
        options = request.data.get('options', {})
        
        # Transform to table-oriented format using appropriate processor
        if use_compact:
            table_processor = CompactTableProcessor()
            table_data = table_processor.transform_to_compact_table_format(json_data, options)
        else:
            table_processor = TableProcessor()
            table_data = table_processor.transform_to_table_format(json_data, options)
        
        response_data = {
            'success': True,
            'format': format_type,
            'table_data': table_data
        }
        
        # Add compression stats for compact format
        if use_compact:
            original_size = len(json.dumps(json_data))
            compressed_size = len(json.dumps(table_data))
            response_data['compression_stats'] = {
                'original_size': original_size,
                'compressed_size': compressed_size,
                'reduction_percent': int((1 - compressed_size / original_size) * 100) if original_size > 0 else 0
            }
        
        return Response(response_data, status=200)
        
    except Exception as e:
        return Response(
            {'error': f'Error transforming data: {str(e)}'}, 
            status=500
        )


@api_view(['POST'])
def resolve_headers(request):
    """
    Resolve headers for table-oriented JSON
    Note: Header resolution is built into compact format, so this is mainly for verbose format
    """
    try:
        table_data = request.data.get('table_data')
        
        if not table_data:
            return Response(
                {'error': 'No table data provided'}, 
                status=400
            )
        
        # Check format parameter
        format_type = request.GET.get('format', 'verbose').lower()
        use_compact = format_type == 'compact'
        
        if use_compact:
            # Compact format already has labels resolved
            return Response({
                'success': True,
                'format': format_type,
                'resolved_data': table_data,
                'message': 'Compact format already includes resolved headers in labels'
            }, status=200)
        else:
            # Resolve headers for verbose format
            header_resolver = HeaderResolver()
            resolved_data = header_resolver.resolve_headers(table_data, {})
            
            return Response({
                'success': True,
                'format': format_type,
                'resolved_data': resolved_data
            }, status=200)
        
    except Exception as e:
        return Response(
            {'error': f'Error resolving headers: {str(e)}'}, 
            status=500
        )
