import json
import os
import tempfile
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
from rest_framework import status
from .excel_processor import ExcelProcessor
from .table_processor import TableProcessor
from .header_resolver import HeaderResolver


@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def upload_and_convert(request):
    """
    Upload an Excel file and convert it to JSON with table-oriented format
    """
    try:
        if 'file' not in request.FILES:
            return Response(
                {'error': 'No file provided'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        uploaded_file = request.FILES['file']
        
        # Validate file type
        allowed_extensions = ['.xlsx', '.xlsm', '.xltx', '.xltm']
        file_extension = os.path.splitext(uploaded_file.name)[1].lower()
        
        if file_extension not in allowed_extensions:
            return Response(
                {'error': f'Unsupported file format. Allowed formats: {", ".join(allowed_extensions)}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Save uploaded file temporarily
        temp_path = default_storage.save(
            f'temp/{uploaded_file.name}', 
            ContentFile(uploaded_file.read())
        )
        full_path = os.path.join(settings.MEDIA_ROOT, temp_path)
        
        # Process the Excel file to get original JSON
        processor = ExcelProcessor()
        json_data = processor.process_file(full_path)
        
        # Transform to table-oriented format
        table_processor = TableProcessor()
        table_data = table_processor.transform_to_table_format(json_data, {})
        
        # Resolve headers for enhanced table data
        header_resolver = HeaderResolver()
        enhanced_table_data = header_resolver.resolve_headers(table_data, {})
        
        # Calculate response sizes
        json_data_size = len(json.dumps(json_data))
        table_data_size = len(json.dumps(enhanced_table_data))
        total_size = json_data_size + table_data_size
        
        # Check if response would be too large (>10MB)
        LARGE_FILE_THRESHOLD = 10 * 1024 * 1024  # 10MB
        
        if total_size > LARGE_FILE_THRESHOLD:
            # For large files, return summary and download links
            summary_data = {
                'workbook': {
                    'metadata': json_data.get('workbook', {}).get('metadata', {}),
                    'properties': json_data.get('workbook', {}).get('properties', {}),
                    'sheets': []
                }
            }
            
            # Add sheet summaries
            for sheet in json_data.get('workbook', {}).get('sheets', []):
                sheet_summary = {
                    'name': sheet.get('name', 'Unknown'),
                    'table_count': len(sheet.get('tables', [])),
                    'total_rows': sum(len(table.get('rows', [])) for table in sheet.get('tables', [])),
                    'total_columns': sum(len(table.get('columns', [])) for table in sheet.get('tables', []))
                }
                summary_data['workbook']['sheets'].append(sheet_summary)
            
            # Clean up temporary file
            default_storage.delete(temp_path)
            
            return Response({
                'success': True,
                'filename': uploaded_file.name,
                'large_file': True,
                'warning': f'File is very large ({total_size / 1024 / 1024:.1f} MB). Use download links below.',
                'summary': summary_data,
                'download_urls': {
                    'full_data': f'/api/download-json/?type=full&filename={uploaded_file.name}',
                    'table_data': f'/api/download-json/?type=table&filename={uploaded_file.name}'
                },
                'file_info': {
                    'total_size_mb': total_size / 1024 / 1024,
                    'json_data_size_mb': json_data_size / 1024 / 1024,
                    'table_data_size_mb': table_data_size / 1024 / 1024,
                    'sheet_count': len(json_data.get('workbook', {}).get('sheets', [])),
                    'total_tables': sum(len(sheet.get('tables', [])) for sheet in json_data.get('workbook', {}).get('sheets', []))
                }
            }, status=status.HTTP_200_OK)
        else:
            # For smaller files, return full data
            # Clean up temporary file
            default_storage.delete(temp_path)
            
            return Response({
                'success': True,
                'filename': uploaded_file.name,
                'large_file': False,
                'data': json_data,
                'table_data': enhanced_table_data
            }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': f'Error processing file: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def download_json(request):
    """
    Download the processed JSON data as a file
    """
    try:
        download_type = request.GET.get('type', 'full')
        filename = request.GET.get('filename', 'converted_data.json')
        
        # For now, return a placeholder response
        # In a real implementation, you would store the processed data temporarily
        # and retrieve it here based on the filename
        
        if download_type == 'full':
            content = json.dumps({'message': 'Full data download not yet implemented'}, indent=2)
            download_filename = f"{os.path.splitext(filename)[0]}_full_data.json"
        else:  # table
            content = json.dumps({'message': 'Table data download not yet implemented'}, indent=2)
            download_filename = f"{os.path.splitext(filename)[0]}_table_data.json"
        
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
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
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
    """
    try:
        json_data = request.data.get('json_data')
        
        if not json_data:
            return Response(
                {'error': 'No JSON data provided'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Transform to table-oriented format
        table_processor = TableProcessor()
        table_data = table_processor.transform_to_table_format(json_data, {})
        
        return Response({
            'success': True,
            'table_data': table_data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': f'Error transforming data: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
def resolve_headers(request):
    """
    Resolve headers for table-oriented JSON
    """
    try:
        table_data = request.data.get('table_data')
        
        if not table_data:
            return Response(
                {'error': 'No table data provided'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Resolve headers
        header_resolver = HeaderResolver()
        resolved_data = header_resolver.resolve_headers(table_data, {})
        
        return Response({
            'success': True,
            'resolved_data': resolved_data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': f'Error resolving headers: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
