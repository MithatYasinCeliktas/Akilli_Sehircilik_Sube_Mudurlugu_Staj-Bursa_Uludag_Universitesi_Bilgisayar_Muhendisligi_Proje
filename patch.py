import os

def replace_in_file(filepath, old_text, new_text):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    content = content.replace(old_text, new_text)
    with open(filepath, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)

# 1. setup_db.py
setup_db_path = 'backend/setup_db.py'
old_setup = 'from app.models.institution import Institution  # noqa: F401'
new_setup = 'from app.models.institution import Institution  # noqa: F401\nfrom app.models.system_log import SystemLog\nfrom app.models.notification import Notification'
replace_in_file(setup_db_path, old_setup, new_setup)

# 2. unit-list.component.html
unit_html_path = 'frontend/src/app/features/units/pages/unit-list/unit-list.component.html'
old_html = '<p-dropdown'
new_html = '<p-dropdown appendTo="body"'
replace_in_file(unit_html_path, old_html, new_html)

# 3. unit-list.component.ts
unit_ts_path = 'frontend/src/app/features/units/pages/unit-list/unit-list.component.ts'
old_unit_ts_1 = 'if (this.unitForm.invalid) {'
new_unit_ts_1 = 'if (this.unitForm.invalid) {\n      this.unitForm.markAllAsTouched();'
replace_in_file(unit_ts_path, old_unit_ts_1, new_unit_ts_1)
old_unit_ts_2 = 'error: () => {\n          this.formLoading = false;\n        }'
new_unit_ts_2 = 'error: (err: any) => {\n          this.formLoading = false;\n          this.messageService.add({severity:error, summary:Hata, detail:err.error?.detail || Kayıt sırasında hata oluştu});\n        }'
replace_in_file(unit_ts_path, old_unit_ts_2, new_unit_ts_2)

# 4. report-form.component.ts
report_ts_path = 'frontend/src/app/features/reports/pages/report-form/report-form.component.ts'
old_rep_ts_1 = 'if (this.reportForm.invalid) return;'
new_rep_ts_1 = 'if (this.reportForm.invalid) { this.reportForm.markAllAsTouched(); return; }'
replace_in_file(report_ts_path, old_rep_ts_1, new_rep_ts_1)
old_rep_ts_2 = 'error: () => { this.loading = false; }'
new_rep_ts_2 = 'error: (err: any) => { this.loading = false; this.messageService.add({severity:error, summary:Hata, detail:err.error?.detail || Kayıt sırasında hata oluştu}); }'
replace_in_file(report_ts_path, old_rep_ts_2, new_rep_ts_2)

print("Done")