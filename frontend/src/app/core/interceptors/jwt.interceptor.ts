import { Injectable } from '@angular/core';
import { HttpRequest, HttpHandler, HttpEvent, HttpInterceptor } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

@Injectable()
export class JwtInterceptor implements HttpInterceptor {
  intercept(request: HttpRequest<unknown>, next: HttpHandler): Observable<HttpEvent<unknown>> {
    let token: string | null = null;
    try {
      const storage = typeof window !== 'undefined' ? window.sessionStorage : null;
      if (storage) {
        token = storage.getItem(environment.tokenKey);
      }
    } catch (e) {
      // LocalStorage is disabled or throws SecurityError
    }
    const isApiUrl = request.url.startsWith(environment.apiUrl);

    if (token && isApiUrl) {
      request = request.clone({
        setHeaders: {
          Authorization: `Bearer ${token}`
        }
      });
    }

    return next.handle(request);
  }
}