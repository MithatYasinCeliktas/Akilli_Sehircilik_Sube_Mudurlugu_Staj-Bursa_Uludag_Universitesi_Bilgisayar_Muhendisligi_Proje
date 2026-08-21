import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import { SystemLog, LogFilter } from '../models/system-log.model';
import { DataResponse, PaginatedData } from '../models/api-response.model';

@Injectable({
  providedIn: 'root'
})
export class SystemLogService {
  private apiUrl = `${environment.apiUrl}/logs`;

  constructor(private http: HttpClient) {}

  getLogs(filter: LogFilter): Observable<DataResponse<PaginatedData<SystemLog>>> {
    let params = new HttpParams();
    
    if (filter.user_id) params = params.set('user_id', filter.user_id.toString());
    if (filter.action) params = params.set('action', filter.action);
    if (filter.entity_type) params = params.set('entity_type', filter.entity_type);
    if (filter.entity_id) params = params.set('entity_id', filter.entity_id.toString());
    if (filter.start_date) params = params.set('start_date', filter.start_date);
    if (filter.end_date) params = params.set('end_date', filter.end_date);
    if (filter.page) params = params.set('page', filter.page.toString());
    if (filter.page_size) params = params.set('page_size', filter.page_size.toString());

    return this.http.get<DataResponse<PaginatedData<SystemLog>>>(this.apiUrl, { params });
  }

  exportLogsJson(filter: LogFilter): Observable<Blob> {
    let params = new HttpParams();
    
    if (filter.user_id) params = params.set('user_id', filter.user_id.toString());
    if (filter.action) params = params.set('action', filter.action);
    if (filter.entity_type) params = params.set('entity_type', filter.entity_type);
    if (filter.entity_id) params = params.set('entity_id', filter.entity_id.toString());
    if (filter.start_date) params = params.set('start_date', filter.start_date);
    if (filter.end_date) params = params.set('end_date', filter.end_date);

    return this.http.get(`${this.apiUrl}/export`, {
      params,
      responseType: 'blob'
    });
  }
}
