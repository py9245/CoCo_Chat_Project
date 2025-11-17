from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView

from boards.models import Post
from boards.serializers import PostSerializer


class PostListCreateView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    def get(self, request):
        posts = Post.objects.select_related("author", "author__profile").all()
        serializer = PostSerializer(posts, many=True, context={"request": request})
        return Response({"posts": serializer.data})

    def post(self, request):
        serializer = PostSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        post = serializer.save()
        return Response(
            PostSerializer(post, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class PostDetailView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    def get_object(self, pk):
        return Post.objects.select_related("author", "author__profile").get(pk=pk)

    def ensure_owner(self, request, post):
        if not request.user.is_authenticated:
            raise PermissionDenied("로그인이 필요합니다.")
        if request.user.is_staff or post.author_id == request.user.id:
            return
        raise PermissionDenied("본인 게시글만 수정 또는 삭제할 수 있습니다.")

    def get(self, request, pk):
        post = self.get_object(pk)
        serializer = PostSerializer(post, context={"request": request})
        return Response({"post": serializer.data})

    def patch(self, request, pk):
        post = self.get_object(pk)
        self.ensure_owner(request, post)
        serializer = PostSerializer(post, data=request.data, context={"request": request}, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"post": serializer.data})

    def delete(self, request, pk):
        post = self.get_object(pk)
        self.ensure_owner(request, post)
        post.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
