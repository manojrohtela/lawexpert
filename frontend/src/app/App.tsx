import { useState, useRef } from 'react';
import { Navigation } from './components/Navigation';
import { Sidebar } from './components/Sidebar';
import { ChatArea } from './components/ChatArea';
import { InsightsPanel } from './components/InsightsPanel';
import { Footer } from './components/Footer';
import { Menu, X, BarChart3 } from 'lucide-react';

export default function App() {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isInsightsPanelOpen, setIsInsightsPanelOpen] = useState(true);
  const [recentChats, setRecentChats] = useState<string[]>([]);
  const [chatKey, setChatKey] = useState(0);
  const pendingQueryRef = useRef<string>('');

  function handleNewMessage(query: string) {
    setRecentChats((prev) => {
      const filtered = prev.filter((q) => q !== query);
      return [query, ...filtered].slice(0, 20);
    });
  }

  function handleNewChat() {
    setChatKey((k) => k + 1);
    pendingQueryRef.current = '';
  }

  function handleSelectChat(query: string) {
    pendingQueryRef.current = query;
    setChatKey((k) => k + 1);
    setIsSidebarOpen(false);
  }

  return (
    <div className="h-screen w-full flex flex-col bg-background">
      <Navigation />

      <div className="flex-1 flex overflow-hidden relative">
        <button
          onClick={() => setIsSidebarOpen(!isSidebarOpen)}
          className="lg:hidden fixed top-20 left-4 z-50 w-10 h-10 bg-[#1E3A8A] text-white rounded-lg shadow-lg flex items-center justify-center"
        >
          {isSidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>

        <button
          onClick={() => setIsInsightsPanelOpen(!isInsightsPanelOpen)}
          className="hidden lg:flex fixed top-20 right-4 z-50 w-10 h-10 bg-white border border-border rounded-lg shadow-sm hover:shadow-md items-center justify-center transition-shadow"
        >
          <BarChart3 className="w-5 h-5 text-[#1E3A8A]" />
        </button>

        <div
          className={`${
            isSidebarOpen ? 'translate-x-0' : '-translate-x-full'
          } lg:translate-x-0 fixed lg:relative z-40 transition-transform duration-300 ease-in-out h-full`}
        >
          <Sidebar
            recentChats={recentChats}
            onNewChat={handleNewChat}
            onSelectChat={handleSelectChat}
          />
        </div>

        {isSidebarOpen && (
          <div
            className="lg:hidden fixed inset-0 bg-black/20 z-30"
            onClick={() => setIsSidebarOpen(false)}
          />
        )}

        <div className="flex-1 flex flex-col min-w-0">
          <ChatArea
            key={chatKey}
            onMessage={handleNewMessage}
            initialQuery={pendingQueryRef.current}
          />
          <Footer />
        </div>

        {isInsightsPanelOpen && (
          <div className="hidden lg:block">
            <InsightsPanel />
          </div>
        )}
      </div>
    </div>
  );
}
