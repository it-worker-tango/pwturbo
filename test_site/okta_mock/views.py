"""
模拟 OKTA SSO 认证流程的视图

完整流程：
  1. 应用检测到未登录 → 重定向到 /okta/authorize/?next=<app_url>
  2. 用户在模拟 OKTA 页面输入账号密码
  3. 验证成功 → 生成 token → 重定向回应用并携带 token
  4. 应用用 token 换取用户信息 → 完成登录
"""
import hashlib
import time
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth import authenticate, login
from django.views.decorators.csrf import csrf_exempt


# 简单的内存 token 存储（生产环境应使用 Redis 等）
_token_store = {}


def _generate_token(username: str) -> str:
    """生成模拟 OKTA token"""
    raw = f"{username}:{time.time()}:mock_okta_secret"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


def authorize(request):
    """
    模拟 OKTA 授权端点。
    真实 OKTA: GET /oauth2/v1/authorize
    """
    next_url = request.GET.get("next", "/dashboard/")
    client_id = request.GET.get("client_id", "mock_client")

    # 如果已经登录，直接生成 token 重定向
    if request.user.is_authenticated:
        token = _generate_token(request.user.username)
        _token_store[token] = {
            "username": request.user.username,
            "email": request.user.email,
            "expires": time.time() + 3600,
        }
        return redirect(f"{next_url}?okta_token={token}")

    # 未登录，显示模拟 OKTA 登录页
    return render(request, "okta_mock/login.html", {
        "next_url": next_url,
        "client_id": client_id,
    })


@csrf_exempt
def callback(request):
    """
    处理模拟 OKTA 登录表单提交。
    验证成功后重定向回应用并携带 token。
    """
    if request.method != "POST":
        return redirect("/okta/authorize/")

    username = request.POST.get("username", "")
    password = request.POST.get("password", "")
    next_url = request.POST.get("next_url", "/dashboard/")

    user = authenticate(request, username=username, password=password)
    if user:
        login(request, user)
        token = _generate_token(username)
        _token_store[token] = {
            "username": user.username,
            "email": user.email,
            "is_staff": user.is_staff,
            "expires": time.time() + 3600,
        }
        # 携带 token 重定向回应用
        redirect_url = f"{next_url}{'&' if '?' in next_url else '?'}okta_token={token}"
        return redirect(redirect_url)
    else:
        return render(request, "okta_mock/login.html", {
            "next_url": next_url,
            "error": "用户名或密码错误",
        })


def token_info(request):
    """
    模拟 OKTA userinfo 端点，用 token 换取用户信息。
    真实 OKTA: GET /oauth2/v1/userinfo
    """
    token = request.GET.get("token") or request.headers.get("Authorization", "").replace("Bearer ", "")

    if not token or token not in _token_store:
        return JsonResponse({"error": "invalid_token"}, status=401)

    info = _token_store[token]
    if time.time() > info["expires"]:
        del _token_store[token]
        return JsonResponse({"error": "token_expired"}, status=401)

    return JsonResponse({
        "success": True,
        "sub": info["username"],
        "email": info["email"],
        "name": info["username"],
    })
