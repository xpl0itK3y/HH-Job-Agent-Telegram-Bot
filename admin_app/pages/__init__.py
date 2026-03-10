from admin_app.pages.admin_tools import AdminToolsPage
from admin_app.pages.audit_logs import AuditLogsPage
from admin_app.pages.chat_history import ChatHistoryPage
from admin_app.pages.dashboard import DashboardPage
from admin_app.pages.operations import OperationsPage
from admin_app.pages.resumes import ResumesPage
from admin_app.pages.search_settings import SearchSettingsPage
from admin_app.pages.user_detail import UserDetailPage
from admin_app.pages.users import UsersPage
from admin_app.pages.vacancies import VacanciesPage

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
