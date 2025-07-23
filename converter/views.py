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
    Upload an Excel file and convert it to JSON
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
        
        # Process the Excel file
        processor = ExcelProcessor()
        json_data = processor.process_file(full_path)
        
        # Clean up temporary file
        default_storage.delete(temp_path)
        
        return Response({
            'success': True,
            'filename': uploaded_file.name,
            'data': json_data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': f'Error processing file: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
def download_json(request):
    """
    Download the processed JSON data as a file
    """
    try:
        data = request.data.get('json_data')
        filename = request.data.get('filename', 'converted_data.json')
        
        if not data:
            return Response(
                {'error': 'No JSON data provided'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create JSON response with proper headers for download
        response = HttpResponse(
            json.dumps(data, indent=2, ensure_ascii=False),
            content_type='application/json'
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}.json"'
        
        return response
        
    except Exception as e:
        return Response(
            {'error': f'Error creating download: {str(e)}'}, 
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
    Transform Excel JSON output to table-oriented format
    """
    try:
        json_data = request.data.get('json_data')
        options = request.data.get('options', {})
        
        if not json_data:
            return Response(
                {'error': 'No JSON data provided'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        processor = TableProcessor()
        table_data = processor.transform_to_table_format(json_data, options)
        
        return Response({
            'success': True,
            'table_data': table_data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': f'Error transforming to table format: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
def resolve_headers(request):
    """
    Resolve row and column headers for data cells in table-oriented JSON
    """
    try:
        table_json = request.data.get('table_json')
        options = request.data.get('options', {})
        
        if not table_json:
            return Response(
                {'error': 'No table JSON data provided'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        resolver = HeaderResolver()
        enhanced_data = resolver.resolve_headers(table_json, options)
        
        return Response({
            'success': True,
            'enhanced_data': enhanced_data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': f'Error resolving headers: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
