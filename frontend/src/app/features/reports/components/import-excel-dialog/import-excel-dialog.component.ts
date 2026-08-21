import { Component, OnInit } from '@angular/core';
import { DynamicDialogRef } from 'primeng/dynamicdialog';
import { ReportService } from '../../../../core/services/report.service';
import { Message, MessageService } from 'primeng/api';
import { ItemCategory } from '../../../../core/models/report.model';
import { AuthService } from '../../../../core/services/auth.service';
import { InstitutionService } from '../../../../core/services/institution.service';

@Component({
  selector: 'app-import-excel-dialog',
  templateUrl: './import-excel-dialog.component.html'
})
export class ImportExcelDialogComponent implements OnInit {
  step: number = 1;
  selectedFile: File | null = null;
  loading: boolean = false;
  
  previewData: any = null;
  resultData: any = null;
  messages: Message[] = [];
  institutions: any[] = [];

  isManager: boolean = false;
  targetReport: 'OWN_REPORT' | 'MANAGER_REPORT' = 'OWN_REPORT';

  constructor(
    private ref: DynamicDialogRef,
    private reportService: ReportService,
    private authService: AuthService,
    private institutionService: InstitutionService,
    private messageService: MessageService
  ) {}

  ngOnInit(): void {
    const user = this.authService.currentUserValue;
    if (user && ['MANAGER', 'USER_MANAGER', 'ADMIN'].includes(user.role)) {
      this.isManager = true;
      this.targetReport = 'OWN_REPORT'; // Default for managers
    } else {
      this.isManager = false;
      this.targetReport = 'MANAGER_REPORT'; // Only option for normal users
    }

    this.institutionService.getInstitutions(true).subscribe(res => {
      this.institutions = res || [];
    });

  }

  onFileSelected(event: any): void {
    const file = event.target.files[0];
    if (file) {
      this.selectedFile = file;
    }
  }

  previewFile(): void {
    if (!this.selectedFile) return;

    this.loading = true;
    this.messages = [];
    
    this.reportService.previewImport(this.selectedFile, this.targetReport).subscribe({
      next: (data: any) => {
        this.previewData = data;
        this.step = 2;
        this.loading = false;
        
        if (!data.valid) {
          this.messages = [
            { severity: 'error', summary: 'Hata', detail: 'Dosyada hatalar veya çözülmesi gereken çakışmalar (isim benzerliği) var. Lütfen aşağıdaki tabloyu inceleyin.' }
          ];
        }
      },
      error: (err: any) => {
        this.loading = false;
        this.messages = [
          { severity: 'error', summary: 'Hata', detail: err.error?.detail || 'Dosya okunurken bir hata oluştu.' }
        ];
        this.step = 2;
      }
    });
  }


  resolveInstitutionConflict(row: any, conflict: any, newName: string): void {
    if (!newName) return;
    
    // Replace raw with newName in kurum string
    let parts = (row.kurum || '').split(',').map((s: string) => s.trim());
    let idx = parts.indexOf(conflict.raw);
    if (idx !== -1) {
      parts[idx] = newName;
      row.kurum = parts.join(', ');
    }
    
    // Remove from conflicts
    row.institution_conflicts = row.institution_conflicts.filter((c: any) => c.raw !== conflict.raw);
    
    // Check if error needs removing
    if (row.institution_conflicts.length === 0) {
      row.errors = row.errors.filter((e: string) => !e.includes('kurumu sistemde bulunamadı'));
    }
    
    this.messageService.add({severity:'success', summary:'Güncellendi', detail:'Kurum ismi başarıyla değiştirildi.'});
  }

  requestOrAddInstitution(row: any, conflict: any): void {
    if (this.isManager) {
      // Yöneticiler doğrudan ekleyebilir
      this.institutionService.createInstitution({ name: conflict.raw, is_active: true }).subscribe({
        next: (res) => {
          this.institutions.push(res);
          this.resolveInstitutionConflict(row, conflict, conflict.raw);
          this.messageService.add({severity:'success', summary:'Eklendi', detail: `'${conflict.raw}' kurumu başarıyla eklendi.`});
        },
        error: (err) => {
          this.messageService.add({severity:'error', summary:'Hata', detail: 'Kurum eklenirken hata oluştu.'});
        }
      });
    } else {
      // Personel istek yollar
      this.institutionService.requestInstitution(conflict.raw).subscribe({
        next: (res) => {
          this.messageService.add({severity:'success', summary:'Talep İletildi', detail: `'${conflict.raw}' için yöneticinize talep gönderildi. İçe aktarmaya devam etmek için bu kurumu excel satırından silmeli veya başka bir kurumla eşleştirmelisiniz.`});
        },
        error: (err) => {
          this.messageService.add({severity:'error', summary:'Hata', detail: 'Talep gönderilirken hata oluştu.'});
        }
      });
    }
  }

  isValidForSubmit(): boolean {

    if (!this.previewData || !this.previewData.rows) return false;
    
    if (this.previewData.global_errors && this.previewData.global_errors.length > 0) return false;

    for (let row of this.previewData.rows) {
      if (row.errors && row.errors.length > 0) return false;
      if (row.conflicts && row.conflicts.length > 0 && !row.target_user_id) return false;
      if (row.institution_conflicts && row.institution_conflicts.length > 0) return false;
      if (row.available_reports && row.available_reports.length > 1 && !row.selected_report_id) return false;
    }
    
    return true;
  }

  executeImport(): void {
    this.loading = true;
    const payload = {
      ...this.previewData,
      target: this.targetReport
    };
    
    this.reportService.revalidateImport(payload).subscribe({
      next: (res: any) => {
        this.previewData = res;
        
        // Yeniden kontrol sonucunda hata kalmadıysa direkt execute'a geç
        if (this.isValidForSubmit()) {
          const execPayload = {
            ...this.previewData,
            target: this.targetReport
          };
          this.reportService.executeImport(execPayload).subscribe({
            next: (execRes: any) => {
              this.loading = false;
              this.resultData = execRes;
              this.step = 3;
            },
            error: (err) => {
              this.loading = false;
              this.messageService.add({
                severity: 'error',
                summary: 'Hata',
                detail: err.error?.detail?.message || 'İçe aktarma sırasında bir hata oluştu.'
              });
            }
          });
        } else {
          // Hata varsa kullanıcıya uyarı ver ve önizlemede kal
          this.loading = false;
          this.messageService.add({
            severity: 'warn',
            summary: 'Eksik veya Hatalı Bilgi',
            detail: 'Lütfen listedeki hataları düzeltin.'
          });
        }
      },
      error: (err) => {
        this.loading = false;
        this.messageService.add({
          severity: 'error',
          summary: 'Hata',
          detail: 'Yeniden doğrulama sırasında bir hata oluştu.'
        });
      }
    });
  }

  close(success: boolean = false): void {
    this.ref.close(success);
  }

  getCategoryLabel(category: string): string {
    switch (category) {
      case ItemCategory.YAPILAN_ISLER: return 'Yapılan İşler';
      case ItemCategory.YAPILACAK_ISLER: return 'Yapılacak İşler';
      case ItemCategory.KORDINASYON_GEREKTIREN_ISLER: return 'Koordinasyon Gerektiren İşler';
      default: return category;
    }
  }
}
