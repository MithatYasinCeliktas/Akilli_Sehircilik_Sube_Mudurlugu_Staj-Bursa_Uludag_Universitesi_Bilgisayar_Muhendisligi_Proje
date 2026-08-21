import { Component, OnInit } from '@angular/core';
import { Location } from '@angular/common';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { ReportService } from '../../../../core/services/report.service';
import { ItemCategory, ReportStatus, ActivityReport, ReportItem, ReportItemReview } from '../../../../core/models/report.model';
import { AuthService } from '../../../../core/services/auth.service';
import { InstitutionService } from '../../../../core/services/institution.service';
import { Institution } from '../../../../core/models/institution.model';
import { MessageService } from 'primeng/api';

@Component({
  selector: 'app-report-form',
  templateUrl: './report-form.component.html',
  providers: [MessageService]
})
export class ReportFormComponent implements OnInit {
  reportForm!: FormGroup;
  itemForm!: FormGroup;
  reviewForm!: FormGroup;
  passDownForm!: FormGroup;

  isEditMode: boolean = false;
  reportId: number | null = null;
  reportData: ActivityReport | null = null;
  loading: boolean = false;
  
  isCreator: boolean = false;
  canEditReportBase: boolean = false; // Only superadmin or creator
  canAddRow: boolean = false; // Only if NOT creator AND report not approved
  canApproveReport: boolean = false;
  canTransferReport: boolean = false;
  
  currentUserId: number | null = null;

  
  get yapilanIsler() {
    let items = this.reportData?.yapilan_isler || [];
    return items.sort((a, b) => (a.creator_id || 0) - (b.creator_id || 0));
  }
  
  get yapilacakIsler() {
    let items = this.reportData?.yapilacak_isler || [];
    return items.sort((a, b) => (a.creator_id || 0) - (b.creator_id || 0));
  }

  get koordinasyonIsleri() {
    let items = this.reportData?.koordinasyon_isleri || [];
    return items.sort((a, b) => (a.creator_id || 0) - (b.creator_id || 0));
  }

  categoryOptions = [
    { label: 'Yapılan İşler', value: ItemCategory.YAPILAN_ISLER },
    { label: 'Yapılacak İşler', value: ItemCategory.YAPILACAK_ISLER },
    { label: 'Koordinasyon Gerektiren İşler', value: ItemCategory.KORDINASYON_GEREKTIREN_ISLER }
  ];
  institutions: Institution[] = [];

  readonly categoryKordinasyon = ItemCategory.KORDINASYON_GEREKTIREN_ISLER;
  categoryYapanIsler = ItemCategory.YAPILAN_ISLER;

  // Tablo Sütun Genişlik Ayarları (İhtiyaca göre buradan değiştirilebilir)
  // Toplam %100'ü geçmemesine veya tablo genişliğine uygun olmasına dikkat edin.
  colWidthContent = '35%';        // Açıklama sütunu (en geniş)
  colWidthProposals = '25%';      // Öneriler sütunu (ikinci geniş)
  colWidthInstitutions = '15%';   // İlgili Kurum Kuruluşlar sütunu
  colWidthDefault = '10%';        // Diğer sütunlar (Sıra, Personel, Durum, İşlemler)

  // Modals
  displayItemModal: boolean = false;
  displayReviewModal: boolean = false;
  displayPassDownModal: boolean = false;
  editingItemId: number | null = null;
  reviewingItemId: number | null = null;
  passingDownItemId: number | null = null;
  highlightedItemId: number | null = null;

  constructor(
    private fb: FormBuilder,
    private reportService: ReportService,
    private authService: AuthService,
    private route: ActivatedRoute,
    private router: Router,
    private messageService: MessageService,
    private institutionService: InstitutionService,
    private location: Location
  ) {}

  ngOnInit(): void {
    this.currentUserId = this.authService.currentUserValue?.id || null;
    this.initForms();
    
    const idParam = this.route.snapshot.paramMap.get('id');
    if (idParam && idParam !== 'new') {
      this.isEditMode = true;
      this.reportId = +idParam;
      this.loadReportData(this.reportId);
    } else {
      // New report form only allows year/month setup
      this.canEditReportBase = true;
    }
    
    this.route.queryParams.subscribe(params => {
      if (params['itemId']) {
        this.highlightedItemId = +params['itemId'];
        setTimeout(() => {
          const el = document.getElementById('item-' + this.highlightedItemId);
          if (el) {
            el.scrollIntoView({ behavior: 'smooth', block: 'center' });
          }
        }, 500); // give table time to render
      }
    });

    this.institutionService.getInstitutions(true).subscribe({
      next: (data) => {
        this.institutions = data;
      }
    });
  }

  private initForms(): void {
    this.reportForm = this.fb.group({
      year: [new Date().getFullYear(), [Validators.required, Validators.min(2000)]],
      month: [new Date().getMonth() + 1, [Validators.required, Validators.min(1), Validators.max(12)]],
      title: ['']
    });

    this.itemForm = this.fb.group({
      category: [null, Validators.required],
      content: ['', Validators.required],
      related_institutions: [[]],
      solution_proposals: [''],
      display_order: [0]
    });

    this.reviewForm = this.fb.group({
      status: [ReportStatus.APPROVED, Validators.required],
      rejection_note: ['']
    });

    this.passDownForm = this.fb.group({
      extra_note: ['']
    });
  }

  loadReportData(id: number): void {
    this.loading = true;
    this.reportService.getReportById(id).subscribe({
      next: (report) => {
        this.reportData = report;
        
        const currentUser = this.authService.currentUserValue;
        if (currentUser) {
          const isAdmin = currentUser.role === 'ADMIN' || currentUser.is_superuser;
          this.isCreator = report.user_id === currentUser.id;
          
          this.canEditReportBase = this.isCreator || !!isAdmin;
          this.canAddRow = !this.isCreator; // Her zaman yeni satır eklenebilir, onaylansa bile
          this.canApproveReport = this.isCreator && report.status !== ReportStatus.APPROVED;
          this.canTransferReport = this.isCreator && report.status === ReportStatus.APPROVED;
          
          if (!this.canEditReportBase) {
            this.reportForm.disable();
          }
        }

        this.reportForm.patchValue({
          year: report.year,
          month: report.month,
          title: report.title
        });

        // Items are in report.items
        this.loading = false;
      },
      error: () => {
        this.loading = false;
        this.router.navigate(['/reports']);
      }
    });
  }

  onReportSubmit(): void {
    if (this.reportForm.invalid) return;

    this.loading = true;
    const formValue = this.reportForm.value;

    if (this.isEditMode && this.reportId) {
      this.reportService.updateReport(this.reportId, formValue).subscribe({
        next: (updated) => {
          this.loading = false;
          this.messageService.add({ severity: 'success', summary: 'Başarılı', detail: 'Rapor güncellendi' });
          this.loadReportData(this.reportId!);
        },
        error: () => { this.loading = false; }
      });
    } else {
      this.reportService.createReport(formValue).subscribe({
        next: (created) => {
          this.loading = false;
          this.messageService.add({ severity: 'success', summary: 'Başarılı', detail: 'Yeni rapor oluşturuldu' });
          this.router.navigate(['/reports', created.id]);
        },
        error: () => { this.loading = false; }
      });
    }
  }

  // ITEM CRUD
  openNewItemModal(): void {
    this.editingItemId = null;
    this.itemForm.reset({ display_order: 0 });
    this.displayItemModal = true;
  }

  openEditItemModal(item: ReportItem): void {
    this.editingItemId = item.id!;
    let parsedInstitutions: string[] = [];
    if (item.related_institutions) {
      parsedInstitutions = item.related_institutions.split(',').map(s => s.trim()).filter(s => s.length > 0);
    }
    this.itemForm.patchValue({
      category: item.category,
      content: item.content,
      related_institutions: parsedInstitutions,
      solution_proposals: item.solution_proposals,
      display_order: item.display_order
    });
    this.onCategoryChange();
    this.displayItemModal = true;
  }

  onCategoryChange(): void {
    const category = this.itemForm.get('category')?.value;
    const isKordinasyon = category === this.categoryKordinasyon;
    
    const relatedInstCtrl = this.itemForm.get('related_institutions');
    const solutionPropsCtrl = this.itemForm.get('solution_proposals');
    
    if (isKordinasyon) {
      relatedInstCtrl?.setValidators(Validators.required);
      solutionPropsCtrl?.setValidators(Validators.required);
    } else {
      relatedInstCtrl?.clearValidators();
      solutionPropsCtrl?.clearValidators();
    }
    
    relatedInstCtrl?.updateValueAndValidity();
    solutionPropsCtrl?.updateValueAndValidity();
  }

  saveItem(): void {
    if (this.itemForm.invalid || !this.reportId) return;

    this.loading = true;
    const val = { ...this.itemForm.value };
    
    // Check and stringify institutions array
    if (Array.isArray(val.related_institutions)) {
      val.related_institutions = val.related_institutions.join(', ');
    } else {
      val.related_institutions = val.related_institutions || '';
    }

    if (this.editingItemId) {
      this.reportService.updateReportItem(this.reportId, this.editingItemId, val).subscribe({
        next: () => {
          this.loading = false;
          this.displayItemModal = false;
          this.loadReportData(this.reportId!);
        },
        error: () => { this.loading = false; }
      });
    } else {
      this.reportService.addReportItem(this.reportId, val).subscribe({
        next: () => {
          this.loading = false;
          this.displayItemModal = false;
          this.loadReportData(this.reportId!);
        },
        error: () => { this.loading = false; }
      });
    }
  }

  deleteItem(itemId: number): void {
    if (!this.reportId || !confirm('Bu satırı silmek / rapordan çıkarmak istediğinize emin misiniz?')) return;
    this.loading = true;
    this.reportService.deleteReportItem(this.reportId, itemId).subscribe({
      next: () => {
        this.loading = false;
        this.loadReportData(this.reportId!);
      },
      error: () => { this.loading = false; }
    });
  }

  // REVIEW ITEM
  openReviewModal(item: ReportItem): void {
    this.reviewingItemId = item.id!;
    this.reviewForm.reset({ status: ReportStatus.APPROVED });
    this.displayReviewModal = true;
  }

  onReviewStatusChange(): void {
    const status = this.reviewForm.get('status')?.value;
    const noteCtrl = this.reviewForm.get('rejection_note');
    if (status === ReportStatus.REJECTED) {
      noteCtrl?.setValidators(Validators.required);
    } else {
      noteCtrl?.clearValidators();
    }
    noteCtrl?.updateValueAndValidity();
  }

  submitReview(): void {
    if (this.reviewForm.invalid || !this.reportId || !this.reviewingItemId) return;
    this.loading = true;
    this.reportService.reviewReportItem(this.reportId, this.reviewingItemId, this.reviewForm.value).subscribe({
      next: () => {
        this.loading = false;
        this.displayReviewModal = false;
        this.loadReportData(this.reportId!);
      },
      error: () => { this.loading = false; }
    });
  }

  // PASS DOWN REJECTION
  openPassDownModal(item: ReportItem): void {
    this.passingDownItemId = item.id!;
    this.passDownForm.reset();
    this.displayPassDownModal = true;
  }

  submitPassDown(): void {
    if (!this.reportId || !this.passingDownItemId) return;
    this.loading = true;
    const extraNote = this.passDownForm.get('extra_note')?.value || '';
    
    this.reportService.passDownRejection(this.reportId, this.passingDownItemId, extraNote).subscribe({
      next: () => {
        this.loading = false;
        this.displayPassDownModal = false;
        this.messageService.add({ severity: 'success', summary: 'Başarılı', detail: 'Red durumu alt personele başarıyla iletildi.' });
        this.loadReportData(this.reportId!);
      },
      error: () => { this.loading = false; }
    });
  }

  // APPROVE / TRANSFER REPORT
  approveFullReport(force: boolean = false): void {
    if (!this.reportId) return;
    if (!force && !confirm('Bu raporu tamamen onaylayıp kapatmak istediğinize emin misiniz?')) return;
    
    this.loading = true;
    this.reportService.approveReport(this.reportId, force).subscribe({
      next: () => {
        this.loading = false;
        this.messageService.add({ severity: 'success', summary: 'Başarılı', detail: 'Rapor tamamen onaylandı.' });
        this.loadReportData(this.reportId!);
      },
      error: (err) => {
        this.loading = false;
        // The backend throws 400 with missing_users if we didn't force and someone is missing
        if (err.error?.detail && err.error.detail.missing_users) {
          const missing = err.error.detail.missing_users.join(', ');
          if (confirm(`Aşağıdaki kişiler henüz rapor girmedi:\n${missing}\n\nYine de onaylamak istiyor musunuz?`)) {
            this.approveFullReport(true);
          }
        }
      }
    });
  }

  transferReport(): void {
    if (!this.reportId || !confirm('Bu raporu üst yöneticinizin ilgili ay/yıl raporuna aktarmak istediğinize emin misiniz?')) return;
    this.loading = true;
    this.reportService.transferReport(this.reportId).subscribe({
      next: (res) => {
        this.loading = false;
        this.messageService.add({ severity: 'success', summary: 'Aktarım Başarılı', detail: 'Rapor başarıyla üst yöneticiye aktarıldı.' });
        // You might want to navigate to the manager's report, but res is the manager's report so we can just redirect
        this.router.navigate(['/reports', res.id]);
      },
      error: () => { this.loading = false; }
    });
  }

  autoResize(element: any): void {
    const el = element as HTMLTextAreaElement;
    el.style.height = 'auto';
    el.style.height = el.scrollHeight + 'px';
  }

  goBack(): void {
    this.location.back();
  }
}
