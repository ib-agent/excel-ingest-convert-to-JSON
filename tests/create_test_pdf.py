#!/usr/bin/env python3
"""
Create a simple test PDF file for testing PDF processing functionality
"""

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors

def create_test_pdf():
    """Create a test PDF with tables and text"""
    
    # Create PDF
    c = canvas.Canvas("test_sample.pdf", pagesize=letter)
    width, height = letter
    
    # Add title
    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, height - 100, "Sample PDF Document")
    
    # Add subtitle
    c.setFont("Helvetica", 12)
    c.drawString(100, height - 130, "This is a test document for PDF processing")
    
    # Add some text content
    c.setFont("Helvetica", 10)
    text_content = [
        "This document contains various types of content including:",
        "",
        "1. Regular text paragraphs",
        "2. A simple table with data",
        "3. Numbers and percentages",
        "4. Different formatting styles",
        "",
        "The total revenue for Q4 2023 was $1,500,000, representing a 25.5% increase",
        "over the previous quarter. Our team of 150 employees worked on 45 different",
        "projects throughout the year, achieving 95% customer satisfaction."
    ]
    
    y_position = height - 180
    for line in text_content:
        c.drawString(100, y_position, line)
        y_position -= 15
    
    # Draw a simple table
    c.setFont("Helvetica-Bold", 12)
    c.drawString(100, y_position - 30, "Sample Data Table:")
    
    # Table data
    data = [
        ["Product", "Q1", "Q2", "Q3", "Q4", "Total"],
        ["Widget A", "100", "150", "200", "250", "700"],
        ["Widget B", "75", "125", "175", "225", "600"],
        ["Widget C", "50", "100", "150", "200", "500"]
    ]
    
    # Table dimensions
    start_x, start_y = 100, y_position - 60
    cell_width, cell_height = 80, 25
    
    # Draw table
    for i, row in enumerate(data):
        for j, cell in enumerate(row):
            x = start_x + j * cell_width
            y = start_y - i * cell_height
            
            # Draw cell border
            c.rect(x, y, cell_width, cell_height)
            
            # Add text
            if i == 0:  # Header row
                c.setFont("Helvetica-Bold", 10)
            else:
                c.setFont("Helvetica", 10)
            
            c.drawString(x + 5, y + 8, str(cell))
    
    # Add more text with numbers
    c.setFont("Helvetica", 10)
    more_text = [
        "",
        "Financial Summary:",
        "• Revenue: $2,500,000",
        "• Expenses: $1,800,000",
        "• Profit: $700,000",
        "• Growth Rate: 15.3%",
        "",
        "Key Metrics:",
        "• Customer Count: 1,250",
        "• Average Order: $85.50",
        "• Conversion Rate: 3.2%",
        "• Retention Rate: 87.5%"
    ]
    
    y_position = start_y - len(data) * cell_height - 30
    for line in more_text:
        c.drawString(100, y_position, line)
        y_position -= 15
    
    c.save()
    print("✓ Test PDF created: test_sample.pdf")

if __name__ == "__main__":
    create_test_pdf() 