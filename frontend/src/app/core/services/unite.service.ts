import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, map } from 'rxjs';
import { environment } from '../../../environments/environment';
import { DataResponse } from '../models/api-response.model';

export interface UnitTreeNode {
  id: number;
  name: string;
  code: string;
  unitType: string;
  children?: UnitTreeNode[];
}

@Injectable({
  providedIn: 'root'
})
export class UnitService {
  private readonly baseUrl = `${environment.apiUrl}/units`;

  constructor(private http: HttpClient) {}

  getUnitTree(): Observable<UnitTreeNode[]> {
    return this.http
      .get<DataResponse<UnitTreeNode[]>>(`${this.baseUrl}/tree`)
      .pipe(map(res => res.data));
  }

  createUnit(unit: Partial<UnitTreeNode>): Observable<UnitTreeNode> {
    return this.http
      .post<DataResponse<UnitTreeNode>>(this.baseUrl, unit)
      .pipe(map(res => res.data));
  }

  updateUnit(id: number, unit: Partial<UnitTreeNode>): Observable<UnitTreeNode> {
    return this.http
      .put<DataResponse<UnitTreeNode>>(`${this.baseUrl}/${id}`, unit)
      .pipe(map(res => res.data));
  }

  deleteUnit(id: number): Observable<boolean> {
    return this.http
      .delete<DataResponse<boolean>>(`${this.baseUrl}/${id}`)
      .pipe(map(res => res.data));
  }
}