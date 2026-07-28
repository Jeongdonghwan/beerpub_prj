# 배포 가이드 (Cafe24 가상서버)

## 1. 준비
```bash
git clone <repo> && cd beerpub_prj
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # DATABASE_URL(Cafe24 MariaDB), SECRET_KEY, ADMIN_* 교체
python seed.py         # DB 생성 + 테이블 + 시드
```

## 2. 실행
```bash
gunicorn -c deploy/gunicorn.conf.py "app:create_app()"
```
systemd 서비스로 등록해 부팅 시 자동 시작 권장.

## 3. nginx
`deploy/nginx.conf` 를 `/etc/nginx/conf.d/beerpub.conf` 로 복사 후
`server_name` / static alias 경로 수정 → `nginx -t && systemctl reload nginx`.

## 4. 운영 전환 체크리스트
- `.env` 의 SECRET_KEY 를 강한 값으로 교체
- ADMIN_PASS 교체 후 `python seed.py` 는 재실행해도 기존 계정 유지 (변경은 admin_user 테이블에서)
- `config/brand.py` 의 `[확인필요]` 값 교체 (브랜드 확정값)
- 관리자 → 사이트 설정에서 네이버 verification 코드 입력
- `app/utils/notify.py` 의 ConsoleNotifier 를 SMTP/알림톡 구현체로 교체
