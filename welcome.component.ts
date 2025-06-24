import { Component, OnInit } from '@angular/core';
import { MsalService } from '@azure/msal-angular';
import { ApiService } from '../api.service';
import { CommonModule } from '@angular/common';

@Component({
  standalone: true,
  selector: 'app-welcome',
  imports: [CommonModule],
  template: `
    <div style="text-align: center; margin-top: 40px;">
      <h2>Welcome {{ username }}</h2>
      <button (click)="callApi()">Call Backend</button>
      <pre *ngIf="apiResult">{{ apiResult | json }}</pre>
    </div>
  `
})
export class WelcomeComponent implements OnInit {
  username: string | undefined;
  apiResult: any;

  constructor(private msalService: MsalService, private api: ApiService) {}

  ngOnInit(): void {
    const account = this.msalService.instance.getActiveAccount() ||
                    this.msalService.instance.getAllAccounts()[0];
    this.username = account?.name;
  }

  callApi() {
    this.api.callProtectedRoute().subscribe({
      next: (res) => this.apiResult = res,
      error: (err) => this.apiResult = { error: err.message }
    });
  }
}
