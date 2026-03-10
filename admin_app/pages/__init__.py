from admin_app.pages.dashboard import DashboardPage
from admin_app.pages.users import UsersPage

PAGE_REGISTRY = {
    "dashboard": DashboardPage(),
    "users": UsersPage(),
}
