import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';

import { InstitutionsRoutingModule } from './institutions-routing.module';
import { InstitutionListComponent } from './pages/institution-list/institution-list.component';

// PrimeNG
import { TableModule } from 'primeng/table';
import { ButtonModule } from 'primeng/button';
import { InputTextModule } from 'primeng/inputtext';
import { DialogModule } from 'primeng/dialog';
import { ToastModule } from 'primeng/toast';
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { InputSwitchModule } from 'primeng/inputswitch';
import { TooltipModule } from 'primeng/tooltip';

@NgModule({
  declarations: [
    InstitutionListComponent
  ],
  imports: [
    CommonModule,
    InstitutionsRoutingModule,
    FormsModule,
    ReactiveFormsModule,
    TableModule,
    ButtonModule,
    InputTextModule,
    DialogModule,
    ToastModule,
    ConfirmDialogModule,
    InputSwitchModule,
    TooltipModule
  ]
})
export class InstitutionsModule { }
