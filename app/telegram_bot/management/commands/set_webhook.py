from django.core.management.base import BaseCommand
from django.conf import settings
import requests

class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        webhook_url = settings.TELEGRAM_WEBHOOK_URL
        token = settings.TELEGRAM_BOT_TOKEN
        url = f"https://api.telegram.org/bot{token}/setWebhook"
        response = requests.post(url, data={'url': webhook_url})
        if response.status_code == 200:
            self.stdout.write(self.style.SUCCESS(f"Webhook set to {webhook_url}"))
        else:
            self.stdout.write(self.style.ERROR(f"Failed to set webhook: {response.text}"))