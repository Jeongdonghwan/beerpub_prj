"""메뉴 누끼 이미지 일괄 임포트 (멱등).

- 로컬(원본 폴더 있음): '메뉴이미지(누끼)/' 의 PNG를 파싱·WebP 최적화 →
  menu_manifest.json 생성(git 커밋 대상) → DB upsert.
- 서버(원본 폴더 없음): git 으로 받은 menu_manifest.json + WebP 만으로 DB upsert.

파일명 패턴: "{카테고리번호}. {카테고리명} {메뉴번호}. {메뉴명}[ - {이미지번호}].png"
  이미지번호 1 → 카드(image), 2 → 상세(detail_image)

사용법: python import_menus.py   (로컬/서버 공용, DATABASE_URL 따름)
"""
import json
import re
from pathlib import Path

BASE = Path(__file__).resolve().parent
SRC_DIR = BASE / "메뉴이미지(누끼)"
OUT_DIR = BASE / "app" / "static" / "images" / "menu"
MANIFEST = BASE / "menu_manifest.json"

PAT = re.compile(r"^(\d+)\.\s*(.+?)\s+(\d+)\.\s*(.+?)(?:\s*-\s*(\d+))?\.png$", re.IGNORECASE)

CARD_SIZE = 800
DETAIL_SIZE = 1200
MAX_KB = 300

DRINK_CATEGORY = "주류"  # 살얼음 캐러셀이 이름으로 참조 — 유지, sort는 항상 마지막


def optimize(src, out_path, max_px):
    """RGBA 유지 WebP 저장. 이미 있으면 스킵. 파일 크기(KB) 반환."""
    from PIL import Image

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


def build_records():
    """[{cat_no, cat_name, menu_no, name, image, detail_image}, ...] 반환.
    원본 폴더가 있으면 파싱+최적화 후 manifest 저장, 없으면(서버) manifest 로드."""
    if not SRC_DIR.exists():
        if not MANIFEST.exists():
            raise SystemExit(
                f"원본 폴더({SRC_DIR.name})도 {MANIFEST.name}도 없습니다. "
                "로컬에서 한 번 실행해 manifest 를 생성·커밋한 뒤 서버에서 git pull 하세요."
            )
        records = json.loads(MANIFEST.read_text(encoding="utf-8"))
        print(f"[0/3] 서버 모드 — {MANIFEST.name} 에서 {len(records)}건 로드")
        # git 으로 받은 WebP 존재 검증
        missing = [r["image"] for r in records if not (OUT_DIR / Path(r["image"]).name).exists()]
        if missing:
            print(f"  [경고] WebP {len(missing)}건 없음 — git pull 이 완전한지 확인 필요")
        return records

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    cats = parse_files()
    records = []
    for (cat_no, cat_name), menus in sorted(cats.items()):
        for menu_no, entry in sorted(menus.items()):
            card_src = entry["files"].get(1) or next(iter(entry["files"].values()))
            detail_src = entry["files"].get(2, card_src)
            stem = f"c{cat_no:02d}_m{menu_no:02d}"
            card_kb = optimize(card_src, OUT_DIR / f"{stem}.webp", CARD_SIZE)
            detail_kb = optimize(detail_src, OUT_DIR / f"{stem}_d.webp", DETAIL_SIZE)
            records.append({
                "cat_no": cat_no, "cat_name": cat_name,
                "menu_no": menu_no, "name": entry["name"],
                "image": f"/static/images/menu/{stem}.webp",
                "detail_image": f"/static/images/menu/{stem}_d.webp",
            })
            print(f"  {cat_name} #{menu_no:02d} {entry['name']} (카드 {card_kb}KB / 상세 {detail_kb}KB)")
    MANIFEST.write_text(json.dumps(records, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"[0/3] {MANIFEST.name} 저장 ({len(records)}건) — git 커밋 대상")
    return records


def run():
    from app import create_app
    from app.extensions import db
    from app.models import Menu, MenuCategory

    records = build_records()
    new_cat_names = {r["cat_name"] for r in records}

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
        cat_pairs = sorted({(r["cat_no"], r["cat_name"]) for r in records})
        for (cat_no, cat_name) in cat_pairs:
            cat = MenuCategory.query.filter_by(name=cat_name).first()
            if cat is None:
                cat = MenuCategory(name=cat_name)
                db.session.add(cat)
            cat.sort = cat_no
            cat.is_active = True
            db.session.flush()
            cat_ids[cat_name] = cat.id
        drink = MenuCategory.query.filter_by(name=DRINK_CATEGORY).first()
        if drink:
            drink.sort = max(no for (no, _) in cat_pairs) + 1
        print(f"[2/3] 카테고리 upsert: {len(cat_ids)}종 + {DRINK_CATEGORY}{'(유지)' if drink else '(없음)'}")

        # 3) 메뉴 upsert
        n_new = n_upd = 0
        for r in records:
            item = Menu.query.filter_by(category_id=cat_ids[r["cat_name"]], name=r["name"]).first()
            if item is None:
                item = Menu(category_id=cat_ids[r["cat_name"]], name=r["name"], price=0)
                db.session.add(item)
                n_new += 1
            else:
                n_upd += 1
            item.image = r["image"]
            item.detail_image = r["detail_image"]
            item.sort = r["menu_no"]
            item.is_active = True

        db.session.commit()
        total_c = MenuCategory.query.count()
        total_m = Menu.query.count()
        print(f"[3/3] 메뉴 신규 {n_new} / 갱신 {n_upd} — 현재 카테고리 {total_c}, 메뉴 {total_m}")


if __name__ == "__main__":
    run()
