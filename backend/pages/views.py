from django.http import JsonResponse
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import UserProfile
from boards.models import Post
from chatrooms.models import ChatRoom
from pages.models import PageSection, SiteStat
from pages.serializers import PageSectionSerializer, SiteStatSerializer
from randomchat.utils import perform_randomchat_housekeeping


def healthz(_request):
    return JsonResponse({"ok": True})


class HomePageView(APIView):
    def get(self, request):
        perform_randomchat_housekeeping()
        sections = PageSection.objects.all()
        stats = SiteStat.objects.all()
        payload = {
            "sections": PageSectionSerializer(sections, many=True).data,
            "stats": SiteStatSerializer(stats, many=True).data,
            "totals": {
                "users": UserProfile.objects.count(),
                "posts": Post.objects.count(),
                "rooms": ChatRoom.objects.count(),
            },
        }
        return Response(payload)
