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
from .compact_excel_processor import CompactExcelProcessor
from .compact_table_processor import CompactTableProcessor
from .excel_complexity_analyzer import ExcelComplexityAnalyzer
from .excel_processor import ExcelProcessor
from .complexity_preserving_compact_processor import ComplexityPreservingCompactProcessor
from .anthropic_excel_client import AnthropicExcelClient
from .ai_result_parser import AIResultParser
from .comparison_engine import ComparisonEngine

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
    Upload an Excel file and convert it to JSON with compact table-oriented format
    Uses RLE-enabled CompactExcelProcessor for optimal performance
    
    New Features:
    - Complexity analysis for each sheet
    - Comparison mode flag for dual processing (traditional + AI)
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
        
        # Get processing options
        enable_comparison = request.POST.get('enable_comparison', 'false').lower() == 'true'
        enable_ai_analysis = request.POST.get('enable_ai_analysis', 'false').lower() == 'true'
        
        # Always use compact format (RLE-enabled)
        format_type = 'compact'
        use_compact = True
        
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
        
        # Process the Excel file using enhanced complexity-preserving processor
        processor = ComplexityPreservingCompactProcessor(enable_rle=True)
        json_data = processor.process_file(full_path, 
                                         filter_empty_trailing=True,
                                         include_complexity_metadata=True)
        
        # Initialize complexity analyzer
        complexity_analyzer = ExcelComplexityAnalyzer()
        
        # Analyze complexity for each sheet using enhanced metadata
        complexity_results = {}
        complexity_metadata_dict = json_data.get('complexity_metadata', {}).get('sheets', {})
        
        for sheet in json_data.get('workbook', {}).get('sheets', []):
            sheet_name = sheet.get('name', 'Unknown')
            
            # Get complexity metadata for this sheet
            sheet_complexity_metadata = complexity_metadata_dict.get(sheet_name)
            
            # Analyze complexity using metadata if available
            complexity_analysis = complexity_analyzer.analyze_sheet_complexity(
                sheet, 
                complexity_metadata=sheet_complexity_metadata
            )
            complexity_results[sheet_name] = complexity_analysis
            
            # Log complexity analysis
            print(f"DEBUG: Sheet '{sheet_name}' complexity: {complexity_analysis['complexity_score']:.3f} ({complexity_analysis['complexity_level']})")
            print(f"DEBUG: Recommendation: {complexity_analysis['recommendation']}")
            print(f"DEBUG: Using metadata: {sheet_complexity_metadata is not None}")
            if complexity_analysis['failure_indicators']:
                print(f"DEBUG: Failure indicators: {complexity_analysis['failure_indicators']}")
        
        # Prepare processing options
        processing_options = {
            'enable_comparison': enable_comparison,
            'enable_ai_analysis': enable_ai_analysis,
            'complexity_results': complexity_results
        }
        
        # Transform to compact table-oriented format
        table_processor = CompactTableProcessor()
        table_data = table_processor.transform_to_compact_table_format(json_data, processing_options)
        
        # Enhanced data includes complexity analysis
        enhanced_table_data = table_data
        
        # Add complexity analysis to response
        enhanced_table_data['complexity_analysis'] = complexity_results
        
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
            summary_data = {
                'workbook': {
                    'meta': json_data.get('workbook', {}).get('meta', {}),
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
                
                sheet_summary = {
                    'name': sheet.get('name', 'Unknown'),
                    'table_count': len(tables),
                    'total_rows': sum(len(table.get('labels', {}).get('rows', [])) for table in tables),
                    'total_columns': sum(len(table.get('labels', {}).get('cols', [])) for table in tables)
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
                    'estimated_verbose_size_mb': estimated_size / 1024 / 1024 * 3.5,
                    'estimated_reduction_percent': 70,
                    'rle_enabled': True
                }
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
            
            # Add compression stats (always using compact format with RLE)
            response_data['compression_stats'] = {
                'format_used': format_type,
                'estimated_verbose_size_mb': total_size / 1024 / 1024 * 3.5,
                'actual_size_mb': total_size / 1024 / 1024,
                'estimated_reduction_percent': 70,
                'rle_enabled': True
            }
            
            # Add RLE statistics if available
            if 'rle_compression' in json_data:
                response_data['rle_stats'] = json_data['rle_compression']
            
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
    Transform Excel JSON to compact table-oriented format
    Uses RLE-enabled compact format for optimal performance
    """
    try:
        json_data = request.data.get('json_data')
        
        if not json_data:
            return Response(
                {'error': 'No JSON data provided'}, 
                status=400
            )
        
        # Always use compact format
        format_type = 'compact'
        
        # Get options from request
        options = request.data.get('options', {})
        
        # Transform to compact table-oriented format
        table_processor = CompactTableProcessor()
        table_data = table_processor.transform_to_compact_table_format(json_data, options)
        
        response_data = {
            'success': True,
            'format': format_type,
            'table_data': table_data
        }
        
        # Add compression stats (always using compact format)
        original_size = len(json.dumps(json_data))
        compressed_size = len(json.dumps(table_data))
        response_data['compression_stats'] = {
            'original_size': original_size,
            'compressed_size': compressed_size,
            'reduction_percent': int((1 - compressed_size / original_size) * 100) if original_size > 0 else 0,
            'rle_enabled': True
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
    Note: Header resolution is built into compact format (labels structure)
    """
    try:
        table_data = request.data.get('table_data')
        
        if not table_data:
            return Response(
                {'error': 'No table data provided'}, 
                status=400
            )
        
        # Always use compact format (header resolution is built-in)
        format_type = 'compact'
        
        # Compact format already has labels resolved
        return Response({
            'success': True,
            'format': format_type,
            'resolved_data': table_data,
            'message': 'Compact format already includes resolved headers in labels structure'
        }, status=200)
        
    except Exception as e:
        return Response(
            {'error': f'Error resolving headers: {str(e)}'}, 
            status=500
        )


@api_view(['POST'])
def analyze_excel_complexity(request):
    """
    Analyze Excel file complexity and get processing recommendations
    
    This endpoint performs complexity analysis on uploaded Excel files
    to determine when traditional heuristics will struggle and AI should be used.
    """
    try:
        if 'file' not in request.FILES:
            return Response(
                {'error': 'No file provided'}, 
                status=400
            )
        
        uploaded_file = request.FILES['file']
        
        # Validate file type
        allowed_extensions = ['.xlsx', '.xlsm', '.xltx', '.xltm']
        file_extension = os.path.splitext(uploaded_file.name)[1].lower()
        
        if file_extension not in allowed_extensions:
            return Response(
                {'error': f'Unsupported file format. Allowed formats: {", ".join(allowed_extensions)}'}, 
                status=400
            )
        
        # Save uploaded file temporarily
        temp_path = default_storage.save(
            f'temp/{uploaded_file.name}', 
            ContentFile(uploaded_file.read())
        )
        full_path = os.path.join(settings.MEDIA_ROOT, temp_path)
        
        try:
            # Process the Excel file
            processor = CompactExcelProcessor()
            json_data = processor.process_file(full_path)
            
            # Initialize complexity analyzer
            complexity_analyzer = ExcelComplexityAnalyzer()
            
            # Analyze complexity for each sheet
            complexity_results = {}
            overall_recommendations = {}
            
            for sheet in json_data.get('workbook', {}).get('sheets', []):
                sheet_name = sheet.get('name', 'Unknown')
                complexity_analysis = complexity_analyzer.analyze_sheet_complexity(sheet)
                complexity_results[sheet_name] = complexity_analysis
                overall_recommendations[sheet_name] = complexity_analysis['recommendation']
            
            # Determine overall file recommendation
            recommendations = list(overall_recommendations.values())
            if 'ai_first' in recommendations:
                overall_recommendation = 'ai_first'
            elif 'dual' in recommendations:
                overall_recommendation = 'dual'
            else:
                overall_recommendation = 'traditional'
            
            # Clean up temporary file
            default_storage.delete(temp_path)
            
            return Response({
                'success': True,
                'filename': uploaded_file.name,
                'overall_recommendation': overall_recommendation,
                'sheet_analysis': complexity_results,
                'summary': {
                    'total_sheets': len(complexity_results),
                    'simple_sheets': len([r for r in recommendations if r == 'traditional']),
                    'moderate_sheets': len([r for r in recommendations if r == 'dual']),
                    'complex_sheets': len([r for r in recommendations if r == 'ai_first']),
                    'average_complexity': sum(c['complexity_score'] for c in complexity_results.values()) / len(complexity_results) if complexity_results else 0
                }
            }, status=200)
            
        finally:
            # Ensure cleanup even if processing fails
            try:
                default_storage.delete(temp_path)
            except:
                pass
        
    except Exception as e:
        return Response(
            {'error': f'Error analyzing complexity: {str(e)}'}, 
            status=500
        )


@api_view(['POST']) 
def excel_comparison_analysis(request):
    """
    Perform dual processing comparison (traditional heuristics vs AI analysis)
    
    This endpoint runs both traditional table detection and AI-powered analysis
    on the same Excel file to generate comparison data for tuning and testing.
    """
    try:
        if 'file' not in request.FILES:
            return Response(
                {'error': 'No file provided'}, 
                status=400
            )
        
        uploaded_file = request.FILES['file']
        
        # Validate file type
        allowed_extensions = ['.xlsx', '.xlsm', '.xltx', '.xltm']
        file_extension = os.path.splitext(uploaded_file.name)[1].lower()
        
        if file_extension not in allowed_extensions:
            return Response(
                {'error': f'Unsupported file format. Allowed formats: {", ".join(allowed_extensions)}'}, 
                status=400
            )
        
        # Save uploaded file temporarily
        temp_path = default_storage.save(
            f'temp/{uploaded_file.name}', 
            ContentFile(uploaded_file.read())
        )
        full_path = os.path.join(settings.MEDIA_ROOT, temp_path)
        
        try:
            # Process the Excel file
            processor = CompactExcelProcessor()
            json_data = processor.process_file(full_path)
            
            # Initialize analyzers
            complexity_analyzer = ExcelComplexityAnalyzer()
            table_processor = CompactTableProcessor()
            
            # Perform analysis for each sheet
            comparison_results = {}
            
            for sheet in json_data.get('workbook', {}).get('sheets', []):
                sheet_name = sheet.get('name', 'Unknown')
                
                # 1. Complexity Analysis
                complexity_analysis = complexity_analyzer.analyze_sheet_complexity(sheet)
                
                # 2. Traditional Heuristic Processing
                traditional_options = {
                    'enable_comparison': False,
                    'enable_ai_analysis': False
                }
                traditional_result = table_processor.transform_to_compact_table_format(
                    {'workbook': {'sheets': [sheet]}}, 
                    traditional_options
                )
                
                # 3. AI Processing using Anthropic
                print(f"DEBUG: Starting AI analysis for sheet '{sheet_name}'...")
                
                # Initialize AI client and parser
                ai_client = AnthropicExcelClient()
                ai_parser = AIResultParser()
                
                if ai_client.is_available():
                    # Perform AI analysis
                    ai_raw_response = ai_client.analyze_excel_tables(
                        sheet, 
                        complexity_metadata=complexity_analysis,
                        analysis_focus="comprehensive"
                    )
                    
                    # Parse AI response
                    ai_result = ai_parser.parse_excel_analysis(ai_raw_response)
                    
                    print(f"DEBUG: AI analysis completed for '{sheet_name}'")
                    print(f"DEBUG: AI found {ai_result.get('table_count', 0)} tables")
                    print(f"DEBUG: AI confidence: {ai_result.get('ai_analysis', {}).get('confidence', 0.0):.3f}")
                    
                else:
                    print("DEBUG: AI client not available, using placeholder")
                    ai_result = {
                        'status': 'unavailable',
                        'message': 'Anthropic AI client not available (API key missing or package not installed)',
                        'ai_analysis': {
                            'tables': [],
                            'sheet_summary': {
                                'total_tables': 0,
                                'structure_complexity': 'unknown',
                                'recommended_processing': 'traditional'
                            },
                            'confidence': 0.0,
                            'processing_notes': ['AI analysis unavailable']
                        },
                        'table_count': 0,
                        'high_confidence_tables': 0,
                        'complexity_assessment': {
                            'level': 'unknown',
                            'score': 0.0,
                            'factors': ['ai_unavailable']
                        },
                        'processing_recommendation': 'traditional',
                        'validation': {
                            'errors': ['AI service unavailable'],
                            'warnings': [],
                            'valid': False
                        },
                        'converted_tables': []
                    }
                
                # 4. Comprehensive Comparison Analysis
                print(f"DEBUG: Starting comparison analysis for '{sheet_name}'...")
                
                # Initialize comparison engine
                comparison_engine = ComparisonEngine()
                
                # Perform comprehensive comparison
                comparison_data = comparison_engine.compare_analysis_results(
                    traditional_result=traditional_result,
                    ai_result=ai_result,
                    complexity_metadata=complexity_analysis,
                    sheet_name=sheet_name
                )
                
                print(f"DEBUG: Comparison completed for '{sheet_name}'")
                print(f"DEBUG: Winner: {comparison_data['summary']['winner']}")
                print(f"DEBUG: Agreement score: {comparison_data['metrics']['agreement_score']:.3f}")
                
                comparison_results[sheet_name] = comparison_data
            
            # Clean up temporary file
            default_storage.delete(temp_path)
            
            return Response({
                'success': True,
                'filename': uploaded_file.name,
                'comparison_results': comparison_results,
                'summary': {
                    'total_sheets_analyzed': len(comparison_results),
                    'ai_implementation_status': 'placeholder',
                    'analysis_timestamp': complexity_analyzer._get_timestamp()
                }
            }, status=200)
            
        finally:
            # Ensure cleanup even if processing fails
            try:
                default_storage.delete(temp_path)
            except:
                pass
        
    except Exception as e:
        return Response(
            {'error': f'Error performing comparison analysis: {str(e)}'}, 
            status=500
        )
