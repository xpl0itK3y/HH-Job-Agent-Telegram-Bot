from admin_app.views.admin_tools import AdminToolsPage
from admin_app.views.audit_logs import AuditLogsPage
from admin_app.views.chat_history import ChatHistoryPage
from admin_app.views.dashboard import DashboardPage
from admin_app.views.operations import OperationsPage
from admin_app.views.resumes import ResumesPage
from admin_app.views.search_settings import SearchSettingsPage
from admin_app.views.user_detail import UserDetailPage
from admin_app.views.users import UsersPage
from admin_app.views.vacancies import VacanciesPage

PAGE_REGISTRY = {
    "dashboard": DashboardPage(),
    "users": UsersPage(),
    "user_detail": UserDetailPage(),
    "resumes": ResumesPage(),
    "search_settings": SearchSettingsPage(),
    "vacancies": VacanciesPage(),
    "chat_history": ChatHistoryPage(),
    "operations": OperationsPage(),
    "audit_logs": AuditLogsPage(),
    "admin_tools": AdminToolsPage(),
}
