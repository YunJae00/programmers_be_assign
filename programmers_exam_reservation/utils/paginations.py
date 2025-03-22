from rest_framework.pagination import PageNumberPagination


class CustomPagination(PageNumberPagination):
    page_size_query_param = 10
    page_size_display_value = 'page_size'
    max_page_size = 100

    def get_paginated_data(self, data):
        return {
            "links": {
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
            },
            "total": self.page.paginator.count,
            "page_size": int(self.request.GET.get("page_size", self.page_size)),
            "current_page": self.page.number,
            "total_pages": self.page.paginator.num_pages,
            "results": data,
        }
