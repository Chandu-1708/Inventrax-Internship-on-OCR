from flask import Flask, request, render_template, redirect, url_for
import os
from werkzeug.utils import secure_filename
import pytesseract
import re
import pandas as pd
from img2table.ocr import TesseractOCR
from img2table.document import Image
from flask import Response

tesseract_path = r"C:\Program Files\Tesseract-OCR"
os.environ["PATH"] += os.pathsep + tesseract_path
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

app = Flask(__name__, template_folder='templates')
app.config["IMAGE_UPLOADS"] = "D:/internship"

@app.route('/home', methods=["GET", "POST"])

def upload_image():
    if request.method == "POST":
        image = request.files['file']

        if image.filename == '':
            print("Image must have a file name")
            return redirect(request.url)

        filename = secure_filename(image.filename)

        basedir = os.path.abspath(os.path.dirname(__file__))
        image.save(os.path.join(basedir, app.config["IMAGE_UPLOADS"], filename))

        # Perform text extraction from the image
        image_path = os.path.join(basedir, app.config["IMAGE_UPLOADS"], filename)
        text = image_to_string(image_path)

        # Perform text extraction from the cropped image
        doc = Image(image_path)
        ocr = TesseractOCR(n_threads=1, lang="eng")

        # Table extraction
        extracted_tables_all = doc.extract_tables(
            ocr=ocr,
            implicit_rows=True,
            borderless_tables=True,
            min_confidence=50
        )
        extracted_tables = extracted_tables_all[0]
        frames = []
        for table in extracted_tables_all:
            try:
                frames.append(table.df)
            except:
                frames.append(table)

        df = pd.DataFrame(frames[0]).reset_index(drop=True)
        df.reset_index(drop=True, inplace=True)
        pattern = r'\b\d\b\s'

        # Replace the unwanted single-digit numbers with an empty string
        text = re.sub(pattern, '', text)

        
        text=text.strip().replace(':','').replace('No','').replace('Number','').replace('+','').replace('#','')
        words = text.split()
        # Find the index of the word 'GSTIN'
        
        invoice_index = words.index('Invoice')
        date_index = words.index('Date')
        # Extract the GSTIN value which is the word next to 'GSTIN'
        
        invoice_no = words[invoice_index+1]
        invoice_date = words[date_index+1]

        df['Invoice No'] = invoice_no
        df['Invoice Date'] = invoice_date
        df.loc[0:1,['Invoice No']] = 'Invoice No'
        df.loc[0:1,['Invoice Date']] = 'Invoice Date'


        return render_template('index1.html', df=df)

    return render_template('index1.html', df=None)  # Pass df as None when rendering template

@app.route('/download_json', methods=["POST"])
def download_json():
    if request.method == "POST":
        data = request.form.get('data')  # Get the JSON data from the form

        # Check if the "download" checkbox is selected
        download_requested = request.form.get('download')

        if download_requested:
            # Set up the response to download the JSON file
            response = Response(data, content_type='application/json')
            response.headers["Content-Disposition"] = "attachment; filename=data.json"

            return response
        else:
            # If the checkbox is not selected, simply return a message.
            return "JSON download not requested. The data is available on the page."

    # In case the request method is not POST, handle the error by returning a proper response.
    return "Invalid request method for downloading JSON", 400

@app.route('/display/<filename>')
def display_image(filename):
    return redirect(url_for('static', filename="Images/" + filename), code=301)

def image_to_string(image_path):
    # Use pytesseract to extract text from the image
    text = pytesseract.image_to_string(image_path)
    return text

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=2004)
