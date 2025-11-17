from django.urls import path

from boards.views import PostDetailView, PostListCreateView


app_name = "boards"

urlpatterns = [
    path("posts", PostListCreateView.as_view(), name="post-list"),
    path("posts/<int:pk>", PostDetailView.as_view(), name="post-detail"),
]
