from admin_app.pages.dashboard import DashboardPage
from admin_app.pages.user_detail import UserDetailPage
from admin_app.pages.users import UsersPage

PAGE_REGISTRY = {
    "dashboard": DashboardPage(),
    "users": UsersPage(),
    "user_detail": UserDetailPage(),
}
