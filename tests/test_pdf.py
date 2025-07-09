import os
from app import create_pdf

def test_create_pdf():
    # Przykładowy obrazek (czarno-biały, publiczny)
    url = "https://upload.wikimedia.org/wikipedia/commons/thumb/4/47/PNG_transparency_demonstration_1.png/1024px-PNG_transparency_demonstration_1.png"
    pdf_bytes, error = create_pdf(url)
    assert pdf_bytes is not None, f"Błąd PDF: {error}"
    assert pdf_bytes[:4] == b'%PDF', "Plik nie jest PDF-em"
    # Zapisz tymczasowo i usuń
    with open("test_output.pdf", "wb") as f:
        f.write(pdf_bytes)
    assert os.path.exists("test_output.pdf")
    os.remove("test_output.pdf")
