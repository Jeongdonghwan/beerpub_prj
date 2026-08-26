from flask import Blueprint, Response, abort, render_template, request, url_for

from ..models import Banner, Interior, Menu, MenuCategory, Notice, Story

bp = Blueprint("main", __name__)

DOC_SLUGS = {
    "policy": ("이용약관", "doc_policy"),
    "private": ("개인정보처리방침", "doc_private"),
    "antiemail": ("이메일무단수집거부", "doc_antiemail"),
}


@bp.route("/")
def index():
    menus = (
        Menu.query.filter_by(is_active=True)
        .order_by(Menu.sort, Menu.id)
        .limit(10)
        .all()
    )
    interiors = Interior.query.order_by(Interior.sort, Interior.id).limit(12).all()
    stories = (
        Story.query.filter_by(is_active=True).order_by(Story.sort).limit(12).all()
    )
    banners = Banner.query.filter_by(is_active=True).order_by(Banner.sort).all()
    drink_cat = MenuCategory.query.filter_by(name="주류").first()
    drinks = (
        Menu.query.filter_by(category_id=drink_cat.id, is_active=True)
        .order_by(Menu.sort, Menu.id).all()
        if drink_cat else []
    )
    return render_template(
        "main/index.html",
        menus=menus,
        interiors=interiors,
        stories=stories,
        banners=banners,
        drink_cat=drink_cat,
        drinks=drinks,
    )


@bp.route("/story/popup/<int:story_id>")
def story_popup(story_id):
    item = Story.query.get_or_404(story_id)
    return render_template("main/_story_popup.html", item=item)


@bp.route("/doc/<slug>")
def doc(slug):
    if slug not in DOC_SLUGS:
        abort(404)
    title, cfg_key = DOC_SLUGS[slug]
    tpl = "doc/_fragment.html" if request.args.get("embed") else "doc/document.html"
    return render_template(tpl, doc_title=title, cfg_key=cfg_key, slug=slug)


@bp.route("/sitemap.xml")
def sitemap():
    base = request.url_root.rstrip("/")
    static_paths = [
        "/", "/brand/info", "/brand/history", "/menu/preview", "/menu/list",
        "/interior/list", "/store/list", "/startup/step", "/startup/cost",
        "/inquiry/", "/board/notice", "/doc/policy", "/doc/private", "/doc/antiemail",
    ]
    urls = [f"<url><loc>{base}{p}</loc></url>" for p in static_paths]
    for n in Notice.query.order_by(Notice.id).all():
        urls.append(f"<url><loc>{base}{url_for('board.notice_view', notice_id=n.id)}</loc></url>")
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        + "".join(urls)
        + "</urlset>"
    )
    return Response(xml, mimetype="application/xml")


@bp.route("/robots.txt")
def robots():
    base = request.url_root.rstrip("/")
    body = f"User-agent: *\nAllow: /\nDisallow: /admin\nSitemap: {base}/sitemap.xml\n"
    return Response(body, mimetype="text/plain")
