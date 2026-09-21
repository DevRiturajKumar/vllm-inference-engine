import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { User, Bot, Copy, Check, AlertCircle, Terminal } from 'lucide-react';
import { ThinkingBlock } from './ThinkingBlock';
import { formatModelName, extractThinkingFromContent } from '../utils/format';

// Code block with copy button
function CodeBlock({ children, className, ...props }) {
  const [copied, setCopied] = useState(false);
  const match = /language-(\w+)/.exec(className || '');
  const language = match ? match[1] : '';
  const codeText = String(children).replace(/\n$/, '');

  const handleCopyCode = async () => {
    try {
      await navigator.clipboard.writeText(codeText);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (e) {}
  };

  // If inline code
  if (!match && !String(children).includes('\n')) {
    return (
      <code className="px-1.5 py-0.5 rounded-md bg-slate-200/70 dark:bg-slate-800 text-brand-600 dark:text-brand-400 font-mono text-[0.9em]" {...props}>
        {children}
      </code>
    );
  }

  return (
    <div className="relative my-3 rounded-xl overflow-hidden border border-slate-700/60 bg-[#090d16] text-slate-100 shadow-md">
      <div className="flex items-center justify-between px-3.5 py-1.5 bg-slate-800/80 border-b border-slate-700/60 text-xs text-slate-400">
        <span className="font-mono text-[11px] uppercase tracking-wider text-slate-300">
          {language || 'code'}
        </span>
        <button
          onClick={handleCopyCode}
          type="button"
          className="flex items-center space-x-1 py-1 px-2 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-700/50 transition-colors text-[11px]"
          title="Copy code snippet"
        >
          {copied ? (
            <>
              <Check className="w-3 h-3 text-brand-400" />
              <span className="text-brand-400">Copied!</span>
            </>
          ) : (
            <>
              <Copy className="w-3 h-3" />
              <span>Copy</span>
            </>
          )}
        </button>
      </div>
      <pre className="p-3.5 overflow-x-auto text-xs sm:text-sm font-mono leading-relaxed">
        <code>{codeText}</code>
      </pre>
    </div>
  );
}

export function ChatMessage({ message }) {
  const isUser = message.role === 'user';
  const isSystem = message.role === 'system';
  const [copied, setCopied] = useState(false);

  // Safety fallback: if <think> or </think> tags slipped into content, extract them
  let displayReasoning = message.reasoning || '';
  let displayContent = message.content || '';

  if (!displayReasoning && (
    displayContent.includes('</think>') || 
    displayContent.includes('<think>') || 
    displayContent.includes('</thinking>') || 
    displayContent.includes('<thinking>')
  )) {
    const extracted = extractThinkingFromContent(displayContent);
    if (extracted.reasoning) {
      displayReasoning = extracted.reasoning;
      displayContent = extracted.content;
    }
  }

  const handleCopy = async () => {
    if (!displayContent) return;
    try {
      await navigator.clipboard.writeText(displayContent);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (e) {
      console.error('Failed to copy message:', e);
    }
  };

  if (isSystem) {
    return (
      <div className="flex justify-center my-3">
        <div className="text-xs text-slate-500 dark:text-slate-400 bg-slate-100 dark:bg-slate-800/60 px-3 py-1.5 rounded-full border border-slate-200/60 dark:border-slate-700/60 text-center max-w-lg">
          <span className="font-semibold text-slate-700 dark:text-slate-300">System: </span>
          {message.content}
        </div>
      </div>
    );
  }

  return (
    <div className={`group flex gap-3 sm:gap-4 py-4 px-3 sm:px-6 transition-colors ${
      isUser 
        ? 'bg-transparent' 
        : 'bg-slate-100/40 dark:bg-slate-900/30 border-y border-slate-200/40 dark:border-slate-800/40'
    }`}>
      {/* Avatar */}
      <div className="flex-shrink-0 pt-0.5">
        <div className={`w-8 h-8 sm:w-9 sm:h-9 rounded-xl flex items-center justify-center shadow-sm ${
          isUser 
            ? 'bg-slate-800 text-white dark:bg-slate-200 dark:text-slate-900' 
            : 'bg-brand-500 text-white dark:bg-brand-500 shadow-brand-500/20'
        }`}>
          {isUser ? <User className="w-4 h-4 sm:w-5 sm:h-5" /> : <Bot className="w-4 h-4 sm:w-5 sm:h-5" />}
        </div>
      </div>

      {/* Content Container */}
      <div className="flex-1 min-w-0 space-y-1">
        {/* Header with Role, Model Name, and Copy button */}
        <div className="flex items-center justify-between text-xs text-slate-400 dark:text-slate-500">
          <div className="flex items-center space-x-2">
            <span className="font-semibold text-slate-800 dark:text-slate-200" title={message.model || ''}>
              {isUser ? 'You' : formatModelName(message.model)}
            </span>
            {message.timestamp && (
              <span className="text-[11px] text-slate-400 dark:text-slate-500">
                {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </span>
            )}
          </div>

          <div className="flex items-center space-x-1 opacity-0 group-hover:opacity-100 transition-opacity">
            <button
              onClick={handleCopy}
              type="button"
              className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 hover:bg-slate-200/60 dark:hover:bg-slate-800 transition-colors min-h-[32px] min-w-[32px] flex items-center justify-center"
              title="Copy response text"
              aria-label="Copy response text"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-brand-500" /> : <Copy className="w-3.5 h-3.5" />}
            </button>
          </div>
        </div>

        {/* Reasoning / Thinking Accordion */}
        {(displayReasoning || message.isThinking) && (
          <ThinkingBlock 
            reasoning={displayReasoning} 
            isStreaming={message.isThinking} 
          />
        )}

        {/* Error state */}
        {message.error && (
          <div className="flex items-center space-x-2 p-3 my-2 text-xs text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-950/30 rounded-lg border border-red-200 dark:border-red-900/50">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span>{message.error}</span>
          </div>
        )}

        {/* Message Body with Rich Markdown */}
        <div className="prose-chat text-sm sm:text-[15px] leading-relaxed text-slate-800 dark:text-slate-200 break-words">
          {isUser ? (
            <div className="whitespace-pre-wrap">{displayContent}</div>
          ) : (
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                code: CodeBlock,
              }}
            >
              {displayContent}
            </ReactMarkdown>
          )}

          {message.isStreaming && !message.isThinking && (
            <span className="streaming-cursor" />
          )}
        </div>
      </div>
    </div>
  );
}
