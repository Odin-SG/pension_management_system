import os
from fpdf import FPDF
from app.models import db, User, PensionFund, InterestRate, Report
from datetime import datetime


# Класс для генерации PDF-отчетов
class PDFReport(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Отчет по пенсионным накоплениям', 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Страница {self.page_no()}', 0, 0, 'C')

    def add_title(self, title):
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, title, 0, 1, 'L')
        self.ln(5)

    def add_table(self, data, headers):
        self.set_font('Arial', 'B', 12)
        for header in headers:
            self.cell(40, 10, header, 1, 0, 'C')
        self.ln()

        self.set_font('Arial', '', 12)
        for row in data:
            for item in row:
                self.cell(40, 10, str(item), 1, 0, 'C')
            self.ln()

# Логика генерации отчета по накоплениям пользователя
def generate_user_report(user_id):
    user = User.query.get(user_id)
    if not user:
        return None, 'Пользователь не найден.'

    funds = PensionFund.query.filter_by(user_id=user.id).all()
    total_amount = sum(fund.amount for fund in funds)
    user_rate = InterestRate.query.filter_by(user_id=user.id).first()
    rate = user_rate.rate if user_rate else InterestRate.query.filter_by(user_id=0).first().rate

    pdf = PDFReport()
    font_path = os.path.join(os.path.dirname(__file__), '../fonts/')

    pdf.add_font('Arial', '', os.path.join(font_path, 'arial.ttf'), uni=True)
    pdf.add_font('Arial', 'B', os.path.join(font_path, 'arialbd.ttf'), uni=True)
    pdf.add_font('Arial', 'I', os.path.join(font_path, 'ariali.ttf'), uni=True)
    pdf.add_font('Arial', 'BI', os.path.join(font_path, 'arialbi.ttf'), uni=True)

    pdf.add_page()
    pdf.add_title(f'Отчет по накоплениям для пользователя: {user.username}')
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 10, f'Общая сумма накоплений: {total_amount} руб.', 0, 1)
    pdf.cell(0, 10, f'Процентная ставка: {rate}%', 0, 1)

    headers = ['Сумма', 'Дата взноса']
    data = [[str(fund.amount or 0), fund.contribution_date.strftime('%Y-%m-%d') or 'N/A'] for fund in funds]
    pdf.add_table(data, headers)

    report_dir = f'reports/{user.username}'
    if not os.path.exists(report_dir):
        os.makedirs(report_dir)
    report_filename = f'{datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")}_{user.username}.pdf'
    report_path = os.path.join(report_dir, report_filename)
    pdf.output(report_path)

    new_report = Report(user_id=user.id, filename=report_filename)
    try:
        db.session.add(new_report)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return None, 'Ошибка при сохранении отчета в базе данных.'

    return report_path, None


def get_report_path(report_id):
    """
    Получение пути к сохраненному отчету по ID.
    """
    report = Report.query.get(report_id)
    if not report:
        return None, 'Отчет не найден.'

    user = User.query.get(report.user_id)
    if not user:
        return None, 'Пользователь, связанный с отчетом, не найден.'

    # Определяем путь к файлу
    report_path = os.path.join(f'reports/{user.username}', report.filename)
    if not os.path.exists(report_path):
        return None, 'Файл отчета не найден на сервере.'

    return report_path, None