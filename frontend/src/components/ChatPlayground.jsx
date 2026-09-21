import React, { useRef, useEffect, useState } from 'react';
import { 
  Send, 
  Square, 
  Sparkles, 
  ArrowDown, 
  Brain,
  MessageSquarePlus,
  Terminal,
  Code2,
  HelpCircle
} from 'lucide-react';
import { ChatMessage } from './ChatMessage';
import { useSettings } from '../context/SettingsContext';
import { isReasoningModel } from '../utils/format';

const SUGGESTIONS = [
  {
    icon: HelpCircle,
    title: 'Quantum Computing',
    prompt: 'Explain the principles of quantum superposition and entanglement in simple, intuitive terms.',
  },
  {
    icon: Code2,
    title: 'Python Async Code',
    prompt: 'Write an asynchronous Python function using asyncio and httpx to download 5 URLs concurrently with error handling.',
  },
  {
    icon: Brain,
    title: 'Logic & Reasoning',
    prompt: 'There are 3 boxes labeled Apples, Oranges, and Mixed. Every box is mislabeled. You can pick only one fruit from one box. How do you determine the correct label for every box?',
  },
  {
    icon: Terminal,
    title: 'FastAPI Microservice',
    prompt: 'Demonstrate how to build a high-performance streaming Server-Sent Events (SSE) endpoint in FastAPI with Python.',
  },
];

export function ChatPlayground({ 
  messages, 
  isStreaming, 
  onSendMessage, 
  onStopStreaming,
  loadedModel
}) {
  const { settings } = useSettings();
  const [inputPrompt, setInputPrompt] = useState('');
  const [showScrollBottom, setShowScrollBottom] = useState(false);
  
  const messagesEndRef = useRef(null);
  const scrollContainerRef = useRef(null);
  const textareaRef = useRef(null);
  const userScrolledUpRef = useRef(false);

  // Auto-scroll to bottom on new tokens or messages without fighting user manual scroll
  useEffect(() => {
    if (settings.autoScroll && !userScrolledUpRef.current && scrollContainerRef.current) {
      scrollContainerRef.current.scrollTop = scrollContainerRef.current.scrollHeight;
    }
  }, [messages, isStreaming, settings.autoScroll]);

  // Track scroll position for floating "Scroll to bottom" button
  const handleScroll = () => {
    if (!scrollContainerRef.current) return;
    const { scrollTop, scrollHeight, clientHeight } = scrollContainerRef.current;
    const isScrolledUp = scrollHeight - scrollTop - clientHeight > 80;
    userScrolledUpRef.current = isScrolledUp;
    setShowScrollBottom(isScrolledUp);
  };

  const scrollToBottom = () => {
    userScrolledUpRef.current = false;
    setShowScrollBottom(false);
    if (scrollContainerRef.current) {
      scrollContainerRef.current.scrollTo({
        top: scrollContainerRef.current.scrollHeight,
        behavior: 'smooth',
      });
    }
  };

  // Adjust textarea height dynamically
  const handleInputChange = (e) => {
    setInputPrompt(e.target.value);
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  };

  const handleSubmit = (e) => {
    e?.preventDefault();
    if (!inputPrompt.trim() || isStreaming) return;
    userScrolledUpRef.current = false;
    setShowScrollBottom(false);
    onSendMessage(inputPrompt.trim());
    setInputPrompt('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="flex-1 flex flex-col h-full relative overflow-hidden bg-white dark:bg-[#090d16] transition-colors">
      
      {/* Messages Scroll Area */}
      <div 
        ref={scrollContainerRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto divide-y divide-transparent"
      >
        {messages.length === 0 ? (
          /* Empty / Welcome State */
          <div className="max-w-3xl mx-auto px-4 py-8 sm:py-16 text-center">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-tr from-brand-500/20 to-emerald-500/10 text-brand-500 mb-6 border border-brand-500/20 shadow-lg shadow-brand-500/10">
              <Sparkles className="w-8 h-8" />
            </div>

            <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900 dark:text-white mb-2">
              vLLM Inference Studio
            </h2>
            <p className="text-sm text-slate-500 dark:text-slate-400 max-w-md mx-auto mb-8">
              Continuous batching, PagedAttention, and low-latency token generation powered by FastAPI.
            </p>

            {/* Suggestion Prompts */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-left max-w-2xl mx-auto">
              {SUGGESTIONS.map((item, idx) => {
                const Icon = item.icon;
                return (
                  <button
                    key={idx}
                    onClick={() => {
                      setInputPrompt(item.prompt);
                      if (textareaRef.current) {
                        textareaRef.current.focus();
                      }
                    }}
                    type="button"
                    className="p-3.5 rounded-2xl bg-slate-50 hover:bg-slate-100 dark:bg-slate-900/60 dark:hover:bg-slate-800/80 border border-slate-200/80 dark:border-slate-800 transition-all duration-150 hover:border-brand-500/40 text-left group min-h-[64px]"
                  >
                    <div className="flex items-center space-x-2 mb-1">
                      <Icon className="w-4 h-4 text-brand-500 group-hover:scale-110 transition-transform" />
                      <span className="text-xs font-semibold text-slate-800 dark:text-slate-200">
                        {item.title}
                      </span>
                    </div>
                    <p className="text-xs text-slate-500 dark:text-slate-400 line-clamp-2">
                      {item.prompt}
                    </p>
                  </button>
                );
              })}
            </div>
          </div>
        ) : (
          /* Render Messages */
          <div className="max-w-4xl mx-auto py-2">
            {messages.map((msg, index) => (
              <ChatMessage key={index} message={msg} />
            ))}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Floating Scroll to Bottom FAB */}
      {showScrollBottom && (
        <button
          onClick={scrollToBottom}
          type="button"
          className="absolute bottom-24 right-6 p-2.5 rounded-full bg-brand-500 hover:bg-brand-600 text-white shadow-lg shadow-brand-500/30 transition-all duration-200 animate-fade-in z-20 min-h-[44px] min-w-[44px] flex items-center justify-center"
          aria-label="Scroll to bottom"
        >
          <ArrowDown className="w-5 h-5" />
        </button>
      )}

      {/* Chat Input Bar (Sticky at bottom, Mobile Safe Area) */}
      <div className="p-3 sm:p-4 bg-white/90 dark:bg-[#090d16]/90 backdrop-blur-md border-t border-slate-200/80 dark:border-slate-800/80 safe-bottom">
        <div className="max-w-4xl mx-auto">
          <form onSubmit={handleSubmit} className="relative flex flex-col rounded-2xl bg-slate-100 dark:bg-slate-900/90 border border-slate-200 dark:border-slate-700/80 shadow-sm focus-within:border-brand-500/60 focus-within:ring-2 focus-within:ring-brand-500/20 transition-all">
            
            {/* Input Textarea */}
            <textarea
              ref={textareaRef}
              rows={1}
              value={inputPrompt}
              onChange={handleInputChange}
              onKeyDown={handleKeyDown}
              placeholder={loadedModel ? `Message ${loadedModel.split('/').pop()}...` : 'Enter a prompt to generate...'}
              className="w-full py-3 pl-4 pr-24 bg-transparent resize-none text-sm sm:text-base text-slate-900 dark:text-slate-100 placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none max-h-48"
            />

            {/* Bottom Controls inside the input box */}
            <div className="flex items-center justify-between px-3 pb-2 pt-1 text-xs text-slate-400">
              <div className="flex items-center space-x-2">
                {isReasoningModel(loadedModel) && settings.enableThinking && (
                  <span className="inline-flex items-center px-2 py-0.5 rounded-md bg-amber-500/10 text-amber-600 dark:text-amber-400 text-[11px] font-medium border border-amber-500/20">
                    <Brain className="w-3 h-3 mr-1" />
                    Reasoning (CoT)
                  </span>
                )}
                <span className="hidden sm:inline text-[11px] text-slate-400">
                  Press Enter to send, Shift+Enter for new line
                </span>
              </div>

              {/* Action Buttons: Send or Stop */}
              <div className="flex items-center space-x-1.5">
                {isStreaming ? (
                  <button
                    onClick={onStopStreaming}
                    type="button"
                    className="p-2 rounded-xl bg-red-500 hover:bg-red-600 text-white font-medium text-xs shadow-md shadow-red-500/20 transition-colors flex items-center space-x-1.5 min-h-[40px] min-w-[40px] justify-center"
                    title="Stop generation"
                    aria-label="Stop generation"
                  >
                    <Square className="w-4 h-4 fill-current" />
                    <span className="hidden sm:inline">Stop</span>
                  </button>
                ) : (
                  <button
                    type="submit"
                    disabled={!inputPrompt.trim()}
                    className="p-2 rounded-xl bg-brand-500 hover:bg-brand-600 disabled:opacity-40 disabled:hover:bg-brand-500 text-white font-medium text-xs shadow-md shadow-brand-500/25 transition-all flex items-center space-x-1.5 min-h-[40px] min-w-[40px] justify-center"
                    aria-label="Send message"
                  >
                    <Send className="w-4 h-4" />
                    <span className="hidden sm:inline">Send</span>
                  </button>
                )}
              </div>
            </div>

          </form>
        </div>
      </div>

    </div>
  );
}
