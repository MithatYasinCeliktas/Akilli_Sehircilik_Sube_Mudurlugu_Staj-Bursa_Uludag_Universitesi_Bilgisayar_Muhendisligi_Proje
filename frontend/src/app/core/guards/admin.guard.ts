import { Injectable } from '@angular/core';
import { CanActivate, Router } from '@angular/router';
import { AuthService } from '../services/auth.service';

@Injectable({
  providedIn: 'root'
})
export class AdminGuard implements CanActivate {
  constructor(
    private authService: AuthService,
    private router: Router
  ) {}

  canActivate(): boolean {
    const currentUser = this.authService.currentUserValue;
    if (currentUser && (currentUser.is_superuser || currentUser.isSuperuser || currentUser.role === 'ADMIN' || currentUser.role === 'USER_MANAGER')) {
      return true;
    }

    this.router.navigate(['/dashboard']);
    return false;
  }
}