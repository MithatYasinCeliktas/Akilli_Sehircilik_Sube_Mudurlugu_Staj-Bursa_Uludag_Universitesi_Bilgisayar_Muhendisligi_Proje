import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, map } from 'rxjs';
import { environment } from '../../../environments/environment';
import { DataResponse } from '../models/api-response.model';
import { Institution } from '../models/institution.model';

@Injectable({
  providedIn: 'root'
})
export class InstitutionService {
  requestInstitution(name: string): Observable<any> {
    return this.http.post(`${this.baseUrl}/request`, { name });
  }

  private readonly baseUrl = `${environment.apiUrl}/institutions`;

  constructor(private http: HttpClient) {}

  getInstitutions(activeOnly: boolean = false): Observable<Institution[]> {
    let params = new HttpParams();
    if (activeOnly) {
      params = params.set('active_only', 'true');
    }

    return this.http
      .get<DataResponse<Institution[]>>(this.baseUrl, { params })
      .pipe(map(res => res.data));
  }

  createInstitution(institution: Partial<Institution>): Observable<Institution> {
    return this.http
      .post<DataResponse<Institution>>(this.baseUrl, institution)
      .pipe(map(res => res.data));
  }

  updateInstitution(id: number, institution: Partial<Institution>): Observable<Institution> {
    return this.http
      .put<DataResponse<Institution>>(`${this.baseUrl}/${id}`, institution)
      .pipe(map(res => res.data));
  }

  deleteInstitution(id: number): Observable<boolean> {
    return this.http
      .delete<DataResponse<boolean>>(`${this.baseUrl}/${id}`)
      .pipe(map(res => res.data || true));
  }
}
