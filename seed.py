"""DB 생성 + 12테이블 + 더미 시드 데이터 삽입 (멱등 — 데이터가 있으면 건너뜀).

사용법: python seed.py
"""
import os
from urllib.parse import urlparse

import pymysql
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

load_dotenv()


def ensure_database():
    """mysql CLI 없이 PyMySQL raw 연결로 beerpub DB 생성."""
    url = urlparse(os.environ.get(
        "DATABASE_URL", "mysql+pymysql://root:1234@127.0.0.1:3306/beerpub"
    ).replace("mysql+pymysql", "mysql"))
    dbname = url.path.lstrip("/").split("?")[0]
    conn = pymysql.connect(
        host=url.hostname or "127.0.0.1", port=url.port or 3306,
        user=url.username or "root", password=url.password or "",
    )
    with conn.cursor() as cur:
        cur.execute(
            f"CREATE DATABASE IF NOT EXISTS `{dbname}` "
            "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        )
    conn.close()
    print(f"[1/3] 데이터베이스 확인: {dbname}")


CATEGORIES = ["신메뉴", "시그니처", "튀김", "분식/피자", "탕/볶음", "마른안주", "사이드", "주류"]

# (카테고리, 이름, 가격, 뱃지, 설명) — 더미. image 는 전부 빈 값 → 플레이스홀더 박스 렌더
MENUS = [
    ("튀김",    "고추바사삭 치킨",     15900, "best",      "청양 고추 간장 소스의 바삭한 치킨"),
    ("분식/피자", "새우폭탄 로제파스타", 14500, "",          "탱글한 새우가 가득한 로제 파스타"),
    ("신메뉴",   "롱롱치즈 돈까스",     13900, "new",       "길게 늘어나는 치즈 돈까스"),
    ("튀김",    "페스츄리 오징어",     12900, "",          "겹겹이 바삭한 페스츄리 오징어 튀김"),
    ("사이드",   "킬바사 콘치즈",       9900,  "",          "킬바사 소시지를 올린 콘치즈"),
    ("주류",    "살얼음 맥주",         4900,  "signature", "살얼음이 서리는 시그니처 생맥주"),
    ("주류",    "레몬 살얼음 하이볼",   6900,  "",          "상큼한 레몬 살얼음 하이볼"),
    ("주류",    "자몽 살얼음 하이볼",   6900,  "",          "쌉싸름한 자몽 살얼음 하이볼"),
    ("주류",    "오션 살얼음 하이볼",   7900,  "new",       "청량한 블루 오션 살얼음 하이볼"),
    ("주류",    "유자 살얼음 하이볼",   6900,  "",          "달콤한 유자 살얼음 하이볼"),
]

INTERIORS = [
    "바 카운터", "홀 전경", "외부 파사드", "룸 좌석", "네온 사인", "테라스",
    "오픈 주방", "야간 전경", "입구", "포토존", "단체석", "창가 좌석",
]

STORIES = [
    ("OO 1호점", "장사 초보였던 제가 6개월 만에 단골 가게 사장이 됐습니다"),
    ("OO역점",   "18년 장사 끝에 고른 브랜드, 지금이 제일 마음 편합니다"),
    ("OO점",     "손님은 맛으로, 점주는 시스템으로 만족!"),
    ("OO점",     "퇴근길 손님이 줄 서는 가게, 저도 신기합니다"),
]

STORES = [
    ("OO 1호점", "서울", "서울특별시 OO구 OO로 123 [확인필요]", "02-000-0000"),
    ("OO역점",   "경기", "경기도 OO시 OO대로 45 [확인필요]",   "031-000-0000"),
    ("OO점",     "부산", "부산광역시 OO구 OO길 67 [확인필요]", "051-000-0000"),
]

HISTORIES = [
    (2021, 3,  "브랜드 론칭 [확인필요]"),
    (2021, 11, "직영 1호점 오픈 [확인필요]"),
    (2022, 6,  "가맹 1호점 오픈 [확인필요]"),
    (2023, 9,  "가맹 10호점 돌파 [확인필요]"),
    (2025, 1,  "시그니처 살얼음 주류 라인업 출시 [확인필요]"),
]

BANNERS = [("언론보도", ""), ("제휴사", ""), ("수상이력", "")]

NOTICES = [
    ("창업설명회 안내 [더미]", "매월 정기 창업설명회를 진행합니다. 자세한 일정은 가맹문의로 확인해 주세요."),
    ("홈페이지 오픈 안내 [더미]", "맥주엔딹 가맹모집 홈페이지가 오픈했습니다."),
]

DOC_DUMMY = (
    "본 문서는 더미 약관입니다. [확인필요] 법무 검토를 거친 최종본으로 교체하세요.\n\n"
    "제1조 (목적)\n이 약관은 서비스 이용에 관한 기본적인 사항을 규정합니다.\n\n"
    "제2조 (정의)\n이 약관에서 사용하는 용어의 정의는 관계 법령에 따릅니다."
)


def seed():
    from app import create_app
    from app.extensions import db
    from app.models import (
        AdminUser, Banner, History, Interior, Menu, MenuCategory, Notice,
        SiteConfig, Story, Store,
    )

    app = create_app()
    with app.app_context():
        db.create_all()
        print("[2/3] 테이블 생성 완료 (12테이블)")

        inserted = []

        if MenuCategory.query.count() == 0:
            for i, name in enumerate(CATEGORIES):
                db.session.add(MenuCategory(name=name, sort=i))
            db.session.flush()
            inserted.append(f"카테고리 {len(CATEGORIES)}")

        if Menu.query.count() == 0:
            cat_map = {c.name: c.id for c in MenuCategory.query.all()}
            for i, (cat, name, price, badge, desc) in enumerate(MENUS):
                db.session.add(Menu(
                    category_id=cat_map[cat], name=name, price=price,
                    badge=badge, description=desc, image="", sort=i,
                ))
            inserted.append(f"메뉴 {len(MENUS)}")

        if Interior.query.count() == 0:
            for i, title in enumerate(INTERIORS):
                db.session.add(Interior(title=f"OO점 · {title}", image="", thumb="", sort=i))
            inserted.append(f"인테리어 {len(INTERIORS)}")

        if Story.query.count() == 0:
            for i, (branch, summary) in enumerate(STORIES):
                db.session.add(Story(
                    branch_name=branch, title=summary, summary=summary,
                    content=summary + "\n\n[확인필요] 실제 점주 인터뷰 전문으로 교체하세요.",
                    sort=i,
                ))
            inserted.append(f"스토리 {len(STORIES)}")

        if Store.query.count() == 0:
            for name, region, addr, phone in STORES:
                db.session.add(Store(name=name, region=region, address=addr, phone=phone))
            inserted.append(f"매장 {len(STORES)}")

        if History.query.count() == 0:
            for i, (year, month, content) in enumerate(HISTORIES):
                db.session.add(History(year=year, month=month, content=content, sort=i))
            inserted.append(f"연혁 {len(HISTORIES)}")

        if Banner.query.count() == 0:
            for i, (title, link) in enumerate(BANNERS):
                db.session.add(Banner(title=f"{title} [더미]", image="", link=link, sort=i))
            inserted.append(f"배너 {len(BANNERS)}")

        if Notice.query.count() == 0:
            for title, content in NOTICES:
                db.session.add(Notice(title=title, content=content))
            inserted.append(f"공지 {len(NOTICES)}")

        if AdminUser.query.count() == 0:
            db.session.add(AdminUser(
                username=app.config["ADMIN_USER"],
                password_hash=generate_password_hash(app.config["ADMIN_PASS"]),
            ))
            inserted.append("관리자 계정 1")

        if SiteConfig.query.count() == 0:
            from config.brand import BRAND
            defaults = {
                "meta_title": BRAND["meta"]["title"],
                "meta_description": BRAND["meta"]["description"],
                "naver_verification": "",
                "s2_bg_image": "",
                "doc_policy": DOC_DUMMY,
                "doc_private": DOC_DUMMY,
                "doc_antiemail": DOC_DUMMY,
            }
            for k, v in defaults.items():
                db.session.add(SiteConfig(cfg_key=k, cfg_value=v))
            inserted.append(f"site_config {len(defaults)}")

        db.session.commit()
        if inserted:
            print("[3/3] 시드 삽입:", ", ".join(inserted))
        else:
            print("[3/3] 기존 데이터 존재 — 시드 건너뜀 (멱등)")


if __name__ == "__main__":
    ensure_database()
    seed()
