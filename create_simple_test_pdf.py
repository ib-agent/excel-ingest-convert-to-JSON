#!/usr/bin/env python3
"""
Create a simple test PDF file using a different approach
"""

import subprocess
import tempfile
import os

def create_test_pdf():
    """Create a test PDF using a simple HTML to PDF conversion"""
    
    # Create HTML content
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test PDF Document</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            table { border-collapse: collapse; width: 100%; margin: 20px 0; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #f2f2f2; }
            .section { margin: 20px 0; }
        </style>
    </head>
    <body>
        <h1>Sample PDF Document</h1>
        <p>This is a test document for PDF processing functionality.</p>
        
        <div class="section">
            <h2>Financial Summary</h2>
            <p>The total revenue for Q4 2023 was $1,500,000, representing a 25.5% increase over the previous quarter. Our team of 150 employees worked on 45 different projects throughout the year, achieving 95% customer satisfaction.</p>
        </div>
        
        <div class="section">
            <h2>Sample Data Table</h2>
            <table>
                <tr>
                    <th>Product</th>
                    <th>Q1</th>
                    <th>Q2</th>
                    <th>Q3</th>
                    <th>Q4</th>
                    <th>Total</th>
                </tr>
                <tr>
                    <td>Widget A</td>
                    <td>100</td>
                    <td>150</td>
                    <td>200</td>
                    <td>250</td>
                    <td>700</td>
                </tr>
                <tr>
                    <td>Widget B</td>
                    <td>75</td>
                    <td>125</td>
                    <td>175</td>
                    <td>225</td>
                    <td>600</td>
                </tr>
                <tr>
                    <td>Widget C</td>
                    <td>50</td>
                    <td>100</td>
                    <td>150</td>
                    <td>200</td>
                    <td>500</td>
                </tr>
            </table>
        </div>
        
        <div class="section">
            <h2>Key Metrics</h2>
            <ul>
                <li>Revenue: $2,500,000</li>
                <li>Expenses: $1,800,000</li>
                <li>Profit: $700,000</li>
                <li>Growth Rate: 15.3%</li>
                <li>Customer Count: 1,250</li>
                <li>Average Order: $85.50</li>
                <li>Conversion Rate: 3.2%</li>
                <li>Retention Rate: 87.5%</li>
            </ul>
        </div>
        
        <div class="section">
            <h2>Additional Information</h2>
            <p>This document contains various types of content including regular text paragraphs, a simple table with data, numbers and percentages, and different formatting styles. The processing system should be able to extract tables, identify numbers in text, and organize text content into logical sections.</p>
        </div>
    </body>
    </html>
    """
    
    # Write HTML to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
        f.write(html_content)
        html_file = f.name
    
    try:
        # Try to convert HTML to PDF using wkhtmltopdf if available
        pdf_file = "test_sample.pdf"
        
        # Check if wkhtmltopdf is available
        try:
            subprocess.run(['wkhtmltopdf', '--version'], capture_output=True, check=True)
            # Convert HTML to PDF
            subprocess.run(['wkhtmltopdf', html_file, pdf_file], check=True)
            print(f"✓ Test PDF created: {pdf_file}")
            return pdf_file
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("⚠ wkhtmltopdf not available. Creating HTML file instead.")
            # If wkhtmltopdf is not available, just create the HTML file
            html_output = "test_sample.html"
            with open(html_output, 'w') as f:
                f.write(html_content)
            print(f"✓ Test HTML created: {html_output}")
            print("You can convert this to PDF using your browser's print function or an online converter.")
            return html_output
            
    finally:
        # Clean up temporary HTML file
        try:
            os.unlink(html_file)
        except:
            pass

if __name__ == "__main__":
    create_test_pdf() 