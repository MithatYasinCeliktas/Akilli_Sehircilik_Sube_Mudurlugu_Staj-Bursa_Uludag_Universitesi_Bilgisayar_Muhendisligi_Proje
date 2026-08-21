import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormsModule } from '@angular/forms';
import { RouterModule, Routes } from '@angular/router';

import { ReportListComponent } from './pages/report-list/report-list.component';
import { ReportFormComponent } from './pages/report-form/report-form.component';
import { ImportExcelDialogComponent } from './components/import-excel-dialog/import-excel-dialog.component';
import { SharedModule } from '../../shared/shared.module';

const routes: Routes = [
  { path: '', component: ReportListComponent },
  { path: 'new', component: ReportFormComponent },
  { path: ':id', component: ReportFormComponent }
];

@NgModule({
  declarations: [ReportListComponent, ReportFormComponent, ImportExcelDialogComponent],
  imports: [
    CommonModule,
    ReactiveFormsModule,
    FormsModule,
    RouterModule.forChild(routes),
    SharedModule
  ]
})
export class ReportsModule { }