import { ApplicationConfig } from '@angular/core';
import {
  provideRouter,
  withComponentInputBinding
} from '@angular/router';
import {
  provideHttpClient,
  withInterceptorsFromDi
} from '@angular/common/http';

import {
  MsalService,
  MsalGuard,
  MSAL_INSTANCE,
  MSAL_GUARD_CONFIG,
  MsalGuardConfiguration,
  MsalBroadcastService,
  MSAL_INTERCEPTOR_CONFIG,
  MsalInterceptorConfiguration,
  MsalInterceptor
} from '@azure/msal-angular';

import { HTTP_INTERCEPTORS } from '@angular/common/http';
import {
  InteractionType,
  PublicClientApplication
} from '@azure/msal-browser';

import { routes } from './app.routes';

/* ---------- MSAL core (PCA) ---------- */
export function msalInstanceFactory() {
  return new PublicClientApplication({
    auth: {
      clientId: '<forntend>',
      authority: 'https://login.microsoftonline.com/<tenent>',
      redirectUri: 'http://localhost:4200',      // ⬅️ replace with prod URL later
    },
    cache: {
      cacheLocation: 'localStorage',
      storeAuthStateInCookie: false
    }
  });
}

/* ---------- MSAL Guard (login scopes) ---------- */
export function msalGuardConfigFactory(): MsalGuardConfiguration {
  return {
    interactionType: InteractionType.Redirect,
    authRequest: {
      scopes: [
        'openid',
        'profile',
        'api://<backend>/access_as_user'
      ]
    }
  };
}

/* ---------- MSAL Interceptor (attach tokens to API calls) ---------- */
export function msalInterceptorConfigFactory(): MsalInterceptorConfiguration {
  return {
    interactionType: InteractionType.Redirect,
    protectedResourceMap: new Map<string, string[]>([
      // any request matching this URL gets the listed scopes
      ['http://localhost:8000/*', [
        'api://<backend>/access_as_user'
      ]]
    ])
  };
}

/* ---------- Global provider table ---------- */
export const appConfig: ApplicationConfig = {
  providers: [
    /* Angular HttpClient with DI interceptors */
    provideHttpClient(withInterceptorsFromDi()),

    /* Router (stand-alone API) */
    provideRouter(routes, withComponentInputBinding()),

    /* MSAL core + guard */
    { provide: MSAL_INSTANCE,        useFactory: msalInstanceFactory },
    { provide: MSAL_GUARD_CONFIG,    useFactory: msalGuardConfigFactory },

    /* MSAL interceptor config */
    { provide: MSAL_INTERCEPTOR_CONFIG, useFactory: msalInterceptorConfigFactory },

    /* Interceptor class itself */
    { provide: HTTP_INTERCEPTORS, useClass: MsalInterceptor, multi: true },

    /* Runtime services */
    MsalService,
    MsalGuard,
    MsalBroadcastService,
  ]
};
