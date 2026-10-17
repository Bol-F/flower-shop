from rest_framework import generics, permissions, serializers
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle

from apps.users.views import OAuthNoStoreMixin

from .assistant import assistant_capabilities, flower_advice


class FlowerAdviceSerializer(serializers.Serializer):
    message = serializers.CharField(max_length=1500, trim_whitespace=True)
    language = serializers.ChoiceField(choices=('EN', 'RU', 'UZ'), default='EN')
    use_web_search = serializers.BooleanField(default=False)


class AssistantThrottle(UserRateThrottle):
    scope = 'flower_assistant'


class AssistantDailyThrottle(UserRateThrottle):
    scope = 'flower_assistant_daily'


class AssistantCapabilitiesView(OAuthNoStoreMixin, generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response(assistant_capabilities())


class FlowerAdviceView(OAuthNoStoreMixin, generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = FlowerAdviceSerializer
    throttle_classes = [AssistantThrottle, AssistantDailyThrottle]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(flower_advice(**serializer.validated_data))
