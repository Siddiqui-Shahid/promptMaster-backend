from imagekitio import ImageKit

from app.core.config import get_settings


settings = get_settings()

imageKit = ImageKit(private_key=settings.imagekit_private_key)
URL_ENDPOINT = settings.imagekit_url_endpoint
