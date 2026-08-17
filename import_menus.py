"""메뉴 누끼 이미지 일괄 임포트 (멱등).

'메뉴이미지(누끼)/' 의 원본 PNG(장당 7~16MB)를 웹용 WebP로 최적화해
app/static/images/menu/ (git 커밋 대상)에 저장하고, 파일명에서 카테고리/메뉴를
파싱해 DB에 upsert 한다. 파일명 패턴:
  "{카테고리번호}. {카테고리명} {메뉴번호}. {메뉴명}[ - {이미지번호}].png"
  이미지번호 1 → 카드(image), 2 → 상세(detail_image)

사용법: python import_menus.py   (로컬/서버 공용, DATABASE_URL 따름)
"""
import re
from pathlib import Path

from PIL import Image

BASE = Path(__file__).resolve().parent
SRC_DIR = BASE / "메뉴이미지(누끼)"
OUT_DIR = BASE / "app" / "static" / "images" / "menu"

PAT = re.compile(r"^(\d+)\.\s*(.+?)\s+(\d+)\.\s*(.+?)(?:\s*-\s*(\d+))?\.png$", re.IGNORECASE)

CARD_SIZE = 800
DETAIL_SIZE = 1200
MAX_KB = 300

DRINK_CATEGORY = "주류"  # 살얼음 캐러셀이 이름으로 참조 — 유지, sort는 항상 마지막


def optimize(src, out_path, max_px):
    """RGBA 유지 WebP 저장. 이미 있으면 스킵. 파일 크기(KB) 반환."""
    if out_path.exists():
        return out_path.stat().st_size // 1024
    img = Image.open(src).convert("RGBA")
    img.thumbnail((max_px, max_px))
    img.save(out_path, "WEBP", quality=80, method=6)
    if out_path.stat().st_size > MAX_KB * 1024:
        img.save(out_path, "WEBP", quality=70, method=6)
    return out_path.stat().st_size // 1024


def parse_files():
    """{(cat_no, cat_name): {menu_no: {"name":…, "files": {variant: path}}}}"""
    cats = {}
    skipped = []
    for f in sorted(SRC_DIR.iterdir()):
        m = PAT.match(f.name)
        if not m:
            if f.is_file():
                skipped.append(f.name)
            continue
        cat_no, cat_name = int(m.group(1)), m.group(2).strip()
        menu_no, menu_name = int(m.group(3)), m.group(4).strip()
        variant = int(m.group(5)) if m.group(5) else 1
        menus = cats.setdefault((cat_no, cat_name), {})
        entry = menus.setdefault(menu_no, {"name": menu_name, "files": {}})
        entry["files"][variant] = f
    for name in skipped:
        print(f"  [경고] 파일명 패턴 불일치 — 스킵: {name}")
    return cats


def run():
    from app import create_app
    from app.extensions import db
    from app.models import Menu, MenuCategory

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    cats = parse_files()
    new_cat_names = {name for (_, name) in cats}

    app = create_app()
    with app.app_context():
        # 1) 새 구성에 없는 기존 카테고리 정리 (주류는 유지)
        removed = []
        for cat in MenuCategory.query.all():
            if cat.name in new_cat_names or cat.name == DRINK_CATEGORY:
                continue
            Menu.query.filter_by(category_id=cat.id).delete()
            db.session.delete(cat)
            removed.append(cat.name)
        if removed:
            print(f"[1/3] 구 카테고리 제거: {', '.join(removed)}")

        # 2) 카테고리 upsert (sort = 파일명 번호, 주류는 마지막)
        cat_ids = {}
        for (cat_no, cat_name) in sorted(cats):
            cat = MenuCategory.query.filter_by(name=cat_name).first()
            if cat is None:
                cat = MenuCategory(name=cat_name)
                db.session.add(cat)
            cat.sort = cat_no
            cat.is_active = True
            db.session.flush()
            cat_ids[(cat_no, cat_name)] = cat.id
        drink = MenuCategory.query.filter_by(name=DRINK_CATEGORY).first()
        if drink:
            drink.sort = max(no for (no, _) in cats) + 1
        print(f"[2/3] 카테고리 upsert: {len(cat_ids)}종 + {DRINK_CATEGORY}{'(유지)' if drink else '(없음)'}")

        # 3) 이미지 최적화 + 메뉴 upsert
        n_new = n_upd = 0
        for (cat_no, cat_name), menus in sorted(cats.items()):
            for menu_no, entry in sorted(menus.items()):
                card_src = entry["files"].get(1) or next(iter(entry["files"].values()))
                detail_src = entry["files"].get(2, card_src)
                stem = f"c{cat_no:02d}_m{menu_no:02d}"
                card_kb = optimize(card_src, OUT_DIR / f"{stem}.webp", CARD_SIZE)
                detail_kb = optimize(detail_src, OUT_DIR / f"{stem}_d.webp", DETAIL_SIZE)

                item = Menu.query.filter_by(
                    category_id=cat_ids[(cat_no, cat_name)], name=entry["name"]
                ).first()
                if item is None:
                    item = Menu(category_id=cat_ids[(cat_no, cat_name)], name=entry["name"], price=0)
                    db.session.add(item)
                    n_new += 1
                else:
                    n_upd += 1
                item.image = f"/static/images/menu/{stem}.webp"
                item.detail_image = f"/static/images/menu/{stem}_d.webp"
                item.sort = menu_no
                item.is_active = True
                print(f"  {cat_name} #{menu_no:02d} {entry['name']} (카드 {card_kb}KB / 상세 {detail_kb}KB)")

        db.session.commit()
        total_c = MenuCategory.query.count()
        total_m = Menu.query.count()
        print(f"[3/3] 메뉴 신규 {n_new} / 갱신 {n_upd} — 현재 카테고리 {total_c}, 메뉴 {total_m}")


if __name__ == "__main__":
    run()
