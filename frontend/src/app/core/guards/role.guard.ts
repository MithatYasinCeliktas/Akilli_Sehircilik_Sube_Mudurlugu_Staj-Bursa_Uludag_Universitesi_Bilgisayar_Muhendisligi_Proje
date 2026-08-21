import { Injectable } from '@angular/core';
import { CanActivate, ActivatedRouteSnapshot, RouterStateSnapshot, Router } from '@angular/router';
import { AuthService } from '../services/auth.service';

@Injectable({
  providedIn: 'root'
})
export class RoleGuard implements CanActivate {
  constructor(
    private authService: AuthService,
    private router: Router
  ) {}

  canActivate(route: ActivatedRouteSnapshot, state: RouterStateSnapshot): boolean {
    const currentUser = this.authService.currentUserValue;
    if (!currentUser) {
      this.router.navigate(['/auth/login']);
      return false;
    }

    if (currentUser.is_superuser || currentUser.isSuperuser) {
      return true;
    }

    const expectedRoles = route.data['roles'] as Array<string>;
    if (expectedRoles && expectedRoles.includes(currentUser.role)) {
      return true;
    }

    this.router.navigate(['/dashboard']);
    return false;
  }
}
