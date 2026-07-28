# gunicorn 설정 — Cafe24 가상서버 (Linux) 배포용
# 실행: gunicorn -c deploy/gunicorn.conf.py "app:create_app()"
bind = "unix:/tmp/beerpub.sock"   # nginx proxy_pass 대상. TCP 사용 시 "127.0.0.1:8000"
workers = 2
worker_class = "sync"
timeout = 60
accesslog = "-"
errorlog = "-"
