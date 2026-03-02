import csv
import io
import json
import time
from django.http import JsonResponse, HttpResponse, FileResponse
from django.contrib.auth.decorators import login_required


@login_required
def user_info(request):
    """获取用户信息 API（需要登录）"""
    return JsonResponse({
        'success': True,
        'data': {
            'id': request.user.id,
            'username': request.user.username,
            'email': request.user.email,
            'is_staff': request.user.is_staff,
        }
    })


@login_required
def test_data(request):
    """获取测试数据 API"""
    return JsonResponse({
        'success': True,
        'data': {
            'items': [
                {'id': 1, 'name': '测试项目1', 'status': 'active'},
                {'id': 2, 'name': '测试项目2', 'status': 'pending'},
                {'id': 3, 'name': '测试项目3', 'status': 'completed'},
            ],
            'total': 3
        }
    })


@login_required
def download_csv(request):
    """
    下载 CSV 文件（测试文件下载功能）。
    支持 ?rows=N 参数控制数据行数，模拟大文件。
    """
    rows = int(request.GET.get('rows', 100))

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', '名称', '状态', '创建时间'])
    for i in range(1, rows + 1):
        writer.writerow([i, f'测试项目_{i}', '已完成', f'2026-03-{(i % 28) + 1:02d}'])

    content = output.getvalue().encode('utf-8-sig')  # utf-8-sig 支持 Excel 打开中文
    response = HttpResponse(content, content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition'] = f'attachment; filename="test_data_{rows}rows.csv"'
    response['Content-Length'] = len(content)
    return response


@login_required
def download_json(request):
    """下载 JSON 文件（测试文件下载功能）"""
    rows = int(request.GET.get('rows', 50))
    data = {
        'generated_at': time.strftime('%Y-%m-%d %H:%M:%S'),
        'total': rows,
        'items': [
            {'id': i, 'name': f'item_{i}', 'value': i * 10}
            for i in range(1, rows + 1)
        ]
    }
    content = json.dumps(data, ensure_ascii=False, indent=2).encode('utf-8')
    response = HttpResponse(content, content_type='application/json')
    response['Content-Disposition'] = f'attachment; filename="export_{rows}items.json"'
    response['Content-Length'] = len(content)
    return response
