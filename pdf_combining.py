#! python3
# pdf_combining.py - Combines all the PDFs in the current working directory into a single PDF,
#                    excluding the first pages.

import PyPDF2
import os

# Get all the PDF filenames in a list.
pdf_files = []
for filename in os.listdir('.'):  # alternatively 'os.scandir'
    if filename.endswith('.pdf'):
        pdf_files.append(filename)

pdf_files.sort(key=str.lower)

pdf_writer = PyPDF2.PdfFileWriter()

# Loop through all the PDF files.
for filename in pdf_files:
    pdf_file_obj = open(filename, 'rb')  # For each PDF, the loop opens a filename in read-binary mode.
    pdf_reader = PyPDF2.PdfFileReader(pdf_file_obj)  # Create a PdfFileReader object for that PDF file.

    # Loop through all the pages (except the first) and add them page by page to the PDF writer object (pdf_writer).
    # Range - From the second page go up to, but not include, the integer in pdfReader.numPages.
    for page_num in range(1, pdf_reader.numPages):
        page_obj = pdf_reader.getPage(page_num)
        pdf_writer.addPage(page_obj)

# Save the resulting PDF to a file.
pdf_output = open('allminutes.pdf', 'wb')
pdf_writer.write(pdf_output)
pdf_output.close()
