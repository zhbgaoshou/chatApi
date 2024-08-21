from rest_framework.pagination import PageNumberPagination


# 继承分页类
class PublicPagination(PageNumberPagination):
    page_query_description = '分页参数，当前的页数'
    page_size_query_description = "每页的显示的页数，默认为10条数据，最大为200条"

    page_size = 10  # 每页显示的默认数据个数
    page_query_param = 'page'  # 页号,第几页的参数 ,比如定义为pages，那么请求分页的参数就应该是pages
    page_size_query_param = 'page_size'  # 自己指定每页显示多少个数
    max_page_size = 200  # 最大允许设置的每页显示的数量
