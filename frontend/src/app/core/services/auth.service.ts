import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { BehaviorSubject, Observable, tap, map } from 'rxjs';
import { environment } from '../../../environments/environment';
import { DataResponse } from '../models/api-response.model';
import { AuthToken, LoginRequest, User } from '../models/user.model';

/**
 * Kimlik Doğrulama ve Kullanıcı Oturum Yönetimi Servisi
 *
 * Bu servis, kullanıcının sisteme giriş yapması (login), çıkış yapması (logout),
 * JWT token'ının saklanması ve mevcut kullanıcı profilinin (state) uygulama genelinde
 * RxJS BehaviorSubject ile paylaşılmasından sorumludur.
 */
@Injectable({
  providedIn: 'root'
})
export class AuthService {
  /** 
   * Mevcut kullanıcının anlık değerini tutan özel (private) RxJS öznesidir.
   * Uygulama içindeki bileşenler bu değere direkt erişemez, sadece abone olabilir (subscribe).
   */
  private currentUserSubject: BehaviorSubject<User | null>;
  
  /** 
   * Diğer bileşenlerin kullanıcı değişikliklerini anlık olarak dinleyebileceği (subscribe) Observable akışıdır.
   * Navbar veya Guard'lar genellikle bunu dinler.
   */
  public currentUser$: Observable<User | null>;

  /**
   * Güvenli bir şekilde SessionStorage veya LocalStorage'a erişim sağlar.
   * SSR (Server-Side Rendering) sırasında `window` objesi olmadığı için hata fırlatmasını engeller.
   */
  private getStorage(): Storage | null {
    if (typeof window === 'undefined') {
      return null;
    }
    try {
      const storage = window.sessionStorage;
      if (storage) {
        const testKey = '__storage_test__';
        storage.setItem(testKey, testKey);
        storage.removeItem(testKey);
        return storage;
      }
    } catch (e) {
      // LocalStorage is disabled or throws SecurityError
    }
    return null;
  }

  constructor(private http: HttpClient, private router: Router) {
    let initialUser: User | null = null;
    try {
      // Sayfa yenilendiğinde (refresh), kullanıcının oturumunun kopmaması için
      // SessionStorage'da daha önceden kaydedilmiş kullanıcı varsa geri yükleriz.
      const storage = this.getStorage();
      if (storage) {
        const storedUser = storage.getItem('current_user');
        if (storedUser) {
          initialUser = JSON.parse(storedUser);
        }
      }
    } catch (e) {
      console.error('Error loading current user from storage:', e);
    }
    this.currentUserSubject = new BehaviorSubject<User | null>(initialUser);
    this.currentUser$ = this.currentUserSubject.asObservable();
  }

  /**
   * RxJS aboneliği (subscription) kurmadan, mevcut kullanıcının kim olduğunu 
   * anlık olarak (snapshot) almak için kullanılır.
   */
  public get currentUserValue(): User | null {
    return this.currentUserSubject.value;
  }

  /**
   * Kullanıcının sisteme giriş yapıp yapmadığını (token ve user bilgisinin varlığını) kontrol eder.
   * AuthGuard gibi yetki kontrollerinde kullanılır.
   */
  public isLoggedIn(): boolean {
    const storage = this.getStorage();
    return !!storage?.getItem(environment.tokenKey) && !!this.currentUserValue;
  }

  /**
   * Backend API'sine giriş isteği (login) atar.
   * Başarılı olursa dönen JWT access_token'ı ve kullanıcı profilini tarayıcı hafızasına (Storage) kaydeder.
   * @param credentials E-posta ve şifre bilgilerini içeren LoginRequest objesi
   */
  login(credentials: LoginRequest): Observable<AuthToken> {
    return this.http
      .post<DataResponse<AuthToken>>(`${environment.apiUrl}/auth/login`, credentials)
      .pipe(
        map(response => response.data),
        tap(tokenData => {
          const storage = this.getStorage();
          if (storage) {
            // Backend'den gelen access_token'ı sakla (Daha sonra Interceptor bu token'ı isteklere ekleyecek)
            storage.setItem(environment.tokenKey, tokenData.access_token);
            // Kullanıcı profilini Auth objesinden al ve state'e/storage'a kaydet
            if (tokenData.user) {
              storage.setItem('current_user', JSON.stringify(tokenData.user));
              this.currentUserSubject.next(tokenData.user);
            }
          }
        })
      );
  }

  /**
   * Eğer backend'de kullanıcının yetkileri, adı vs. güncellenirse, 
   * bu metot çağrılarak frontend'deki oturum bilgisinin (`/auth/me` endpointi ile) güncellenmesi sağlanır.
   */
  loadUserProfile(): Observable<User> {
    return this.http
      .get<DataResponse<User>>(`${environment.apiUrl}/auth/me`)
      .pipe(
        map(response => response.data),
        tap(user => {
          const storage = this.getStorage();
          if (storage) {
            storage.setItem('current_user', JSON.stringify(user));
          }
          this.currentUserSubject.next(user);
        })
      );
  }

  /**
   * Kullanıcının oturumunu sonlandırır.
   * Tüm Storage (tarayıcı hafızası) verilerini siler ve kullanıcıyı `/auth/login` (Giriş) ekranına yönlendirir.
   */
  logout(): void {
    // Backend'e logout isteği atıyoruz ki çıkış işlemi loglansın
    this.http.post(`${environment.apiUrl}/auth/logout`, {}).subscribe({
      next: () => this.clearStorageAndRedirect(),
      error: () => this.clearStorageAndRedirect() // Hata olsa bile storage'ı temizle
    });
  }

  private clearStorageAndRedirect(): void {
    const storage = this.getStorage();
    if (storage) {
      storage.removeItem(environment.tokenKey);
      storage.removeItem('current_user');
    }
    this.currentUserSubject.next(null);
    this.router.navigate(['/auth/login']);
  }
}