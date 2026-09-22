"""리뷰 캡처(입소문)·매장 사진(인테리어) 동기화 (멱등).

- 로컬(원본 폴더 있음): 리뷰/, 매장이미지/ 의 PNG 를 WebP 최적화 →
  app/static/images/{reviews,store}/ (git 커밋 대상) → DB upsert.
- 서버(원본 폴더 없음): git 으로 받은 WebP 폴더를 스캔해 DB 동기화만.

story    ← reviews/rv_XX.webp  (branch_name '네이버 영수증리뷰', thumb=경로)
interior ← store/st_XX.webp    (image=원본 1600px, thumb=800px)
빈 thumb/image 의 기존 더미 행과, 파일이 사라진 행은 삭제.

사용법: python import_assets.py
"""
from pathlib import Path

BASE = Path(__file__).resolve().parent
SRC_REVIEWS = BASE / "리뷰"
SRC_STORES = BASE / "매장이미지"
OUT_REVIEWS = BASE / "app" / "static" / "images" / "reviews"
OUT_STORES = BASE / "app" / "static" / "images" / "store"


def optimize(src, out_path, max_px, quality=80):
    from PIL import Image

    if out_path.exists():
        return out_path.stat().st_size // 1024
    img = Image.open(src).convert("RGB")
    img.thumbnail((max_px, max_px))
    img.save(out_path, "WEBP", quality=quality, method=6)
    return out_path.stat().st_size // 1024


def review_card(src, out_card, out_full):
    """리뷰 캡처 → 카드용 720x1280 통일 규격(상단 기준, 짧으면 흰 여백) + 모달용 full(폭 900)."""
    from PIL import Image

    img = Image.open(src).convert("RGB")
    w, h = img.size
    # 카드: 폭 720 통일 → 높이 1280 상단 크롭/흰 배경 패딩
    ch = round(h * 720 / w)
    card = img.resize((720, ch), Image.LANCZOS)
    canvas = Image.new("RGB", (720, 1280), (255, 255, 255))
    canvas.paste(card.crop((0, 0, 720, min(ch, 1280))), (0, 0))
    canvas.save(out_card, "WEBP", quality=80, method=6)
    # 모달용 full: 폭 900, 크롭 없음
    full = img.resize((900, round(h * 900 / w)), Image.LANCZOS)
    full.save(out_full, "WEBP", quality=80, method=6)
    return out_card.stat().st_size // 1024, out_full.stat().st_size // 1024


def build_files(src_dir, out_dir, prefix, max_px, thumb_px=None, review=False):
    """원본이 있으면 변환, 없으면(서버) 기존 출력 폴더 스캔. 파일명 리스트 반환."""
    out_dir.mkdir(parents=True, exist_ok=True)
    if src_dir.exists():
        for i, f in enumerate(sorted(src_dir.glob("*.png")) + sorted(src_dir.glob("*.jpg")), 1):
            name = f"{prefix}_{i:02d}.webp"
            if review:
                card_out = out_dir / name
                full_out = out_dir / f"{prefix}_{i:02d}_full.webp"
                if not (card_out.exists() and full_out.exists()):
                    kb, kb_f = review_card(f, card_out, full_out)
                    print(f"  {name} {kb}KB / full {kb_f}KB")
                continue
            kb = optimize(f, out_dir / name, max_px)
            line = f"  {name} {kb}KB"
            if thumb_px:
                kb_t = optimize(f, out_dir / f"{prefix}_{i:02d}_t.webp", thumb_px)
                line += f" / 썸네일 {kb_t}KB"
            print(line)
    files = sorted(p.name for p in out_dir.glob(f"{prefix}_[0-9][0-9].webp"))
    return files


def run():
    from app import create_app
    from app.extensions import db
    from app.models import Interior, Story

    reviews = build_files(SRC_REVIEWS, OUT_REVIEWS, "rv", 720, review=True)
    stores = build_files(SRC_STORES, OUT_STORES, "st", 1600, thumb_px=800)
    print(f"[1/2] 리뷰 {len(reviews)}장 / 매장 {len(stores)}장")

    app = create_app()
    with app.app_context():
        # 입소문(story): thumb 경로 기준 upsert + 더미/사라진 파일 행 정리
        valid_thumbs = set()
        for i, name in enumerate(reviews, 1):
            thumb = f"/static/images/reviews/{name}"
            valid_thumbs.add(thumb)
            row = Story.query.filter_by(thumb=thumb).first()
            if row is None:
                row = Story(branch_name="네이버 영수증리뷰", title="", summary="", content="", thumb=thumb)
                db.session.add(row)
            row.sort = i
            row.is_active = True
        n_del = 0
        for row in Story.query.all():
            if row.thumb not in valid_thumbs:
                db.session.delete(row)
                n_del += 1

        # 인테리어(interior): image 경로 기준 upsert
        valid_imgs = set()
        for i, name in enumerate(stores, 1):
            image = f"/static/images/store/{name}"
            valid_imgs.add(image)
            row = Interior.query.filter_by(image=image).first()
            if row is None:
                row = Interior(title=f"매장 전경 {i:02d}", image=image)
                db.session.add(row)
            row.thumb = f"/static/images/store/{name[:-5]}_t.webp"
            row.sort = i
        n_del2 = 0
        for row in Interior.query.all():
            if row.image not in valid_imgs:
                db.session.delete(row)
                n_del2 += 1

        db.session.commit()
        print(f"[2/2] story {Story.query.count()}건(삭제 {n_del}) / interior {Interior.query.count()}건(삭제 {n_del2})")


if __name__ == "__main__":
    run()
