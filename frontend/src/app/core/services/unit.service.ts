import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, map } from 'rxjs';
import { environment } from '../../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class UnitService {
  private readonly baseUrl = `${environment.apiUrl}/units`;

  constructor(private http: HttpClient) {}

  getUnitTree(): Observable<any[]> {
    return this.http.get<any[]>(`${this.baseUrl}/tree`).pipe(map((response: any) => response?.data ?? response));
  }

  createUnit(unit: any): Observable<any> {
    return this.http.post<any>(this.baseUrl, unit).pipe(map((res: any) => res?.data ?? res));
  }

  updateUnit(id: number, unit: any): Observable<any> {
    return this.http.put<any>(`${this.baseUrl}/${id}`, unit).pipe(map((res: any) => res?.data ?? res));
  }
}
