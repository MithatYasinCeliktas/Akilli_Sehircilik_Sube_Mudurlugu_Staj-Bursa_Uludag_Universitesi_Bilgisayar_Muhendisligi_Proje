import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, Routes } from '@angular/router';

import { UserListComponent } from './pages/user-list/user-list.component';
import { SharedModule } from '../../shared/shared.module';

const routes: Routes = [
  { path: '', component: UserListComponent }
];

@NgModule({
  declarations: [UserListComponent],
  imports: [
    CommonModule,
    RouterModule.forChild(routes),
    SharedModule
  ]
})
export class UsersModule { }