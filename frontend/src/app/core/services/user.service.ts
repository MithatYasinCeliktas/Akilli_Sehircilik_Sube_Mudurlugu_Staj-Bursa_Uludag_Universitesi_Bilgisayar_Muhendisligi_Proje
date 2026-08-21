import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, map } from 'rxjs';
import { environment } from '../../../environments/environment';
import { DataResponse, PaginatedData } from '../models/api-response.model';
import { User } from '../models/user.model';

@Injectable({
  providedIn: 'root'
})
export class UserService {
  private readonly baseUrl = `${environment.apiUrl}/users`;

  constructor(private http: HttpClient) {}

  getUsers(
    page: number = 1,
    pageSize: number = 10,
    searchText?: string,
    unitId?: number,
    role?: string,
    isActive?: boolean
  ): Observable<PaginatedData<User>> {
    let params = new HttpParams()
      .set('page', page.toString())
      .set('page_size', pageSize.toString());

    if (searchText) params = params.set('search_text', searchText);
    if (unitId) params = params.set('unit_id', unitId.toString());
    if (role) params = params.set('role', role);
    if (isActive !== undefined && isActive !== null) params = params.set('is_active', isActive.toString());

    return this.http
      .get<DataResponse<PaginatedData<User>>>(this.baseUrl, { params })
      .pipe(map(res => res.data));
  }

  getUserById(id: number): Observable<User> {
    return this.http
      .get<DataResponse<User>>(`${this.baseUrl}/${id}`)
      .pipe(map(res => res.data));
  }

  getValidManagers(unitId: number): Observable<User[]> {
    return this.http
      .get<DataResponse<User[]>>(`${this.baseUrl}/managers/valid/${unitId}`)
      .pipe(map(res => res.data));
  }

  createUser(user: Partial<User>): Observable<User> {
    return this.http
      .post<DataResponse<User>>(this.baseUrl, user)
      .pipe(map(res => res.data));
  }

  updateUser(id: number, user: Partial<User>): Observable<User> {
    return this.http
      .put<DataResponse<User>>(`${this.baseUrl}/${id}`, user)
      .pipe(map(res => res.data));
  }

  deleteUser(id: number): Observable<boolean> {
    return this.http
      .delete<DataResponse<boolean>>(`${this.baseUrl}/${id}`)
      .pipe(map(res => res.data));
  }
}