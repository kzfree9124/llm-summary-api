import io
import pytest
from docx import Document
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject
from app.services.file_parser import parse_file
from fastapi import HTTPException, UploadFile
from starlette.datastructures import Headers

# region 共通処理
def create_upload_file(content: str, filename="test.txt", content_type="text/plain"):
    return UploadFile(
        filename=filename,
        file=io.BytesIO(content.encode("utf-8")),
        headers=Headers({"content-type": content_type}),
    )

def create_upload_file_bytes(content: bytes, filename: str, content_type: str):
    return UploadFile(
        filename=filename,
        file=io.BytesIO(content),
        headers=Headers({"content-type": content_type}),
    )
# endregion

# region 正常系

# テキスト抽出処理テスト(テキストファイル)
def test_parse_txt():
    file = create_upload_file("これはテストです")
    
    result = parse_file(file)
    
    assert result == "これはテストです"

# PDFファイルテスト
def test_parse_pdf():
    writer = PdfWriter()
    page = writer.add_blank_page(width=300, height=300)

    font = DictionaryObject()
    font.update({
        NameObject("/Type"): NameObject("/Font"),
        NameObject("/Subtype"): NameObject("/Type1"),
        NameObject("/BaseFont"): NameObject("/Helvetica"),
    })
    fonts = DictionaryObject({NameObject("/F1"): writer._add_object(font)})
    page[NameObject("/Resources")] = DictionaryObject({NameObject("/Font"): fonts})

    content = DecodedStreamObject()
    content.set_data(b"BT /F1 12 Tf 72 200 Td (PDF text) Tj ET")
    page[NameObject("/Contents")] = writer._add_object(content)

    pdf_data = io.BytesIO()
    writer.write(pdf_data)
    pdf_data.seek(0)
    file = UploadFile(
        filename="test.pdf",
        file=pdf_data,
        headers=Headers({"content-type": "application/pdf"}),
    )

    result = parse_file(file)

    assert result.strip() == "PDF text"
    
def test_parse_docx():
    document = Document()
    document.add_paragraph("DOCXのテキストです")
    docx_data = io.BytesIO()
    document.save(docx_data)
    docx_data.seek(0)
    file = UploadFile(
        filename="test.docx",
        file=docx_data,
        headers=Headers({
            "content-type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        }),
    )

    result = parse_file(file)

    assert result == "DOCXのテキストです"

# endregion

# region 異常系

# ファイル種別エラー
def test_parse_unsupported_file():
    file = create_upload_file("dummy", filename="image.png", content_type="image/png")
    
    with pytest.raises(HTTPException) as exc:
        parse_file(file)
    
    assert exc.value.status_code == 400
    assert exc.value.detail == "Unsupported file type."

# ファイルサイズ超過
def test_parse_large_file():
    large_content = "a" * (10 * 1024 * 1024)
    file = create_upload_file(large_content)
    
    with pytest.raises(HTTPException) as exc:
        parse_file(file)
        
    assert exc.value.status_code == 413
    assert exc.value.detail == "File size exceeds limit (5MB)."

# PDF解析に失敗した場合
def test_parse_invalid_pdf():
    file = create_upload_file_bytes(
        b"not a PDF",
        filename="broken.pdf",
        content_type="application/pdf",
    )

    with pytest.raises(HTTPException) as exc:
        parse_file(file)

    assert exc.value.status_code == 400
    assert exc.value.detail == "Failed to parse PDF file."

# PDFからテキストを抽出できない場合
def test_parse_pdf_without_text():
    writer = PdfWriter()
    writer.add_blank_page(width=300, height=300)
    pdf_data = io.BytesIO()
    writer.write(pdf_data)
    pdf_data.seek(0)
    file = UploadFile(
        filename="empty.pdf",
        file=pdf_data,
        headers=Headers({"content-type": "application/pdf"}),
    )

    with pytest.raises(HTTPException) as exc:
        parse_file(file)

    assert exc.value.status_code == 400
    assert exc.value.detail == "Failed to parse PDF file."

# DOCXの解析に失敗した場合
def test_parse_invalid_docx():
    file = create_upload_file_bytes(
        b"not a DOCX",
        filename="broken.docx",
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )

    with pytest.raises(HTTPException) as exc:
        parse_file(file)

    assert exc.value.status_code == 400
    assert exc.value.detail == "Failed to parse DOCX file."

# UTF-8で読めないTXTはShift-JISで読み込む
def test_parse_txt_with_shift_jis_encoding():
    file = create_upload_file_bytes(
        "日本語のテキスト".encode("shift-jis"),
        filename="test.txt",
        content_type="text/plain",
    )

    assert parse_file(file) == "日本語のテキスト"

# TXTの読み込みに失敗した場合
def test_parse_txt_read_error():
    class FailingReadFile(io.BytesIO):
        def read(self, *args, **kwargs):
            raise OSError("read failed")

    file = UploadFile(
        filename="unreadable.txt",
        file=FailingReadFile(b"content"),
        headers=Headers({"content-type": "text/plain"}),
    )

    with pytest.raises(HTTPException) as exc:
        parse_file(file)

    assert exc.value.status_code == 400
    assert exc.value.detail == "Failed to parse TXT file."

# endregion