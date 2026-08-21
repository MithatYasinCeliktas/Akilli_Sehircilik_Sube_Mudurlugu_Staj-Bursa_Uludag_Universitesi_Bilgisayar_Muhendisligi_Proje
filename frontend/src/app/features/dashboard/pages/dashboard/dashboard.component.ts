import { Component, OnInit } from '@angular/core';
import { AuthService } from '../../../../core/services/auth.service';
import { ReportService } from '../../../../core/services/report.service';
import { UserService } from '../../../../core/services/user.service';
import { User } from '../../../../core/models/user.model';
import { MessageService } from 'primeng/api';
import { Router } from '@angular/router';
import { ReportShareService } from '../../../../core/services/report-share.service';
import { ReportShareResponse } from '../../../../core/models/report-share.model';

@Component({
  selector: 'app-dashboard',
  templateUrl: './dashboard.component.html',
  providers: [MessageService]
})
export class DashboardComponent implements OnInit {
  currentUser: User | null = null;
  totalReports: number = 0;
  pendingReports: number = 0;
  approvedReports: number = 0;
  rejectedReports: number = 0;
  
  allReportsList: any[] = [];
  pendingReportsList: any[] = [];
  approvedReportsList: any[] = [];
  rejectedReportsList: any[] = [];
  
  displayReportsDialog: boolean = false;
  dialogTitle: string = '';
  selectedReports: any[] = [];
  
  displayRejectedPreview: boolean = false;
  selectedRejectedReport: any = null;
  
  myRecentReports: any[] = [];
  myRejectedReports: any[] = [];
  
  myRecentItems: any[] = [];
  myRejectedItems: any[] = [];
  
  pendingShares: ReportShareResponse[] = [];
  approvedShares: ReportShareResponse[] = [];
  myShares: ReportShareResponse[] = [];
  sharesLoading: boolean = false;
  mySharesLoading: boolean = false;
  approvedSharesLoading: boolean = false;
  
  // Filtreler
  filterYear: number | null = new Date().getFullYear();
  filterMonth: number | null = new Date().getMonth() + 1;
  
  get filterYearLabel(): string {
    const opt = this.yearOptions.find(o => o.value === this.filterYear);
    return opt ? opt.label : 'Yıl Seçiniz';
  }

  get filterMonthLabel(): string {
    const opt = this.monthOptions.find(o => o.value === this.filterMonth);
    return opt ? opt.label : 'Ay Seçiniz';
  }
  
  yearOptions = [
    { label: 'Tümü', value: null },
    { label: '2024', value: 2024 },
    { label: '2025', value: 2025 },
    { label: '2026', value: 2026 },
    { label: '2027', value: 2027 },
    { label: '2028', value: 2028 },
    { label: '2029', value: 2029 },
    { label: '2030', value: 2030 }
  ];

  monthOptions = [
    { label: 'Tümü', value: null },
    { label: '1 - Ocak', value: 1 },
    { label: '2 - Şubat', value: 2 },
    { label: '3 - Mart', value: 3 },
    { label: '4 - Nisan', value: 4 },
    { label: '5 - Mayıs', value: 5 },
    { label: '6 - Haziran', value: 6 },
    { label: '7 - Temmuz', value: 7 },
    { label: '8 - Ağustos', value: 8 },
    { label: '9 - Eylül', value: 9 },
    { label: '10 - Ekim', value: 10 },
    { label: '11 - Kasım', value: 11 },
    { label: '12 - Aralık', value: 12 }
  ];
  

  loading: boolean = true;

  constructor(
    private authService: AuthService,
    private reportService: ReportService,
    private userService: UserService,
    private messageService: MessageService,
    private router: Router,
    private reportShareService: ReportShareService
  ) {}

  ngOnInit(): void {
    this.currentUser = this.authService.currentUserValue;
    this.loadStats();
    this.loadPendingShares();
    this.loadApprovedShares();
    this.loadMyShares();
  }

  loadPendingShares(): void {
    if (!this.currentUser || (!this.currentUser.is_superuser && this.currentUser.role !== 'ADMIN' && this.currentUser.role !== 'MANAGER')) {
      // Sadece yöneticiler ve adminler görebilir
      return;
    }
    this.sharesLoading = true;
    this.reportShareService.getPendingShares().subscribe({
      next: (shares) => {
        this.pendingShares = shares;
        this.applyLocalFiltersToShares();
        this.sharesLoading = false;
      },
      error: () => {
        this.sharesLoading = false;
      }
    });
  }

  approveShare(shareId: number): void {
    this.reportShareService.approveShare(shareId).subscribe({
      next: () => {
        this.messageService.add({severity: 'success', summary: 'Onaylandı', detail: 'Paylaşım isteği onaylandı.'});
        this.loadPendingShares();
      }
    });
  }

  rejectShare(shareId: number): void {
    const note = prompt("Reddetme nedeninizi girin (Opsiyonel):");
    if (note === null) return; // İptal edildi
    
    this.reportShareService.rejectShare(shareId, { note }).subscribe({
      next: () => {
        this.messageService.add({severity: 'info', summary: 'Reddedildi', detail: 'Paylaşım isteği reddedildi.'});
        this.loadPendingShares();
      }
    });
  }

  
  loadMyShares(): void {
    this.mySharesLoading = true;
    this.reportShareService.getMyShares().subscribe({
      next: (shares) => {
        this.myShares = shares;
        this.applyLocalFiltersToShares();
        this.mySharesLoading = false;
      },
      error: () => {
        this.mySharesLoading = false;
      }
    });
  }

  loadApprovedShares(): void {
    if (!this.currentUser || (!this.currentUser.is_superuser && this.currentUser.role !== 'ADMIN' && this.currentUser.role !== 'MANAGER')) {
      return;
    }
    this.approvedSharesLoading = true;
    this.reportShareService.getApprovedShares().subscribe({
      next: (shares) => {
        this.approvedShares = shares;
        this.applyLocalFiltersToShares();
        this.approvedSharesLoading = false;
      },
      error: () => {
        this.approvedSharesLoading = false;
      }
    });
  }

  filteredPendingShares: ReportShareResponse[] = [];
  filteredApprovedShares: ReportShareResponse[] = [];
  filteredMyShares: ReportShareResponse[] = [];

  /**
   * Paylaşımları yerel olarak (frontend üzerinde) filtreler.
   * Bu fonksiyon Genel Bakış sayfasındaki Yıl ve Ay filtrelerine göre, 
   * Onay Bekleyen ve Onaylanmış paylaşımları anlık olarak süzer.
   * Backend tarafındaki paylaşımlar toplu getirildiği için performans açısından
   * filtreleme işlemi burada yapılmıştır.
   */
  private applyLocalFiltersToShares(): void {
    
    this.filteredMyShares = this.myShares.filter(share => {
      const matchYear = this.filterYear ? share.report?.year === this.filterYear : true;
      const matchMonth = this.filterMonth ? share.report?.month === this.filterMonth : true;
      return matchYear && matchMonth;
    });

    this.filteredPendingShares = this.pendingShares.filter(share => {
      const matchYear = this.filterYear ? share.report?.year === this.filterYear : true;
      const matchMonth = this.filterMonth ? share.report?.month === this.filterMonth : true;
      return matchYear && matchMonth;
    });
    
    this.filteredApprovedShares = this.approvedShares.filter(share => {
      const matchYear = this.filterYear ? share.report?.year === this.filterYear : true;
      const matchMonth = this.filterMonth ? share.report?.month === this.filterMonth : true;
      return matchYear && matchMonth;
    });
  }

  revokeShare(shareId: number): void {
    if (confirm("Bu paylaşım yetkisini geri almak (iptal etmek) istediğinize emin misiniz?")) {
      this.reportShareService.revokeShare(shareId).subscribe({
        next: () => {
          this.messageService.add({severity: 'info', summary: 'İptal Edildi', detail: 'Paylaşım yetkisi geri alındı.'});
          this.loadApprovedShares();
    this.loadMyShares();
        }
      });
    }
  }


  loadStats(): void {
    this.loading = true;
    
    // 1. Ay/Yıl filtresine göre istatistikleri getir
    this.reportService.getReports({ page: 1, pageSize: 1000, year: this.filterYear ?? undefined, month: this.filterMonth ?? undefined }).subscribe({
      next: (data) => {
        this.allReportsList = data.items || [];
        this.pendingReportsList = this.allReportsList.filter(r => r.status === 'PENDING');
        this.approvedReportsList = this.allReportsList.filter(r => r.status === 'APPROVED');
        this.rejectedReportsList = this.allReportsList.filter(r => r.status === 'REJECTED');
        
        if (this.currentUser) {
          this.loadMyRecentReports();
        }

        this.totalReports = data.total;
        this.pendingReports = this.pendingReportsList.length;
        this.approvedReports = this.approvedReportsList.length;
        this.rejectedReports = this.rejectedReportsList.length;
        
        this.loadMyRejectedReports();
        this.applyLocalFiltersToShares();
      },
      error: () => {
        this.loading = false;
      }
    });
  }

  loadMyRejectedReports(): void {
    if (!this.currentUser) {
      this.loading = false;
      return;
    }
    
    const filterParams: any = { page: 1, pageSize: 100 };
    if (this.currentUser.role === 'ADMIN' || this.currentUser.role === 'MANAGER' || this.currentUser.role === 'USER_MANAGER') {
      filterParams.userIds = [this.currentUser.id];
      filterParams.status = 'REJECTED';
    }

    this.reportService.getReports(filterParams).subscribe({
      next: (data) => {
        if (this.currentUser?.role === 'ADMIN' || this.currentUser?.role === 'MANAGER' || this.currentUser?.role === 'USER_MANAGER') {
          this.myRejectedReports = data.items || [];
        } else {
          this.myRejectedItems = [];
          (data.items || []).forEach(report => {
            if (([...(report.yapilan_isler || []), ...(report.yapilacak_isler || []), ...(report.koordinasyon_isleri || [])])) {
              const rejectedItems = ([...(report.yapilan_isler || []), ...(report.yapilacak_isler || []), ...(report.koordinasyon_isleri || [])]).filter((item: any) => item.creator_id === this.currentUser?.id && item.status === 'REJECTED');
              rejectedItems.forEach((item: any) => {
                this.myRejectedItems.push({
                  ...item,
                  report_month: report.month,
                  report_year: report.year,
                  report_id: report.id
                });
              });
            }
          });
        }
        this.loading = false;
      },
      error: () => {
        this.loading = false;
      }
    });
  }

  loadMyRecentReports(): void {
    if (!this.currentUser) return;
    
    const filterParams: any = {
      page: 1, 
      pageSize: 100, 
      year: this.filterYear ?? undefined,
      month: this.filterMonth ?? undefined
    };
    
    if (this.currentUser.role === 'ADMIN' || this.currentUser.role === 'MANAGER' || this.currentUser.role === 'USER_MANAGER') {
      filterParams.userIds = [this.currentUser.id];
    }
    
    this.reportService.getReports(filterParams).subscribe({
      next: (data) => {
        if (this.currentUser?.role === 'ADMIN' || this.currentUser?.role === 'MANAGER' || this.currentUser?.role === 'USER_MANAGER') {
          this.myRecentReports = data.items || [];
        } else {
          this.myRecentItems = [];
          (data.items || []).forEach(report => {
            if (([...(report.yapilan_isler || []), ...(report.yapilacak_isler || []), ...(report.koordinasyon_isleri || [])])) {
              const userItems = ([...(report.yapilan_isler || []), ...(report.yapilacak_isler || []), ...(report.koordinasyon_isleri || [])]).filter((item: any) => item.creator_id === this.currentUser?.id);
              userItems.forEach((item: any) => {
                this.myRecentItems.push({
                  ...item,
                  report_month: report.month,
                  report_year: report.year,
                  report_id: report.id
                });
              });
            }
          });
        }
      },
      error: () => {}
    });
  }

  onFilterChange(): void {
    this.loadStats();
  }

  showReports(type: 'total' | 'pending' | 'approved' | 'rejected'): void {
    if (type === 'total') {
      this.selectedReports = this.allReportsList;
      this.dialogTitle = 'Tüm Raporlar';
    } else if (type === 'pending') {
      this.selectedReports = this.pendingReportsList;
      this.dialogTitle = 'Onay Bekleyen Raporlar';
    } else if (type === 'approved') {
      this.selectedReports = this.approvedReportsList;
      this.dialogTitle = 'Onaylanan Raporlar';
    } else if (type === 'rejected') {
      this.selectedReports = this.rejectedReportsList;
      this.dialogTitle = 'Reddedilen Raporlar';
    }
    this.displayReportsDialog = true;
  }

  showRejectedPreview(report: any): void {
    this.selectedRejectedReport = report;
    this.displayRejectedPreview = true;
  }

  editReport(id: number): void {
    this.router.navigate(['/reports', id]);
  }
  

}