#!/bin/bash
# REFILL 서버 시작 스크립트

# 1. 벡터 DB 빌드 (없을 때만)
if [ ! -d "rag/chroma_db" ] || [ ! -f "rag/chroma_db/chroma.sqlite3" ]; then
    echo "[1/2] Building vector DB..."
    cd rag && python build_vectordb.py && cd ..
    echo "[1/2] Vector DB ready"
else
    echo "[1/2] Vector DB already exists, skipping build"
fi

# 2. FastAPI 서버 시작
echo "[2/2] Starting FastAPI server..."
cd chatbot && uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}
