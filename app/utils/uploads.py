import uuid
from pathlib import Path

from PIL import Image

from config.settings import Config


def save_image(file_storage, board):
    """업로드 저장 + 썸네일 생성. (image_url, thumb_url) 반환. 실패/빈 파일이면 ("", "")."""
    if not file_storage or not file_storage.filename:
        return "", ""
    ext = Path(file_storage.filename).suffix.lower()
    if ext not in Config.ALLOWED_IMAGE_EXT:
        return "", ""

    directory = Config.UPLOAD_DIR / board
    directory.mkdir(parents=True, exist_ok=True)
    name = f"{uuid.uuid4().hex}{ext}"
    path = directory / name
    file_storage.save(path)
    url = f"/static/uploads/{board}/{name}"

    thumb_url = ""
    width = Config.THUMB_WIDTH.get(board)
    if width:
        try:
            img = Image.open(path)
            img.thumbnail((width, width * 3))
            thumb_name = f"thumb_{name}"
            img.save(directory / thumb_name)
            thumb_url = f"/static/uploads/{board}/{thumb_name}"
        except OSError:
            thumb_url = url
    return url, thumb_url
