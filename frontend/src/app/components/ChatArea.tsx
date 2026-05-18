import { ArrowUp, Copy, Check, Scale, ChevronDown, ChevronUp, Database, BookOpen, Gavel } from 'lucide-react';
import { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { sendChat, fetchSuggestions, type ChatMessage, type ChatResponse } from '../../lib/api';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  data?: ChatResponse;
}

interface ChatAreaProps {
  onMessage?: (query: string) => void;
  initialQuery?: string;
}

function TypingDots() {
  return (
    <div className="flex items-center gap-1 py-1">
      {[0, 1, 2].map((i) => (
        <span
          key={i}
          className="w-2 h-2 bg-[#1E3A8A]/40 rounded-full animate-bounce"
          style={{ animationDelay: `${i * 0.15}s` }}
        />
      ))}
    </div>
  );
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <button
      onClick={() => {
        navigator.clipboard.writeText(text);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      }}
      className="p-1.5 rounded-md text-muted-foreground hover:text-foreground hover:bg-accent transition-colors"
      title="Copy"
    >
      {copied ? <Check className="w-3.5 h-3.5 text-green-500" /> : <Copy className="w-3.5 h-3.5" />}
    </button>
  );
}

function ScoreBadge({ score }: { score: number }) {
  const pct = Math.round(score * 100);
  const color =
    pct >= 70 ? 'bg-green-100 text-green-700 border-green-200' :
    pct >= 50 ? 'bg-yellow-100 text-yellow-700 border-yellow-200' :
                'bg-gray-100 text-gray-500 border-gray-200';
  return (
    <span className={`text-xs px-1.5 py-0.5 rounded border font-mono ${color}`}>
      {pct}% match
    </span>
  );
}

function SourcesPanel({ data }: { data: ChatResponse }) {
  const [open, setOpen] = useState(false);
  const totalSources = data.law_hits.length + data.case_hits.length;
  if (totalSources === 0) return null;

  return (
    <div className="mt-3 border border-border rounded-xl overflow-hidden text-sm">
      {/* Header — always visible */}
      <button
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center justify-between px-4 py-2.5 bg-accent/50 hover:bg-accent transition-colors"
      >
        <div className="flex items-center gap-2 text-muted-foreground">
          <Database className="w-3.5 h-3.5 text-[#1E3A8A]" />
          <span className="font-medium text-[#1E3A8A]">
            {totalSources} source{totalSources > 1 ? 's' : ''} retrieved from your index
          </span>
          <span className="text-xs text-muted-foreground">
            ({data.law_hits.length} law{data.law_hits.length !== 1 ? 's' : ''}
            {data.case_hits.length > 0 ? `, ${data.case_hits.length} case${data.case_hits.length !== 1 ? 's' : ''}` : ''})
          </span>
        </div>
        {open ? <ChevronUp className="w-4 h-4 text-muted-foreground" /> : <ChevronDown className="w-4 h-4 text-muted-foreground" />}
      </button>

      {/* Expanded content */}
      {open && (
        <div className="divide-y divide-border">
          {data.law_hits.map((hit, i) => {
            const p = hit.payload;
            const text = (p.text as string) || '';
            return (
              <div key={`law-${i}`} className="px-4 py-3 bg-white space-y-2">
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <BookOpen className="w-3.5 h-3.5 text-blue-500 shrink-0" />
                    <span className="font-semibold text-blue-700">
                      {p.law_name as string} — {p.section_or_article as string}
                    </span>
                  </div>
                  <ScoreBadge score={hit.score} />
                </div>
                <p className="text-xs text-muted-foreground leading-relaxed line-clamp-3">
                  {text.slice(0, 300)}{text.length > 300 ? '…' : ''}
                </p>
              </div>
            );
          })}

          {data.case_hits.map((hit, i) => {
            const p = hit.payload;
            return (
              <div key={`case-${i}`} className="px-4 py-3 bg-white space-y-2">
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <Gavel className="w-3.5 h-3.5 text-teal-500 shrink-0" />
                    <span className="font-semibold text-teal-700">
                      {p.case_name as string} ({p.year as number})
                    </span>
                  </div>
                  <ScoreBadge score={hit.score} />
                </div>
                <p className="text-xs text-muted-foreground">{p.court as string} · {p.topic as string}</p>
                <p className="text-xs text-muted-foreground leading-relaxed line-clamp-3">
                  {(p.summary as string || '').slice(0, 250)}…
                </p>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

function AssistantMessage({ msg }: { msg: Message }) {
  return (
    <div className="flex gap-3 items-start max-w-3xl">
      <div className="w-8 h-8 rounded-full bg-[#1E3A8A] flex items-center justify-center shrink-0 mt-1">
        <Scale className="w-4 h-4 text-white" />
      </div>

      <div className="flex-1 space-y-1">
        {/* Answer */}
        <div className="prose prose-sm max-w-none text-foreground leading-relaxed
          prose-headings:text-[#1E3A8A] prose-headings:font-semibold
          prose-strong:text-foreground prose-strong:font-semibold
          prose-code:bg-accent prose-code:px-1 prose-code:rounded prose-code:text-sm
          prose-ul:my-2 prose-li:my-0.5 prose-p:my-2">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {msg.content}
          </ReactMarkdown>
        </div>

        {/* Sources panel */}
        {msg.data && <SourcesPanel data={msg.data} />}

        <div className="flex items-center gap-1 pt-1">
          <CopyButton text={msg.content} />
        </div>
      </div>
    </div>
  );
}

export function ChatArea({ onMessage, initialQuery }: ChatAreaProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const didRunInitial = useRef(false);

  useEffect(() => {
    fetchSuggestions().then(setSuggestions).catch(() =>
      setSuggestions([
        'What is the punishment for murder under BNS?',
        'Explain bail conditions under BNSS',
        'What does Article 21 say about personal liberty?',
        'Is WhatsApp chat admissible as evidence under BSA?',
      ])
    );
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  useEffect(() => {
    if (initialQuery && !didRunInitial.current) {
      didRunInitial.current = true;
      submit(initialQuery);
    }
  }, [initialQuery]);

  function handleInput(e: React.ChangeEvent<HTMLTextAreaElement>) {
    setInput(e.target.value);
    e.target.style.height = 'auto';
    e.target.style.height = Math.min(e.target.scrollHeight, 200) + 'px';
  }

  async function submit(query: string) {
    const text = query.trim();
    if (!text || loading) return;

    onMessage?.(text);
    setInput('');
    if (inputRef.current) inputRef.current.style.height = 'auto';

    const userMsg: Message = { role: 'user', content: text };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    const history: ChatMessage[] = messages.map((m) => ({
      role: m.role,
      content: m.content,
    }));

    try {
      const data = await sendChat(text, history, 3);
      setMessages((prev) => [...prev, { role: 'assistant', content: data.answer, data }]);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Something went wrong';
      setMessages((prev) => [...prev, { role: 'assistant', content: `Sorry, I ran into an error: ${msg}` }]);
    } finally {
      setLoading(false);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }

  const hasMessages = messages.length > 0;

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden bg-background">
      <div className="flex-1 overflow-y-auto">
        {!hasMessages ? (
          <div className="h-full flex flex-col items-center justify-center p-8">
            <div className="max-w-2xl w-full space-y-8">
              <div className="text-center space-y-3">
                <div className="w-16 h-16 mx-auto bg-[#1E3A8A] rounded-2xl flex items-center justify-center shadow-lg">
                  <Scale className="w-8 h-8 text-white" />
                </div>
                <h1 className="text-2xl font-bold text-[#1E3A8A]">LexAI — Your Legal Expert</h1>
                <p className="text-muted-foreground">
                  Ask me anything about Indian law — BNS, IPC, Constitution, BNSS, IT Act, NDPS and more.
                  I'll give you real section references backed by your indexed data.
                </p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {suggestions.map((q, i) => (
                  <button
                    key={i}
                    onClick={() => submit(q)}
                    className="group text-left p-4 rounded-xl border border-border bg-white hover:border-[#1E3A8A]/40 hover:shadow-md transition-all"
                  >
                    <p className="text-sm text-foreground group-hover:text-[#1E3A8A] transition-colors leading-relaxed">
                      {q}
                    </p>
                  </button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <div className="max-w-3xl mx-auto px-4 py-6 space-y-8">
            {messages.map((msg, i) =>
              msg.role === 'user' ? (
                <div key={i} className="flex justify-end">
                  <div className="max-w-[75%] bg-[#1E3A8A] text-white px-4 py-3 rounded-2xl rounded-tr-sm text-sm leading-relaxed">
                    {msg.content}
                  </div>
                </div>
              ) : (
                <AssistantMessage key={i} msg={msg} />
              )
            )}

            {loading && (
              <div className="flex gap-3 items-start">
                <div className="w-8 h-8 rounded-full bg-[#1E3A8A] flex items-center justify-center shrink-0">
                  <Scale className="w-4 h-4 text-white" />
                </div>
                <div className="bg-white border border-border rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm">
                  <TypingDots />
                </div>
              </div>
            )}

            <div ref={bottomRef} />
          </div>
        )}
      </div>

      {/* Input bar */}
      <div className="border-t border-border bg-background px-4 py-4">
        <div className="max-w-3xl mx-auto">
          <div className="relative flex items-end bg-white border border-border rounded-2xl shadow-sm hover:border-[#1E3A8A]/40 focus-within:border-[#1E3A8A] transition-colors px-4 py-3 gap-3">
            <textarea
              ref={inputRef}
              rows={1}
              value={input}
              onChange={handleInput}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  submit(input);
                }
              }}
              placeholder="Ask about Indian law… (Shift+Enter for new line)"
              disabled={loading}
              className="flex-1 resize-none bg-transparent outline-none text-sm text-foreground placeholder:text-muted-foreground min-h-[24px] max-h-[200px] disabled:opacity-50"
            />
            <button
              onClick={() => submit(input)}
              disabled={loading || !input.trim()}
              className="w-8 h-8 bg-[#1E3A8A] rounded-lg flex items-center justify-center hover:bg-[#1E3A8A]/90 transition-colors disabled:opacity-30 shrink-0"
            >
              <ArrowUp className="w-4 h-4 text-white" />
            </button>
          </div>
          <p className="text-xs text-muted-foreground text-center mt-2">
            LexAI uses real legal data from BNS, IPC, Constitution & more · Not a substitute for professional legal advice
          </p>
        </div>
      </div>
    </div>
  );
}
