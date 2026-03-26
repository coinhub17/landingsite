from flask import Flask, request, send_file, jsonify
from fpdf import FPDF
import datetime, io, uuid, hashlib

app = Flask(__name__)

# ---------- IN-MEMORY STORAGE ----------
cert_store = {}

# ---------- PDF HELPER ----------
def add_field(pdf, label, value):
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, label, ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 8, value)
    pdf.ln(3)

# ---------- GENERATE CERTIFICATE ----------
@app.route("/generate", methods=["POST"])
def generate():
    data = request.json or {}

    ip = data.get("ip", "N/A")
    file_hash = data.get("fileHash", "")
    text_hash = data.get("textHash", "")

    # Validation
    if not file_hash and not text_hash:
        return jsonify({"error": "At least one hash required"}), 400

    certificate_id = str(uuid.uuid4())
    timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

    # Signature
    signature = hashlib.sha256(
        (file_hash + text_hash + timestamp).encode()
    ).hexdigest()

    # Store in memory
    cert_store[certificate_id] = {
        "id": certificate_id,
        "timestamp": timestamp,
        "file_hash": file_hash,
        "text_hash": text_hash,
        "ip": ip,
        "signature": signature
    }

    # Create PDF
    pdf = FPDF()
    pdf.add_page()

    try:
        pdf.image("logo.png", 160, 10, 40)
    except:
        pass

    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 15, "Kerio Valley IP Protection Certificate", ln=True, align="C")
    pdf.ln(10)

    add_field(pdf, "Certificate ID:", certificate_id)
    add_field(pdf, "Timestamp (UTC):", timestamp)
    add_field(pdf, "Public IP:", ip)
    add_field(pdf, "File SHA256:", file_hash or "N/A")
    add_field(pdf, "Text SHA256:", text_hash or "N/A")
    add_field(pdf, "Signature:", signature)

    pdf.ln(5)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 8,
        "Verification Instructions:\n"
        "- Re-hash the original file and compare with File SHA256 above.\n"
        "- Re-hash the original text and compare with Text SHA256 above.\n"
        "- Verify certificate ID via API endpoint.\n"
        "If hashes match, authenticity is verified.\n"
        "This certificate is timestamp-bound."
    )

    # FIXED BUFFER OUTPUT
    pdf_bytes = pdf.output(dest='S').encode('latin1')
    buffer = io.BytesIO(pdf_bytes)

    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"IP_Certificate_{certificate_id}.pdf",
        mimetype='application/pdf'
    )

# ---------- VERIFY CERTIFICATE ----------
@app.route("/verify/<cert_id>", methods=["GET"])
def verify(cert_id):
    cert = cert_store.get(cert_id)

    if cert:
        return jsonify({
            "status": "valid",
            "certificate": cert
        })
    else:
        return jsonify({"status": "not found"}), 404

# ---------- DEBUG: VIEW ALL CERTS ----------
@app.route("/debug/certs", methods=["GET"])
def all_certs():
    return jsonify(cert_store)

# ---------- RUN ----------
if __name__ == "__main__":
    app.run(debug=True)
