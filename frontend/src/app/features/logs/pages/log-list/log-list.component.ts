import { Component, OnInit, OnDestroy } from '@angular/core';
import { SystemLogService } from '../../../../core/services/system-log.service';
import { SystemLog, LogFilter } from '../../../../core/models/system-log.model';
import { TableLazyLoadEvent } from 'primeng/table';
import { finalize } from 'rxjs/operators';

@Component({
  selector: 'app-log-list',
  templateUrl: './log-list.component.html',
  styleUrls: ['./log-list.component.css'],
  standalone: false
})
export class LogListComponent implements OnInit, OnDestroy {
  logs: SystemLog[] = [];
  totalRecords: number = 0;
  loading: boolean = false;
  private refreshInterval: any;
  
  // Filters
  filter: LogFilter = {
    page: 1,
    page_size: 10
  };

  actionOptions = [
    { label: 'Tümü', value: null },
    { label: 'Login', value: 'LOGIN' },
    { label: 'Logout', value: 'LOGOUT' },
    { label: 'Rapor Oluşturma', value: 'CREATE_REPORT' },
    { label: 'Rapor Güncelleme', value: 'UPDATE_REPORT' },
    { label: 'Rapor Silme', value: 'DELETE_REPORT' },
    { label: 'Satır Ekleme', value: 'CREATE_REPORT_ITEM' },
    { label: 'Satır Güncelleme', value: 'UPDATE_REPORT_ITEM' },
    { label: 'Satır Silme', value: 'DELETE_REPORT_ITEM' },
    { label: 'Kullanıcı İşlemleri', value: 'CREATE_USER' },
    { label: 'Excel İçe Aktar', value: 'IMPORT_EXCEL' },
    { label: 'Excel Dışa Aktar', value: 'EXPORT_EXCEL' },
    { label: 'Sohbet Sorusu', value: 'CHAT_QUERY' },
    { label: 'Sohbet Yanıtı', value: 'CHAT_RESPONSE' },
  ];

  entityTypeOptions = [
    { label: 'Tümü', value: null },
    { label: 'Kullanıcı (USER)', value: 'USER' },
    { label: 'Rapor (REPORT)', value: 'REPORT' },
    { label: 'Rapor Satırı (REPORT_ITEM)', value: 'REPORT_ITEM' },
    { label: 'Kurum (INSTITUTION)', value: 'INSTITUTION' },
    { label: 'Birim (UNIT)', value: 'UNIT' },
    { label: 'Paylaşım (REPORT_SHARE)', value: 'REPORT_SHARE' },
    { label: 'Sohbet Kaydı (CHAT_LOG)', value: 'CHAT_LOG' }
  ];

  constructor(private logService: SystemLogService) {}

  ngOnInit(): void {
    // initial load is handled by PrimeNG table's onLazyLoad
    
    // 5 dakikada bir (300000 ms) arka planda sessizce veriyi güncelle
    this.refreshInterval = setInterval(() => {
      this.loadLogs(undefined, true);
    }, 5 * 60 * 1000);
  }

  ngOnDestroy(): void {
    if (this.refreshInterval) {
      clearInterval(this.refreshInterval);
    }
  }

  loadLogs(event?: TableLazyLoadEvent, silent: boolean = false): void {
    if (!silent) {
      this.loading = true;
    }
    
    if (event) {
      this.filter.page = (event.first ?? 0) / (event.rows ?? 10) + 1;
      this.filter.page_size = event.rows ?? 10;
    }

    this.logService.getLogs(this.filter)
      .pipe(finalize(() => {
        if (!silent) this.loading = false;
      }))
      .subscribe({
        next: (response) => {
          this.logs = response.data.items;
          this.totalRecords = response.data.total;
        },
        error: (err) => {
          console.error('Loglar yüklenemedi', err);
        }
      });
  }

  onFilterChange(): void {
    this.filter.page = 1; // Reset to first page on filter change
    this.loadLogs();
  }

  exportJson(): void {
    this.logService.exportLogsJson(this.filter).subscribe(blob => {
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'system_logs.json';
      a.click();
      window.URL.revokeObjectURL(url);
    });
  }

  formatDetails(details: any): string {
    if (!details) return '';
    try {
      return JSON.stringify(details, null, 2);
    } catch (e) {
      return String(details);
    }
  }
}
