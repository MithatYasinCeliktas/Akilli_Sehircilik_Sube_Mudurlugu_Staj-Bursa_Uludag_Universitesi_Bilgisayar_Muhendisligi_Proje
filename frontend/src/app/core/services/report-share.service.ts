import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import { ReportShareCreate, ReportShareAction, ReportShareResponse } from '../models/report-share.model';

@Injectable({
  providedIn: 'root'
})
export class ReportShareService {
  private apiUrl = `${environment.apiUrl}/report-shares`;

  constructor(private http: HttpClient) {}

  requestShare(data: ReportShareCreate): Observable<ReportShareResponse> {
    return this.http.post<ReportShareResponse>(`${this.apiUrl}/request`, data);
  }

  getPendingShares(): Observable<ReportShareResponse[]> {
    return this.http.get<ReportShareResponse[]>(`${this.apiUrl}/pending`);
  }

  getApprovedShares(): Observable<ReportShareResponse[]> {
    return this.http.get<ReportShareResponse[]>(`${this.apiUrl}/approved`);
  }

  getMyShares(): Observable<ReportShareResponse[]> {
    return this.http.get<ReportShareResponse[]>(`${this.apiUrl}/my-shares`);
  }

  getSharedWithMe(): Observable<ReportShareResponse[]> {
    return this.http.get<ReportShareResponse[]>(`${this.apiUrl}/shared-with-me`);
  }

  approveShare(id: number, action: ReportShareAction = {}): Observable<ReportShareResponse> {
    return this.http.put<ReportShareResponse>(`${this.apiUrl}/${id}/approve`, action);
  }

  rejectShare(id: number, action: ReportShareAction = {}): Observable<ReportShareResponse> {
    return this.http.put<ReportShareResponse>(`${this.apiUrl}/${id}/reject`, action);
  }

  revokeShare(id: number, action: ReportShareAction = {}): Observable<ReportShareResponse> {
    return this.http.put<ReportShareResponse>(`${this.apiUrl}/${id}/revoke`, action);
  }
}
