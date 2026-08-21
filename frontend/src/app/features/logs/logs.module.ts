import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';

import { LogsRoutingModule } from './logs-routing.module';
import { LogListComponent } from './pages/log-list/log-list.component';

import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { SharedModule } from '../../shared/shared.module';
import { TableModule } from 'primeng/table';
import { ButtonModule } from 'primeng/button';
import { InputTextModule } from 'primeng/inputtext';
import { CalendarModule } from 'primeng/calendar';
import { DropdownModule } from 'primeng/dropdown';
import { TooltipModule } from 'primeng/tooltip';

@NgModule({
  declarations: [
    LogListComponent
  ],
  imports: [
    CommonModule,
    LogsRoutingModule,
    FormsModule,
    ReactiveFormsModule,
    SharedModule,
    TableModule,
    ButtonModule,
    InputTextModule,
    CalendarModule,
    DropdownModule,
    TooltipModule
  ]
})
export class LogsModule { }
