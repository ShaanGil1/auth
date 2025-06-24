import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export type BackendResponse = {
  message: string;
  oid: string;
  issued_at: number;
};

@Injectable({ providedIn: 'root' })
export class ApiService {
  constructor(private http: HttpClient) {}

  callProtectedRoute(): Observable<BackendResponse> {
    // ⬅️ No token logic needed: MSAL interceptor handles it
    return this.http.get<BackendResponse>('http://localhost:8000/protected');
  }
}
