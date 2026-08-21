import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, map } from 'rxjs';
import { environment } from '../../../environments/environment';
import { DataResponse, PaginatedData } from '../models/api-response.model';
import { ActivityReport, ActivityReportCreate, ReportFilter } from '../models/report.model';

@Injectable({
  providedIn: 'root'
})
export class ReportService {
  private readonly baseUrl = `${environment.apiUrl}/reports`;
  private readonly exportUrl = `${environment.apiUrl}/export`;

  constructor(private http: HttpClient) {}

  getReports(filter: ReportFilter): Observable<PaginatedData<ActivityReport>> {
    let params = new HttpParams();

    if (filter.year) params = params.set('year', filter.year.toString());
    if (filter.month) params = params.set('month', filter.month.toString());
    if (filter.status) params = params.set('status', filter.status);
    if (filter.userIds && filter.userIds.length > 0) {
      filter.userIds.forEach(id => {
        params = params.append('user_ids', id.toString());
      });
    }
    if (filter.unitId) params = params.set('unit_id', filter.unitId.toString());
    if (filter.category) params = params.set('category', filter.category);
    if (filter.searchText) params = params.set('search_text', filter.searchText);
    if (filter.page) params = params.set('page', filter.page.toString());
    if (filter.pageSize) params = params.set('page_size', filter.pageSize.toString());

    return this.http
      .get<DataResponse<PaginatedData<ActivityReport>>>(this.baseUrl, { params })
      .pipe(map(res => res.data));
  }

  getReportById(id: number): Observable<ActivityReport> {
    return this.http
      .get<DataResponse<ActivityReport>>(`${this.baseUrl}/${id}`)
      .pipe(map(res => res.data));
  }

  createReport(report: ActivityReportCreate): Observable<ActivityReport> {
    return this.http
      .post<DataResponse<ActivityReport>>(this.baseUrl, report)
      .pipe(map(res => res.data));
  }

  updateReport(id: number, report: Partial<ActivityReportCreate>): Observable<ActivityReport> {
    return this.http
      .put<DataResponse<ActivityReport>>(`${this.baseUrl}/${id}`, report)
      .pipe(map(res => res.data));
  }

  deleteReport(id: number): Observable<boolean> {
    return this.http
      .delete<DataResponse<boolean>>(`${this.baseUrl}/${id}`)
      .pipe(map(res => res.data));
  }

  exportExcel(filter: ReportFilter): Observable<any> {
    let params = new HttpParams();
    if (filter.year) params = params.set('year', filter.year.toString());
    if (filter.month) params = params.set('month', filter.month.toString());
    if (filter.status) params = params.set('status', filter.status);
    if (filter.userIds && filter.userIds.length > 0) {
      filter.userIds.forEach(id => {
        params = params.append('user_ids', id.toString());
      });
    }
    if (filter.unitId) params = params.set('unit_id', filter.unitId.toString());
    if (filter.category) params = params.set('category', filter.category);
    if (filter.searchText) params = params.set('search_text', filter.searchText);
    if (filter.reportIds && filter.reportIds.length > 0) {
      filter.reportIds.forEach(id => {
        params = params.append('report_ids', id.toString());
      });
    }

    return this.http.get(`${this.exportUrl}/excel`, {
      params,
      responseType: 'blob',
      observe: 'response'
    });
  }

  exportPdf(reportId: number): Observable<any> {
    return this.http.get(`${this.exportUrl}/pdf/${reportId}`, {
      responseType: 'blob',
      observe: 'response'
    });
  }

  addReportItem(reportId: number, item: any): Observable<any> {
    return this.http.post<DataResponse<any>>(`${this.baseUrl}/${reportId}/items`, item).pipe(map(res => res.data));
  }
  updateReportItem(reportId: number, itemId: number, item: any): Observable<any> {
    return this.http.put<DataResponse<any>>(`${this.baseUrl}/${reportId}/items/${itemId}`, item).pipe(map(res => res.data));
  }
  deleteReportItem(reportId: number, itemId: number): Observable<any> {
    return this.http.delete<DataResponse<any>>(`${this.baseUrl}/${reportId}/items/${itemId}`).pipe(map(res => res.data));
  }
  reviewReportItem(reportId: number, itemId: number, review: any): Observable<any> {
    return this.http.put<DataResponse<any>>(`${this.baseUrl}/${reportId}/items/${itemId}/review`, review).pipe(map(res => res.data));
  }
  passDownRejection(reportId: number, itemId: number, data: any): Observable<any> {
    return this.http.post<DataResponse<any>>(`${this.baseUrl}/${reportId}/items/${itemId}/pass-down`, data).pipe(map(res => res.data));
  }
  approveReport(reportId: number, force: boolean = false): Observable<any> {
    return this.http.post<DataResponse<any>>(`${this.baseUrl}/${reportId}/approve?force=${force}`, {}).pipe(map(res => res.data));
  }
  transferReport(reportId: number): Observable<any> {
    return this.http.post<DataResponse<any>>(`${this.baseUrl}/${reportId}/transfer`, {}).pipe(map(res => res.data));
  }
  getUnitReportItems(filters: any): Observable<any> {
    let params = new HttpParams();
    if (filters) {
      Object.keys(filters).forEach(key => {
        if (filters[key] !== undefined && filters[key] !== null) {
          if (Array.isArray(filters[key])) {
            params = params.set(key, filters[key].join(','));
          } else {
            params = params.set(key, filters[key]);
          }
        }
      });
    }
    return this.http.get<DataResponse<any>>(`${this.baseUrl}/unit-items`, { params }).pipe(map(res => res.data));
  }
  getMyProposals(): Observable<any> {
    return this.http.get<DataResponse<any>>(`${this.baseUrl}/proposals/me`).pipe(map(res => res.data));
  }
  respondToProposal(proposalId: number, isApproved: boolean, payload: any): Observable<any> {
    payload.is_approved = isApproved;
    return this.http.post<DataResponse<any>>(`${this.baseUrl}/proposals/${proposalId}/respond`, payload).pipe(map(res => res.data));
  }
  downloadImportTemplate(): Observable<any> {
    return this.http.get(`${environment.apiUrl}/export/excel-template`, { responseType: 'blob', observe: 'response' });
  }
  getReportIdByItem(itemId: number): Observable<number> {
    return this.http.get<DataResponse<number>>(`${this.baseUrl}/item/${itemId}/report-id`).pipe(map(res => res.data));
  }
  previewImport(file: File, targetReport: 'OWN_REPORT' | 'MANAGER_REPORT'): Observable<any> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('target_report', targetReport);
    return this.http.post<DataResponse<any>>(`${environment.apiUrl}/reports/import/preview`, formData).pipe(map(res => res.data));
  }
  revalidateImport(payload: any): Observable<any> {
    return this.http.post<DataResponse<any>>(`${environment.apiUrl}/reports/import/revalidate`, payload).pipe(map(res => res.data));
  }
  executeImport(payload: any): Observable<any> {
    return this.http.post<DataResponse<any>>(`${environment.apiUrl}/reports/import/execute`, payload).pipe(map(res => res.data));
  }

  mergeItems(itemIds: number[], title?: string): Observable<any> {
    return this.http.post<any>(`${this.baseUrl}/merge-items`, { item_ids: itemIds, title });
  }
  mergeReports(reportIds: number[], title?: string): Observable<any> {
    return this.http.post<any>(`${this.baseUrl}/merge`, { report_ids: reportIds, title });
  }
}