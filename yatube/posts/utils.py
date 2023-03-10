from django.core.paginator import Paginator

COUNT_PAGE = 10


def paginator(request, post_list):
    paginator = Paginator(post_list, COUNT_PAGE)
    page_number = request.GET.get("page")
    return paginator.get_page(page_number)
