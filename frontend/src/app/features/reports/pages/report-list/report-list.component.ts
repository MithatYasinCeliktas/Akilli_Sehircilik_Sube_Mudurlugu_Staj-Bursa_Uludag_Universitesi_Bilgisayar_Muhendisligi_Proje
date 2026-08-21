import { Component, OnInit } from '@angular/core';
import { Router, ActivatedRoute } from '@angular/router';
import { ReportService } from '../../../../core/services/report.service';
import { UserService } from '../../../../core/services/user.service';
import { AuthService } from '../../../../core/services/auth.service';
import { ActivityReport, ReportFilter, ReportStatus } from '../../../../core/models/report.model';
import { TreeNode, MessageService } from 'primeng/api';
import { ReportShareService } from '../../../../core/services/report-share.service';
import { ReportShareResponse } from '../../../../core/models/report-share.model';
import { DialogService, DynamicDialogRef } from 'primeng/dynamicdialog';
import { ImportExcelDialogComponent } from '../../components/import-excel-dialog/import-excel-dialog.component';
import { SettingsService } from '../../../../core/services/settings.service';
import { InstitutionService } from '../../../../core/services/institution.service';

@Component({
  selector: 'app-report-list',
  templateUrl: './report-list.component.html',
  providers: [DialogService, MessageService]
})
export class ReportListComponent implements OnInit {
  reports: ActivityReport[] = [];
  totalRecords: number = 0;
  loading: boolean = true;
  canCreateReport: boolean = false;
  currentUserId: number | null = null;
  managerId: number | null = null;
  isAdmin: boolean = false;
  isManager: boolean = false;
  hasManager: boolean = false;
  canImportExcel: boolean = false;

  tabs: { id: string, label: string, icon: string }[] = [];
  activeTabId: string = '';
  activeTabIndex: number = 0;

  sharedReports: ReportShareResponse[] = [];
  selectedSharedReports: ReportShareResponse[] = [];
  sharedLoading: boolean = false;

  filter: ReportFilter = {
    page: 1,
    pageSize: 10
  };
  tempPageSize: number = 10;

  selectedReports: ActivityReport[] = [];

  selectedUnitItems: any[] = [];
  displayMergeItemsDialog: boolean = false;
  mergeItemsTitle: string = '';

  dateRange: Date[] | undefined;

  statusOptions = [
    { label: 'Tümü', value: null },
    { label: 'Onay Bekliyor', value: ReportStatus.PENDING },
    { label: 'Onaylandı', value: ReportStatus.APPROVED },
    { label: 'Reddedildi', value: ReportStatus.REJECTED }
  ];

  categoryTypeOptions = [
    { label: 'Tümü', value: null },
    { label: 'Yapılan İşler', value: 'YAPILAN_ISLER' },
    { label: 'Yapılacak İşler', value: 'YAPILACAK_ISLER' },
    { label: 'Koordinasyon Gerektiren İşler', value: 'KORDINASYON_GEREKTIREN_ISLER' }
  ];

  selectedCategoryType: string | null = null;

  get filterStatusLabel(): string {
    const opt = this.statusOptions.find(o => o.value === (this.filter.status ?? null));
    return opt ? opt.label : 'Durum Seçin';
  }

  setStatusFilter(value: any): void {
    this.filter.status = value === null ? undefined : value;
    this.onFilterChange();
  }

  userTree: TreeNode[] = [];
  selectedUserNodes: TreeNode[] = [];

  importDialogRef: DynamicDialogRef | undefined;

  unitReportYapilan: any[] = [];
  unitReportYapilacak: any[] = [];
  unitReportKoordinasyon: any[] = [];
  selectedUnitYapilan: any[] = [];
  selectedUnitYapilacak: any[] = [];
  selectedUnitKoordinasyon: any[] = [];
  unitReportItemsTotal: number = 0;
  selectedSubordinates: number[] = [];
  selectedInstitutions: string[] = [];
  subordinateOptions: any[] = [];
  institutionOptions: any[] = [];

  constructor(
    private reportService: ReportService,
    private userService: UserService,
    private reportShareService: ReportShareService,
    private authService: AuthService,
    private router: Router,
    private route: ActivatedRoute,
    private dialogService: DialogService,
    private messageService: MessageService,
    private settingsService: SettingsService,
    private institutionService: InstitutionService
  ) {}

  // Fuzzy matching helper
  private getLevenshteinDistance(a: string, b: string): number {
      if (a.length === 0) return b.length;
      if (b.length === 0) return a.length;
      const matrix = [];
      for (let i = 0; i <= b.length; i++) {
          matrix[i] = [i];
      }
      for (let j = 0; j <= a.length; j++) {
          matrix[0][j] = j;
      }
      for (let i = 1; i <= b.length; i++) {
          for (let j = 1; j <= a.length; j++) {
              if (b.charAt(i - 1) === a.charAt(j - 1)) {
                  matrix[i][j] = matrix[i - 1][j - 1];
              } else {
                  matrix[i][j] = Math.min(
                      matrix[i - 1][j - 1] + 1,
                      Math.min(matrix[i][j - 1] + 1, matrix[i - 1][j] + 1)
                  );
              }
          }
      }
      return matrix[b.length][a.length];
  }

  ngOnInit(): void {
    this.authService.currentUser$.subscribe(user => {
      if (user) {
        this.currentUserId = user.id;
        this.managerId = user.manager_id || null;
        this.hasManager = !!this.managerId;
        this.isAdmin = user.role === 'ADMIN' || !!user.is_superuser;
        this.isManager = user.role === 'MANAGER' || user.role === 'USER_MANAGER';
        // MANAGER, USER_MANAGER, or ADMIN can create reports
        this.canCreateReport = user.role === 'ADMIN' || user.role === 'USER_MANAGER' || user.role === 'MANAGER';
        this.canImportExcel = this.canCreateReport || this.hasManager;
        
        // Initialize Tabs based on roles
        this.tabs = [];
        if (this.canCreateReport) {
            this.tabs.push({ id: 'my', label: 'Kendi Raporlarım', icon: 'pi-user' });
            if (user.role === 'MANAGER' || user.role === 'USER_MANAGER' || user.role === 'ADMIN') {
                this.tabs.push({ id: 'unit', label: 'Birim Raporları', icon: 'pi-sitemap' });
            }
        }
        if (this.hasManager) {
            this.tabs.push({ id: 'manager', label: 'Yöneticimin Raporları', icon: 'pi-users' });
        }
        

        if (this.isAdmin) {
            this.tabs.push({ id: 'all', label: 'Tüm Raporlar', icon: 'pi-globe' });
        }
        this.tabs.push({ id: 'shared', label: 'Benimle Paylaşılanlar', icon: 'pi-share-alt' });

        this.loadUsers();
        this.loadInstitutions();
        this.loadSharedReports();
        
        // Default load will be handled if needed, but onTabChange will trigger if we manually call it, 
        // actually p-tabView selects index 0 initially which doesn't always fire onChange for the first load.
        // So we manually initialize the first tab's filter.
        
        this.route.queryParams.subscribe(params => {
          const tabId = params['tab'];
          if (this.tabs.length > 0) {
            let targetIndex = 0;
            if (tabId) {
              const foundIndex = this.tabs.findIndex(t => t.id === tabId);
              if (foundIndex !== -1) {
                targetIndex = foundIndex;
              }
            }
            this.activeTabIndex = targetIndex;
            this.applyTabFilter(this.tabs[targetIndex].id);
            
            const activeId = this.tabs[targetIndex].id;
            if (activeId === 'unit') {
               this.loadUnitReports();
            } else if (activeId !== 'shared') {
               this.loadReports();
            }
          }
          
          if (params['showProposals'] === 'true') {
            setTimeout(() => {
              this.openProposalsDialog();
            }, 500);
          }
        });
        
        // Listen to Chatbot filter triggers
        this.settingsService.filterReports$.subscribe((filterData) => {
           const today = new Date();
           let dateRangeUpdated = false;

           // Chatbot'tan yeni bir istek geldiğinde belirtilmeyen tüm filtreleri temizle
           if (Object.keys(filterData).length > 0) {
               this.filter.year = undefined;
               this.filter.month = undefined;
               this.filter.status = undefined;
               this.filter.searchText = undefined;
               this.dateRange = undefined;
               this.filter.startDate = undefined;
               this.filter.endDate = undefined;
               this.selectedSubordinates = [];
               this.selectedInstitutions = [];
           }
           
           if (filterData.searchText) {
               const searchLower = filterData.searchText.toLocaleLowerCase('tr-TR');
               const matchedSubordinates: any[] = [];
               let remainingSearch = searchLower;
               
               if (this.activeTabId === 'unit' && this.subordinateOptions && this.subordinateOptions.length > 0) {
                   let searchWords = searchLower.split(/\s+/).filter(w => w.length > 2);
                   
                   // 1. Try exact or full name inclusions first
                   this.subordinateOptions.forEach(opt => {
                       const labelLower = opt.label.toLocaleLowerCase('tr-TR');
                       if (searchLower.includes(labelLower)) {
                           if (!matchedSubordinates.includes(opt.value)) {
                               matchedSubordinates.push(opt.value);
                               remainingSearch = remainingSearch.replace(labelLower, ' ').trim();
                               searchWords = remainingSearch.split(/\s+/).filter(w => w.length > 2);
                           }
                       }
                   });
                   
                   // 2. Try word-by-word matching for the remaining search words (including fuzzy match)
                   if (searchWords.length > 0) {
                       this.subordinateOptions.forEach(opt => {
                           if (matchedSubordinates.includes(opt.value)) return;
                           
                           const labelLower = opt.label.toLocaleLowerCase('tr-TR');
                           const matchedWord = searchWords.find(w => {
                               if (labelLower.includes(w)) return true;
                               // Fuzzy match: if word > 4 chars and levenshtein distance <= 2 against any label word
                               if (w.length > 4) {
                                   const lWords = labelLower.split(/\s+/).filter((lw: string) => lw.length > 4);
                                   for (const lw of lWords) {
                                       if (this.getLevenshteinDistance(w, lw) <= 2) return true;
                                   }
                               }
                               return false;
                           });
                           
                           if (matchedWord) {
                               matchedSubordinates.push(opt.value);
                               remainingSearch = remainingSearch.replace(matchedWord, ' ').trim();
                               searchWords = remainingSearch.split(/\s+/).filter(w => w.length > 2);
                           }
                       });
                   }
               }
               
               if (matchedSubordinates.length > 0) {
                   this.selectedSubordinates = matchedSubordinates;
                   
                   // Clean up leftover conjunctions like "ve", "ile"
                   remainingSearch = remainingSearch.replace(/\b(ve|ile)\b/g, ' ').trim();
                   remainingSearch = remainingSearch.replace(/\s+/g, ' ').trim();
               }
               
               // --- Institution Matching ---
               if (this.activeTabId === 'unit' && this.institutionOptions && this.institutionOptions.length > 0) {
                   const matchedInstitutions: any[] = [];
                   let searchWords = remainingSearch.split(/\s+/).filter(w => w.length > 2);
                   
                   // 1. Try exact or full name inclusions first
                   this.institutionOptions.forEach(opt => {
                       const labelLower = opt.label.toLocaleLowerCase('tr-TR');
                       if (remainingSearch.includes(labelLower)) {
                           if (!matchedInstitutions.includes(opt.value)) {
                               matchedInstitutions.push(opt.value);
                               remainingSearch = remainingSearch.replace(labelLower, ' ').trim();
                               searchWords = remainingSearch.split(/\s+/).filter(w => w.length > 2);
                           }
                       }
                   });
                   
                   // 2. Try word-by-word matching for the remaining search words (including fuzzy match)
                   if (searchWords.length > 0) {
                       this.institutionOptions.forEach(opt => {
                           if (matchedInstitutions.includes(opt.value)) return;
                           
                           const labelLower = opt.label.toLocaleLowerCase('tr-TR');
                           const matchedWord = searchWords.find(w => {
                               if (labelLower.includes(w)) return true;
                               // Fuzzy match
                               if (w.length > 4) {
                                   const lWords = labelLower.split(/\s+/).filter((lw: string) => lw.length > 4);
                                   for (const lw of lWords) {
                                       if (this.getLevenshteinDistance(w, lw) <= 2) return true;
                                   }
                               }
                               return false;
                           });
                           
                           if (matchedWord) {
                               matchedInstitutions.push(opt.value);
                               remainingSearch = remainingSearch.replace(matchedWord, ' ').trim();
                               searchWords = remainingSearch.split(/\s+/).filter(w => w.length > 2);
                           }
                       });
                   }
                   
                   if (matchedInstitutions.length > 0) {
                       this.selectedInstitutions = matchedInstitutions;
                       
                       // Clean up leftover conjunctions again
                       remainingSearch = remainingSearch.replace(/\b(ve|ile)\b/g, ' ').trim();
                       remainingSearch = remainingSearch.replace(/\s+/g, ' ').trim();
                   }
               }
               
               // Final remaining search text
               if (remainingSearch.length >= 2) {
                   this.filter.searchText = remainingSearch;
               } else {
                   this.filter.searchText = undefined;
               }
           }

           if (filterData.startDate && filterData.endDate) {
                 const start = new Date(filterData.startDate);
                 const end = new Date(filterData.endDate);
                 this.dateRange = [start, end];
                 this.filter.startDate = filterData.startDate;
                 this.filter.endDate = filterData.endDate;
                 dateRangeUpdated = true;
           } else if (filterData.recent) {
                 const days = parseInt(filterData.recent) || 30;
                 const pastDate = new Date();
                 pastDate.setDate(today.getDate() - days);
                 if (days === 1) { // yesterday
                     this.dateRange = [pastDate, pastDate];
                     this.filter.startDate = this.formatDate(pastDate);
                     this.filter.endDate = this.formatDate(pastDate);
                 } else { // past X days
                     this.dateRange = [pastDate, today];
                     this.filter.startDate = this.formatDate(pastDate);
                     this.filter.endDate = this.formatDate(today);
                 }
                 dateRangeUpdated = true;
             }

           if (filterData.year) {
               this.filter.year = parseInt(filterData.year);
           }

           if (filterData.month) {
               this.filter.month = parseInt(filterData.month);
           }
           
           if (filterData.status !== undefined) {
               this.filter.status = filterData.status as ReportStatus;
           }
           
           if (Object.keys(filterData).length > 0) {
               this.onFilterChange();
           }
        });
      }
    });
  }

  onTabChange(event: any): void {
    const tabId = this.tabs[event.index].id;
    this.activeTabId = tabId;
    this.filter.page = 1;

    // Apply filters based on tab
    this.applyTabFilter(tabId);

    // Load data based on tab
    if (tabId === 'unit') {
        this.loadUnitReports();
    } else if (tabId === 'shared') {
        this.loadSharedReports();
    } else {
        this.loadReports();
    }
    
    // Update URL without triggering navigation
    this.router.navigate([], {
        relativeTo: this.route,
        queryParams: { tab: this.activeTabId },
        queryParamsHandling: 'merge',
    });
  }

  private applyTabFilter(tabId: string): void {
     this.activeTabId = tabId;
     if (tabId === 'my') {
         this.filter.userIds = [this.currentUserId!];
     } else if (tabId === 'manager') {
         this.filter.userIds = [this.managerId!];

     } else if (tabId === 'all') {
         // Don't override userIds if they used the TreeSelect
         this.onFilterChange();
         return; 
     }
  }

  loadSharedReports(): void {
    this.sharedLoading = true;
    this.reportShareService.getSharedWithMe().subscribe({
      next: (res) => {
        this.sharedReports = res;
        this.sharedLoading = false;
      },
      error: () => {
        this.sharedLoading = false;
      }
    });
  }

  loadUsers(): void {
    this.userService.getUsers(1, 1000).subscribe({
      next: (res) => {
        const users = res.items || [];
        
        const userMap = new Map<number, TreeNode>();
        this.subordinateOptions = [];
        
        // İlk geçiş: Bütün düğümleri oluştur
        users.forEach(u => {
          userMap.set(u.id, {
            key: u.id.toString(),
            label: u.full_name || u.email,
            data: u.id,
            children: [],
            expanded: false
          });

          // Check if this user is a subordinate of the current manager
          if (u.manager_id === this.currentUserId || (u.manager && u.manager.id === this.currentUserId)) {
            this.subordinateOptions.push({
              label: u.full_name || u.email,
              value: u.id
            });
          }
        });

        // (The 'unit' tab is now added synchronously in ngOnInit)

        // İkinci geçiş: Ağacı bağla
        const treeNodes: TreeNode[] = [];
        const noManagerGroup: TreeNode = { 
          key: 'no-manager',
          label: 'Diğer / Yöneticisi Olmayanlar', 
          data: null, 
          children: [],
          expanded: false
        };

        users.forEach(u => {
          const node = userMap.get(u.id)!;
          const managerId = u.manager_id || (u.manager ? u.manager.id : null);
          
          if (managerId && userMap.has(managerId)) {
            userMap.get(managerId)!.children!.push(node);
          } else {
            if (managerId) {
               noManagerGroup.children!.push(node);
            } else {
               treeNodes.push(node); 
            }
          }
        });

        if (noManagerGroup.children!.length > 0) {
          treeNodes.push(noManagerGroup);
        }

        this.userTree = treeNodes;
      }
    });
  }

  loadInstitutions(): void {
    this.institutionService.getInstitutions(true).subscribe({
      next: (institutions) => {
        this.institutionOptions = institutions.map(inst => ({
          label: inst.name,
          value: inst.name
        }));
      },
      error: () => {
        console.error("Kurumlar yüklenemedi.");
      }
    });
  }

  onDateChange(): void {
    if (this.dateRange && this.dateRange.length > 0) {
      this.filter.startDate = this.dateRange[0] ? this.formatDate(this.dateRange[0]) : undefined;
      this.filter.endDate = this.dateRange[1] ? this.formatDate(this.dateRange[1]) : undefined;
    } else {
      this.filter.startDate = undefined;
      this.filter.endDate = undefined;
    }
    this.onFilterChange();
  }

  private formatDate(date: Date): string {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  }

  loadReports(): void {
    this.loading = true;
    this.reportService.getReports(this.filter).subscribe({
      next: (data) => {
        this.reports = data.items;
        this.totalRecords = data.total;
        this.loading = false;
      },
      error: () => {
        this.loading = false;
      }
    });
  }

  goToReportItem(item: any): void {
    if (item && item.report_id && item.id) {
      this.router.navigate(['/reports', item.report_id], { queryParams: { itemId: item.id } });
    }
  }

  loadUnitReports(): void {
    this.loading = true;
    const params: any = {
      page: this.filter.page,
      page_size: this.filter.pageSize,
      year: this.filter.year,
      month: this.filter.month,
      status: this.filter.status,
      search_text: this.filter.searchText,
      start_date: this.filter.startDate,
      end_date: this.filter.endDate,
    };
    if (this.selectedSubordinates && this.selectedSubordinates.length > 0) {
       params.creator_ids = this.selectedSubordinates;
    }
    if (this.selectedInstitutions && this.selectedInstitutions.length > 0) {
       params.institutions = this.selectedInstitutions;
    }

    this.reportService.getUnitReportItems(params).subscribe({
      next: (data) => {
        const items = data.items || [];
        this.unitReportYapilan = items.filter((i: any) => i.category === 'YAPILAN_ISLER');
        this.unitReportYapilacak = items.filter((i: any) => i.category === 'YAPILACAK_ISLER');
        this.unitReportKoordinasyon = items.filter((i: any) => i.category === 'KORDINASYON_GEREKTIREN_ISLER');
        this.unitReportItemsTotal = data.total || 0;
        this.loading = false;
      },
      error: () => {
        this.loading = false;
      }
    });
  }

  onPageChange(event: any): void {
    this.filter.page = (event.first / event.rows) + 1;
    this.filter.pageSize = event.rows;
    if (this.activeTabId === 'unit') {
      this.loadUnitReports();
    } else {
      this.loadReports();
    }
  }

  onFilterChange(): void {
    if (this.tempPageSize && this.tempPageSize >= 5) {
      this.filter.pageSize = this.tempPageSize;
    }

    if (this.activeTabId === 'all') {
        if (this.selectedUserNodes && this.selectedUserNodes.length > 0) {
           this.filter.userIds = this.selectedUserNodes.filter(n => n.data !== null).map(n => n.data);
        } else {
           this.filter.userIds = undefined;
        }
    } else if (this.activeTabId === 'my') {
        this.filter.userIds = [this.currentUserId!];
    } else if (this.activeTabId === 'manager') {
        this.filter.userIds = [this.managerId!];
    }

    this.filter.page = 1;
    if (this.activeTabId === 'unit') {
        this.loadUnitReports();
    } else if (this.activeTabId !== 'shared') {
        this.loadReports();
    }
  }

  selectWithTeam(event: Event, node: TreeNode): void {
    event.stopPropagation();
    
    if (this.isNodeAndChildrenSelected(node)) {
      this.removeNodeAndChildren(node);
    } else {
      this.addNodeAndChildren(node);
    }
    
    // Update the array reference so p-treeSelect detects the change
    this.selectedUserNodes = [...this.selectedUserNodes];
    this.onFilterChange();
  }

  private isNodeAndChildrenSelected(node: TreeNode): boolean {
    if (node.data !== null && !this.selectedUserNodes.find(n => n.key === node.key)) {
      return false;
    }
    if (node.children) {
      for (const child of node.children) {
        if (!this.isNodeAndChildrenSelected(child)) {
          return false;
        }
      }
    }
    return true;
  }

  private addNodeAndChildren(node: TreeNode): void {
    if (node.data !== null) {
      if (!this.selectedUserNodes.find(n => n.key === node.key)) {
         this.selectedUserNodes.push(node);
      }
    }
    
    if (node.children) {
      node.children.forEach(child => this.addNodeAndChildren(child));
    }
  }

  private removeNodeAndChildren(node: TreeNode): void {
    if (node.data !== null) {
      this.selectedUserNodes = this.selectedUserNodes.filter(n => n.key !== node.key);
    }
    
    if (node.children) {
      node.children.forEach(child => this.removeNodeAndChildren(child));
    }
  }

  applyPageSize(): void {
    if (this.tempPageSize && this.tempPageSize >= 5) {
      this.filter.pageSize = this.tempPageSize;
      this.onFilterChange();
    }
  }

  createReport(): void {
    this.router.navigate(['/reports/new']);
  }

  editReport(id: number): void {
    this.router.navigate(['/reports', id]);
  }

  shareReport(id: number): void {
    // Save the report ID to localStorage so the unit-list component knows what we are sharing
    localStorage.setItem('share_report_id', id.toString());
    this.router.navigate(['/units'], { queryParams: { mode: 'share' } });
  }

  canShareReport(report: any): boolean {
    if (this.isAdmin) return true;
    
    const currentUser = this.authService.currentUserValue;
    // Yönetici olsanız dahi, KENDİ yöneticinizin (bir üst makamın) raporunu paylaşamazsınız.
    if (currentUser && (report.user_id === currentUser.manager_id || report.userId === currentUser.manager_id)) {
      return false;
    }

    const role = currentUser?.role;
    if (role === 'MANAGER' || role === 'USER_MANAGER') return true;
    
    // Astlar (USER), yöneticilerinin oluşturduğu (kendi oluşturmadıkları) raporları paylaşamazlar.
    // Başkasının (yöneticisinin) raporlar sekmesinde de paylaşma butonu çıkmamalı.
    return report.creator_id === this.currentUserId;
  }

  
  mergeDialogVisible: boolean = false;
  mergeTitle: string = '';
  mergeLoading: boolean = false;


  openMergeItemsDialog() {
    const allSelectedUnitItems = [...(this.selectedUnitYapilan || []), ...(this.selectedUnitYapilacak || []), ...(this.selectedUnitKoordinasyon || [])];
      if (allSelectedUnitItems.length < 2) {
      this.messageService.add({ severity: 'warn', summary: 'Uyarı', detail: 'Birleştirmek için en az 2 satır seçmelisiniz.' });
      return;
    }
    const dateStr = new Date().toISOString().split('T')[0];
    this.mergeItemsTitle = `Birim_${dateStr}`;
    this.displayMergeItemsDialog = true;
  }

  confirmMergeItems() {
    const ids = this.selectedUnitItems.map(i => i.id);
    const title = this.mergeItemsTitle.trim() || undefined;

    this.reportService.mergeItems(ids, title).subscribe({
      next: () => {
        this.messageService.add({ severity: 'success', summary: 'Başarılı', detail: 'Seçilen satırlar yeni bir rapor olarak birleştirildi.' });
        this.displayMergeItemsDialog = false;
        this.selectedUnitYapilan = [];
            this.selectedUnitYapilacak = [];
            this.selectedUnitKoordinasyon = [];
        this.loadUnitReports();
      },
      error: (err: any) => {
        this.messageService.add({ severity: 'error', summary: 'Hata', detail: 'Satırlar birleştirilirken hata oluştu.' });
      }
    });
  }

  openMergeDialog(): void {
    if (this.activeTabId === 'unit') {
      const allSelectedUnitItems = [...(this.selectedUnitYapilan || []), ...(this.selectedUnitYapilacak || []), ...(this.selectedUnitKoordinasyon || [])];
      if (allSelectedUnitItems.length < 2) {
        this.messageService.add({severity: 'warn', summary: 'Uyarı', detail: 'Birleştirmek için en az 2 satır seçmelisiniz.'});
        return;
      }
    } else {
      if (!this.selectedReports || this.selectedReports.length < 2) {
        this.messageService.add({severity: 'warn', summary: 'Uyarı', detail: 'Birleştirmek için en az 2 rapor seçmelisiniz.'});
        return;
      }
    }
    this.mergeTitle = '';
    this.mergeDialogVisible = true;
  }

  confirmMerge(): void {
    let title = this.mergeTitle.trim();
    if (!title) {
        const unitName = this.authService.currentUserValue?.unit?.name || 'Birim';
        const dateStr = new Date().toLocaleDateString('tr-TR').replace(/\./g, '-');
        title = `${unitName}_${dateStr}`;
    }

    this.mergeLoading = true;
    
    if (this.activeTabId === 'unit') {
        const allSelectedUnitItems = [...(this.selectedUnitYapilan || []), ...(this.selectedUnitYapilacak || []), ...(this.selectedUnitKoordinasyon || [])];
        const ids = allSelectedUnitItems.map((r: any) => r.id);
        this.reportService.mergeItems(ids, title).subscribe({
          next: () => {
            this.messageService.add({severity: 'success', summary: 'Başarılı', detail: 'Satırlar başarıyla yeni raporda birleştirildi.'});
            this.mergeDialogVisible = false;
            this.mergeLoading = false;
            this.selectedUnitYapilan = [];
            this.selectedUnitYapilacak = [];
            this.selectedUnitKoordinasyon = [];
            // Maybe refresh reports list
            this.loadReports();
          },
          error: () => {
            this.mergeLoading = false;
          }
        });
    } else {
        const ids = this.selectedReports.map(r => r.id);
        this.reportService.mergeReports(ids, title).subscribe({
          next: () => {
            this.messageService.add({severity: 'success', summary: 'Başarılı', detail: 'Raporlar başarıyla birleştirildi.'});
            this.mergeDialogVisible = false;
            this.mergeLoading = false;
            this.selectedReports = [];
            this.loadReports();
          },
          error: () => {
            this.mergeLoading = false;
          }
        });
    }
  }

  exportExcel(): void {
    const exportFilter = { ...this.filter };
    if (this.activeTabId === 'shared') {
       if (this.selectedSharedReports && this.selectedSharedReports.length > 0) {
          exportFilter.reportIds = this.selectedSharedReports.map(s => s.report_id);
       }
    } else {
       if (this.selectedReports && this.selectedReports.length > 0) {
         exportFilter.reportIds = this.selectedReports.map(r => r.id);
       }
    }

    this.reportService.exportExcel(exportFilter).subscribe((response) => {
      const blob = response.body;
      const contentDisposition = response.headers.get('content-disposition');
      let filename = 'faaliyet_raporlari.xlsx';
      if (contentDisposition) {
        const utf8Matches = /filename\*=UTF-8''([^;]+)/.exec(contentDisposition);
        if (utf8Matches != null && utf8Matches[1]) {
            filename = decodeURIComponent(utf8Matches[1]);
        } else {
            const matches = /filename="?([^";]+)"?/.exec(contentDisposition);
            if (matches != null && matches[1]) {
              filename = matches[1];
            } else {
                const matchesFallback = /filename=([^;]+)/.exec(contentDisposition);
                if (matchesFallback != null && matchesFallback[1]) {
                    filename = matchesFallback[1];
                }
            }
        }
      }
      
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      a.click();
      window.URL.revokeObjectURL(url);
    });
  }

  exportExcelShared(reportId: number): void {
    const exportFilter = { reportIds: [reportId] };
    this.reportService.exportExcel(exportFilter as any).subscribe((response) => {
      const blob = response.body;
      const contentDisposition = response.headers.get('content-disposition');
      let filename = `faaliyet_raporu_${reportId}.xlsx`;
      if (contentDisposition) {
        const utf8Matches = /filename\*=UTF-8''([^;]+)/.exec(contentDisposition);
        if (utf8Matches != null && utf8Matches[1]) {
            filename = decodeURIComponent(utf8Matches[1]);
        } else {
            const matches = /filename="?([^";]+)"?/.exec(contentDisposition);
            if (matches != null && matches[1]) {
              filename = matches[1];
            } else {
                const matchesFallback = /filename=([^;]+)/.exec(contentDisposition);
                if (matchesFallback != null && matchesFallback[1]) {
                    filename = matchesFallback[1];
                }
            }
        }
      }

      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      a.click();
      window.URL.revokeObjectURL(url);
    });
  }

  exportPdf(id: number): void {
    this.reportService.exportPdf(id).subscribe((response) => {
      const blob = response.body;
      const contentDisposition = response.headers.get('content-disposition');
      let filename = `faaliyet_raporu_${id}.pdf`;
      if (contentDisposition) {
        const utf8Matches = /filename\*=UTF-8''([^;]+)/.exec(contentDisposition);
        if (utf8Matches != null && utf8Matches[1]) {
            filename = decodeURIComponent(utf8Matches[1]);
        } else {
            const matches = /filename="?([^";]+)"?/.exec(contentDisposition);
            if (matches != null && matches[1]) {
              filename = matches[1];
            } else {
                const matchesFallback = /filename=([^;]+)/.exec(contentDisposition);
                if (matchesFallback != null && matchesFallback[1]) {
                    filename = matchesFallback[1];
                }
            }
        }
      }

      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      a.click();
      window.URL.revokeObjectURL(url);
    }, (error) => {
        console.error("PDF Export Error", error);
        alert("PDF indirilirken bir hata oluştu. Sunucu bağlantısını kontrol edin.");
    });
  }

  openImportDialog(): void {
    this.importDialogRef = this.dialogService.open(ImportExcelDialogComponent, {
      header: 'Excel\'den İçe Aktar',
      width: '80%',
      contentStyle: { overflow: 'auto' },
      baseZIndex: 10000,
      maximizable: true
    });

    this.importDialogRef.onClose.subscribe((success: boolean) => {
      if (success) {
        this.loadReports();
      }
    });
  }

  proposalsVisible: boolean = false;
  proposals: any[] = [];
  proposalsLoading: boolean = false;

  openProposalsDialog() {
    this.proposalsVisible = true;
    this.loadProposals();
  }

  loadProposals() {
    this.proposalsLoading = true;
    this.reportService.getMyProposals().subscribe({
      next: (data) => {
        this.proposals = data;
        this.proposalsLoading = false;
      },
      error: () => this.proposalsLoading = false
    });
  }

  respondToProposal(proposal: any, isApproved: boolean) {
    const payload = {
      content: proposal.content,
      related_institutions: proposal.related_institutions,
      solution_proposals: proposal.solution_proposals
    };
    
    this.reportService.respondToProposal(proposal.id, isApproved, payload).subscribe(() => {
      this.messageService.add({ severity: 'success', summary: 'Başarılı', detail: 'Teklif yanıtlandı.' });
      this.loadProposals();
    });
  }

  downloadTemplate(): void {
    this.reportService.downloadImportTemplate().subscribe((response) => {
      const blob = response.body;
      const contentDisposition = response.headers.get('content-disposition');
      let filename = 'faaliyet_raporu_taslagi.xlsx';
      if (contentDisposition) {
        const matches = /filename="?([^";]+)"?/.exec(contentDisposition);
        if (matches != null && matches[1]) {
          filename = matches[1];
        }
      }

      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      a.click();
      window.URL.revokeObjectURL(url);
    });
  }
}