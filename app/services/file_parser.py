# PDF/TXT/DOCX → テキスト化

import io
from fastapi import UploadFile, HTTPException
from pypdf import PdfReader
from docx import Document

MAX_FILE_SIZE = 5 * 1024 * 1024     # 5MB

# ファイルサイズチェック
def validate_file_size(file: UploadFile):
    file.file.seek(0, 2)
    size = file.file.tell()
    file.file.seek(0)
    
    if size > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File size exceeds limit (5MB).")

# 文章抽出(PDFファイル)
def extract_text_from_pdf(file: UploadFile) -> str:
    try:
        reader = PdfReader(file.file)
        text = ""
        
        for page in reader.pages:
            text += page.extract_text() or ""
            
        if not text.strip():
            raise ValueError("PDF text extraction failed.")
        
        return text
    
    except Exception:
        raise HTTPException(status_code=400, detail="Failed to parse PDF file.")

# 文章抽出(wordファイル)
def extract_text_from_docx(file: UploadFile) -> str:
    try:
        doc = Document(io.BytesIO(file.file.read()))
        text = "\n".join([p.text for p in doc.paragraphs])
        return text
    except Exception:
        raise HTTPException(status_code=400, detail="Failed to parse DOCX file.")
    
# 文章抽出(テキストファイル)
def extract_text_from_txt(file: UploadFile) -> str:
    try:
        content = file.file.read()
        try:
            return content.decode("utf-8")
        except UnicodeDecodeError:
            return content.decode("shift-jis", errors="ignore")
    except Exception:
        raise HTTPException(status_code=400, detail="Failed to parse TXT file.")

# ファイル種別に応じて文章抽出
def parse_file(file: UploadFile) -> str:
    validate_file_size(file)
    
    content_type = file.content_type

    if content_type == "application/pdf":
        return extract_text_from_pdf(file)
    elif content_type == "text/plain":
        return extract_text_from_txt(file)
    elif content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return extract_text_from_docx(file)
    else:
        raise HTTPException(status_code=400, detail="Unsupported file type.")