import { Plus, MessageSquare, Scale, Laptop, Pill, BookOpen } from 'lucide-react';

const categories = [
  { icon: Scale, label: 'Criminal Law' },
  { icon: Laptop, label: 'Cyber Law' },
  { icon: Pill, label: 'Drug Law' },
  { icon: BookOpen, label: 'Constitution' },
];

interface SidebarProps {
  recentChats: string[];
  onNewChat: () => void;
  onSelectChat: (query: string) => void;
}

export function Sidebar({ recentChats, onNewChat, onSelectChat }: SidebarProps) {
  return (
    <div className="w-72 border-r border-border bg-sidebar h-full flex flex-col">
      <div className="p-4">
        <button
          onClick={onNewChat}
          className="w-full h-11 bg-[#1E3A8A] text-white rounded-xl hover:bg-[#1E3A8A]/90 transition-colors flex items-center justify-center gap-2"
        >
          <Plus className="w-5 h-5" />
          <span>New Chat</span>
        </button>
      </div>

      <div className="px-4 pb-4 flex-1 overflow-y-auto">
        <div className="text-xs text-muted-foreground mb-2">Recent Chats</div>
        {recentChats.length === 0 ? (
          <p className="text-xs text-muted-foreground px-1">No chats yet</p>
        ) : (
          <div className="space-y-1">
            {recentChats.map((chat, index) => (
              <button
                key={index}
                onClick={() => onSelectChat(chat)}
                className="w-full text-left px-3 py-2.5 rounded-lg hover:bg-sidebar-accent transition-colors text-sm text-sidebar-foreground/80 flex items-start gap-2"
              >
                <MessageSquare className="w-4 h-4 mt-0.5 shrink-0 text-muted-foreground" />
                <span className="truncate">{chat}</span>
              </button>
            ))}
          </div>
        )}

        <div className="mt-6">
          <div className="text-xs text-muted-foreground mb-2">Categories</div>
          <div className="space-y-1">
            {categories.map((category, index) => {
              const Icon = category.icon;
              return (
                <button
                  key={index}
                  className="w-full text-left px-3 py-2.5 rounded-lg hover:bg-sidebar-accent transition-colors text-sm flex items-center gap-2"
                >
                  <Icon className="w-4 h-4 text-[#14B8A6]" />
                  <span className="text-sidebar-foreground">{category.label}</span>
                </button>
              );
            })}
          </div>
        </div>
      </div>

      <div className="p-4 border-t border-sidebar-border">
        <div className="bg-gradient-to-br from-[#1E3A8A]/10 to-[#14B8A6]/10 rounded-xl p-4 space-y-2">
          <div className="text-xs text-muted-foreground">Indian Judiciary</div>
          <div className="space-y-1">
            <div className="flex items-baseline gap-1">
              <span className="text-2xl text-[#1E3A8A]">5.3 Cr</span>
              <span className="text-xs text-muted-foreground">cases pending</span>
            </div>
            <div className="flex items-baseline gap-1">
              <span className="text-lg text-[#14B8A6]">26K+</span>
              <span className="text-xs text-muted-foreground">judgments indexed</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
