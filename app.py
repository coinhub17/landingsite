from flask import Flask, request, send_file
from fpdf import FPDF
import datetime, io, uuid

app = Flask(__name__)

def add_field(pdf,label,value):
    pdf.set_font("Helvetica","B",12)
    pdf.cell(0,8,label,ln=True)
    pdf.set_font("Helvetica","",10)
    pdf.multi_cell(0,8,value)
    pdf.ln(3)

@app.route("/generate", methods=["POST"])
def generate():
    data=request.json

    certificate_id=str(uuid.uuid4())
    timestamp=datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

    pdf=FPDF()
    pdf.add_page()

    # LOGO
    pdf.image("logo.png",160,10,40)

    pdf.set_font("Helvetica","B",18)
    pdf.cell(0,15,"IP Timestamp Proof Certificate",ln=True,align="C")
    pdf.ln(10)

    add_field(pdf,"Certificate ID:",certificate_id)
    add_field(pdf,"Timestamp (UTC):",timestamp)
    add_field(pdf,"Public IP:",data["ip"])
    add_field(pdf,"File SHA256:",data["fileHash"])
    add_field(pdf,"Text SHA256:",data["textHash"])

    pdf.ln(5)
    pdf.set_font("Helvetica","",10)
    pdf.multi_cell(0,8,
        "Verification Instructions:\n"
        "- Re-hash the original file and compare with File SHA256 above.\n"
        "- Re-hash the original text and compare with Text SHA256 above.\n"
        "If hashes match, authenticity is verified.\n"
        "Hashes are timestamp-bound in this certificate."
    )

    buffer=io.BytesIO()
    pdf.output(buffer)
    buffer.seek(0)

    return send_file(buffer,as_attachment=True,download_name="IP_Certificate.pdf")

if __name__=="__main__":
    app.run()
