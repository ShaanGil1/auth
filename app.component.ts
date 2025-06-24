import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';   // 👈 add this

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet],        // 👈 register the directive
  template: `<router-outlet />`
})
export class AppComponent {}
