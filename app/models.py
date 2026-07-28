from datetime import datetime

from .extensions import db


class MenuCategory(db.Model):
    __tablename__ = "menu_category"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    sort = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    menus = db.relationship("Menu", backref="category", lazy="dynamic")


class Menu(db.Model):
    __tablename__ = "menu"
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey("menu_category.id"), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    name_en = db.Column(db.String(100), default="")
    price = db.Column(db.Integer, default=0)
    description = db.Column(db.String(500), default="")
    badge = db.Column(db.Enum("new", "best", "signature", "", name="menu_badge"), default="")
    image = db.Column(db.String(255), default="")
    detail_image = db.Column(db.String(255), default="")
    sort = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Interior(db.Model):
    __tablename__ = "interior"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    image = db.Column(db.String(255), default="")
    thumb = db.Column(db.String(255), default="")
    sort = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Story(db.Model):
    __tablename__ = "story"
    id = db.Column(db.Integer, primary_key=True)
    branch_name = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    summary = db.Column(db.String(300), default="")
    content = db.Column(db.Text, default="")
    thumb = db.Column(db.String(255), default="")
    sort = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Store(db.Model):
    __tablename__ = "store"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    region = db.Column(db.String(30), default="")
    address = db.Column(db.String(255), default="")
    phone = db.Column(db.String(30), default="")
    lat = db.Column(db.Float, nullable=True)
    lng = db.Column(db.Float, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Inquiry(db.Model):
    __tablename__ = "inquiry"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(30), nullable=False)
    region = db.Column(db.String(30), default="")
    channel = db.Column(db.String(30), default="")
    message = db.Column(db.Text, default="")
    agree_privacy = db.Column(db.Boolean, default=False)
    status = db.Column(db.Enum("new", "contacted", "closed", name="inquiry_status"), default="new")
    memo = db.Column(db.Text, default="")
    ip = db.Column(db.String(50), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)


class Banner(db.Model):
    __tablename__ = "banner"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), default="")
    image = db.Column(db.String(255), default="")
    link = db.Column(db.String(255), default="")
    sort = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)


class Popup(db.Model):
    __tablename__ = "popup"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), default="")
    image = db.Column(db.String(255), default="")
    link = db.Column(db.String(255), default="")
    is_active = db.Column(db.Boolean, default=True)
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)


class Notice(db.Model):
    __tablename__ = "notice"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, default="")
    hit = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class History(db.Model):
    __tablename__ = "history"
    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer, nullable=False)
    month = db.Column(db.Integer, default=1)
    content = db.Column(db.String(300), nullable=False)
    sort = db.Column(db.Integer, default=0)


class SiteConfig(db.Model):
    __tablename__ = "site_config"
    cfg_key = db.Column(db.String(64), primary_key=True)
    cfg_value = db.Column(db.Text, default="")


class AdminUser(db.Model):
    __tablename__ = "admin_user"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


def get_site_config():
    """site_config 전체를 dict 로 반환 (템플릿 전역 주입용)."""
    return {row.cfg_key: row.cfg_value for row in SiteConfig.query.all()}
