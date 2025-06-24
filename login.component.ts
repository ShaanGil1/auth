import { Component, OnInit } from '@angular/core';
import { MsalService } from '@azure/msal-angular';
import { PublicClientApplication, AuthenticationResult } from '@azure/msal-browser';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';

@Component({
  standalone: true,
  selector: 'app-login',
  imports: [CommonModule],
  template: `
    <div style="text-align: center; margin-top: 40px;">
      <button *ngIf="!isLoggedIn" (click)="login()">Login with Azure AD</button>
    </div>
  `
})
export class LoginComponent implements OnInit {
  isLoggedIn = false;

  constructor(private msalService: MsalService, private router: Router) {}

  async ngOnInit() {
    const instance = this.msalService.instance as PublicClientApplication;
    await instance.initialize();

    const result = await instance.handleRedirectPromise();
    if (result?.account) {
      instance.setActiveAccount(result.account);
      this.isLoggedIn = true;
      this.router.navigate(['/welcome']);
    } else if (instance.getAllAccounts().length > 0) {
      this.isLoggedIn = true;
      this.router.navigate(['/welcome']);
    }
  }

  login() {
    this.msalService.loginRedirect();
  }
}
