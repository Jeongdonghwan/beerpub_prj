import os

from app import create_app

app = create_app()

if __name__ == "__main__":
    # 포트 충돌 시 .env 의 PORT 만 바꾸면 됨
    app.run(debug=True, port=int(os.environ.get("PORT", 8010)))
