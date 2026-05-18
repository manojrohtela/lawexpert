import { Search, User, Moon } from 'lucide-react';

export function Navigation() {
  return (
    <nav className="h-16 border-b border-border bg-white flex items-center px-6 gap-8">
      {/* Logo */}
      <div className="flex items-center gap-2">
        <div className="w-8 h-8 bg-[#1E3A8A] rounded-lg flex items-center justify-center">
          <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 6l3 1m0 0l-3 9a5.002 5.002 0 006.001 0M6 7l3 9M6 7l6-2m6 2l3-1m-3 1l-3 9a5.002 5.002 0 006.001 0M18 7l3 9m-3-9l-6-2m0-2v2m0 16V5m0 16H9m3 0h3" />
          </svg>
        </div>
        <span className="text-[#1E3A8A]">Legal AI</span>
      </div>

      {/* Search Bar */}
      <div className="flex-1 max-w-2xl">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
          <input
            type="text"
            placeholder="Ask legal question..."
            className="w-full h-10 pl-10 pr-4 rounded-lg bg-input-background border border-transparent hover:border-border focus:border-[#1E3A8A] focus:outline-none transition-colors"
          />
        </div>
      </div>

      {/* Right Actions */}
      <div className="flex items-center gap-3">
        <button className="w-9 h-9 rounded-lg hover:bg-accent flex items-center justify-center transition-colors">
          <Moon className="w-5 h-5 text-muted-foreground" />
        </button>
        <button className="w-9 h-9 rounded-full bg-[#1E3A8A] flex items-center justify-center">
          <User className="w-5 h-5 text-white" />
        </button>
      </div>
    </nav>
  );
}
