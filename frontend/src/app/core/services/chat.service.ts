import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

export interface ChatMessageRequest {
  message: string;
}

export interface ChatMessageResponse {
  intent: string;
  message: string;
  route?: string;
  action_trigger?: string;
}

@Injectable({
  providedIn: 'root'
})
export class ChatService {
  private apiUrl = `${environment.apiUrl}/chat`;

  constructor(private http: HttpClient) {}

  sendMessage(message: string): Observable<ChatMessageResponse> {
    return this.http.post<ChatMessageResponse>(`${this.apiUrl}/message`, { message });
  }
}
