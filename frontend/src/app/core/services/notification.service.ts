import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Notification } from '../models/notification.model';
import { environment } from '../../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class NotificationService {
  private apiUrl = `${environment.apiUrl}/notifications`;

  constructor(private http: HttpClient) {}

  getNotifications(): Observable<Notification[]> {
    return this.http.get<Notification[]>(this.apiUrl);
  }

  getUnreadCount(): Observable<number> {
    return this.http.get<number>(`${this.apiUrl}/unread-count`);
  }

  markAsRead(notificationId: number): Observable<Notification> {
    return this.http.post<Notification>(`${this.apiUrl}/${notificationId}/read`, {});
  }

  markAllAsRead(): Observable<any> {
    return this.http.post(`${this.apiUrl}/read-all`, {});
  }
}
