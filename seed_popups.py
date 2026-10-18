"""레이어 팝업 초기 등록 (멱등) — 이미지는 static/images/popup/ 에 git 으로 포함.
이후 수정·교체·추가는 어드민 > 레이어 팝업에서 직접 하면 된다.
사용법: python seed_popups.py
"""
from app import create_app
from app.extensions import db
from app.models import Popup

POPUPS = [
    {"title": "창업비용 이벤트 (가맹비 500→0 · 교육비 500→300)",
     "image": "/static/images/popup/event_fee.png", "link": "/startup/cost"},
    {"title": "오픈 예정 지점",
     "image": "/static/images/popup/open_soon.png", "link": "/inquiry/"},
]

app = create_app()
with app.app_context():
    n_new = n_upd = 0
    for i, p in enumerate(POPUPS):
        row = Popup.query.filter_by(image=p["image"]).first()
        if row is None:
            row = Popup(**p)
            db.session.add(row)
            n_new += 1
        else:
            row.title, row.link = p["title"], p["link"]
            n_upd += 1
        row.is_active = True
    db.session.commit()
    print(f"팝업 신규 {n_new} / 갱신 {n_upd} — 활성 팝업 {Popup.query.filter_by(is_active=True).count()}개")
