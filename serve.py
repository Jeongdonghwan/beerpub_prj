"""초안 공유용 미리보기 서버 (Windows) — waitress, 같은 네트워크에서 접속 가능.

사용법: python serve.py   (포트는 .env 의 PORT, 기본 8020)
운영 배포(Cafe24 Linux)는 deploy/README.md 의 gunicorn 절차 사용.
"""
import os

from waitress import serve

from app import create_app

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8020))
    print(f"* 미리보기 서버: http://0.0.0.0:{port} (같은 네트워크: http://<이 PC IP>:{port})")
    serve(app, host="0.0.0.0", port=port, threads=6)
