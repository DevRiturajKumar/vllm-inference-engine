import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Header } from './components/Header';
import { Sidebar } from './components/Sidebar';
import { ChatPlayground } from './components/ChatPlayground';
import { ModelManagerModal } from './components/ModelManagerModal';
import { SettingsModal } from './components/SettingsModal';
import { useSettings } from './context/SettingsContext';
import { fetchHealth, streamChatCompletion, unloadModel } from './services/api';
import { extractThinkingFromContent } from './utils/format';

export function App() {
  const { settings, updateSettings } = useSettings();

  // Health and engine state
  const [healthData, setHealthData] = useState(null);
  const [healthLoading, setHealthLoading] = useState(true);

  // Chat state
  const [messages, setMessages] = useState([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const abortControllerRef = useRef(null);

  // Modals and Drawer state
  const [isMobileDrawerOpen, setIsMobileDrawerOpen] = useState(false);
  const [isModelManagerOpen, setIsModelManagerOpen] = useState(false);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);

  // Health polling function
  const checkHealth = useCallback(async () => {
    try {
      const data = await fetchHealth(settings.baseUrl);
      setHealthData(data);
      // Synchronize initial thinking setting from backend .env default if not yet synced
      if (data && typeof data.default_enable_thinking === 'boolean' && !settings.syncedWithBackend) {
        updateSettings({
          enableThinking: data.default_enable_thinking,
          syncedWithBackend: true,
        });
      }
    } catch (err) {
      // Endpoint may be temporarily unreachable or warming up
      setHealthData(null);
    } finally {
      setHealthLoading(false);
    }
  }, [settings.baseUrl, settings.syncedWithBackend, updateSettings]);

  // Initial and recurring health polling
  useEffect(() => {
    checkHealth();
    const interval = setInterval(() => {
      if (document.visibilityState === 'visible') {
        checkHealth();
      }
    }, 4000);
    return () => clearInterval(interval);
  }, [checkHealth]);

  // Send message and stream response
  const handleSendMessage = async (userPrompt) => {
    if (!userPrompt || isStreaming) return;

    const userMessage = {
      role: 'user',
      content: userPrompt,
      timestamp: Date.now(),
    };

    // Construct conversation payload for API
    const conversationHistory = [...messages, userMessage];
    setMessages(conversationHistory);

    // Initial placeholder for assistant message
    const assistantMessageIndex = conversationHistory.length;
    const initialAssistantMsg = {
      role: 'assistant',
      content: '',
      reasoning: '',
      isStreaming: true,
      isThinking: false,
      timestamp: Date.now(),
      model: healthData?.loaded_model || 'vLLM',
    };

    setMessages([...conversationHistory, initialAssistantMsg]);
    setIsStreaming(true);

    // Create abort controller for cancelling stream
    const controller = new AbortController();
    abortControllerRef.current = controller;

    // Build OpenAI-compatible request payload
    const apiMessages = [];
    if (settings.systemPrompt?.trim()) {
      apiMessages.push({ role: 'system', content: settings.systemPrompt.trim() });
    }
    conversationHistory.forEach((m) => {
      apiMessages.push({ role: m.role, content: m.content });
    });

    const requestPayload = {
      model: healthData?.loaded_model || 'default',
      messages: apiMessages,
      max_tokens: settings.maxTokens,
      temperature: settings.temperature,
      top_p: settings.topP,
      top_k: settings.topK,
      repetition_penalty: settings.repetitionPenalty,
      enable_thinking: settings.enableThinking,
    };

    let accumulatedContent = '';
    let accumulatedReasoning = '';

    await streamChatCompletion(
      settings.baseUrl,
      requestPayload,
      {
        onChunk: (chunk) => {
          const choice = chunk.choices?.[0];
          if (!choice) return;

          const delta = choice.delta || {};
          let hasUpdated = false;

          // 1. Handle reasoning tokens (DeepSeek-R1 / QwQ format)
          const reasoningDelta = delta.reasoning || delta.reasoning_content;
          if (reasoningDelta) {
            accumulatedReasoning += reasoningDelta;
            hasUpdated = true;
          }

          // 2. Handle standard content tokens
          const contentDelta = delta.content;
          if (contentDelta) {
            accumulatedContent += contentDelta;
            hasUpdated = true;
          }

          // 3. Fallback: if reasoning was sent inside content with </think>, extract it
          if (!accumulatedReasoning && (accumulatedContent.includes('</think>') || accumulatedContent.includes('</thinking>'))) {
            const extracted = extractThinkingFromContent(accumulatedContent);
            if (extracted.reasoning) {
              accumulatedReasoning = extracted.reasoning;
              accumulatedContent = extracted.content;
              hasUpdated = true;
            }
          }

          if (hasUpdated) {
            setMessages((prev) => {
              const next = [...prev];
              const idx = next.length - 1;
              if (idx >= 0 && next[idx].role === 'assistant') {
                next[idx] = {
                  ...next[idx],
                  content: accumulatedContent,
                  reasoning: accumulatedReasoning,
                  isThinking: Boolean(accumulatedReasoning && !accumulatedContent),
                  isStreaming: true,
                };
              }
              return next;
            });
          }
        },
        onDone: (result) => {
          setIsStreaming(false);
          abortControllerRef.current = null;

          // Final safety extraction of thinking blocks
          if (!accumulatedReasoning && (accumulatedContent.includes('</think>') || accumulatedContent.includes('</thinking>'))) {
            const extracted = extractThinkingFromContent(accumulatedContent);
            if (extracted.reasoning) {
              accumulatedReasoning = extracted.reasoning;
              accumulatedContent = extracted.content;
            }
          }

          setMessages((prev) => {
            const next = [...prev];
            const idx = next.length - 1;
            if (idx >= 0 && next[idx].role === 'assistant') {
              next[idx] = {
                ...next[idx],
                isStreaming: false,
                isThinking: false,
                content: accumulatedContent || (result?.aborted ? '(Generation stopped)' : ''),
                reasoning: accumulatedReasoning,
              };
            }
            return next;
          });
          // Refresh health stats after inference
          checkHealth();
        },
        onError: (err) => {
          setIsStreaming(false);
          abortControllerRef.current = null;
          setMessages((prev) => {
            const next = [...prev];
            const idx = next.length - 1;
            if (idx >= 0 && next[idx].role === 'assistant') {
              next[idx] = {
                ...next[idx],
                isStreaming: false,
                isThinking: false,
                error: err.message || 'An error occurred during token generation.',
              };
            }
            return next;
          });
        },
        signal: controller.signal,
      }
    );
  };

  // Stop in-flight streaming
  const handleStopStreaming = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
  };

  // Unload model
  const handleUnloadModel = async () => {
    if (confirm('Are you sure you want to unload the active model from GPU VRAM?')) {
      try {
        await unloadModel(settings.baseUrl);
        await checkHealth();
      } catch (err) {
        alert(err.message || 'Failed to unload model');
      }
    }
  };

  // Clear chat
  const handleClearChat = () => {
    if (messages.length === 0) return;
    if (confirm('Clear current chat history?')) {
      setMessages([]);
    }
  };

  return (
    <div className="flex flex-col h-screen w-full overflow-hidden bg-slate-50 dark:bg-[#0b0f19] text-slate-900 dark:text-slate-100">
      
      {/* Top Navbar */}
      <Header 
        healthData={healthData}
        healthLoading={healthLoading}
        onOpenModelManager={() => setIsModelManagerOpen(true)}
        onOpenSettings={() => setIsSettingsOpen(true)}
        isMobileDrawerOpen={isMobileDrawerOpen}
        setIsMobileDrawerOpen={setIsMobileDrawerOpen}
      />

      {/* Main Content (Sidebar + Chat Area) */}
      <div className="flex-1 flex overflow-hidden">
        <Sidebar 
          healthData={healthData}
          healthLoading={healthLoading}
          onRefreshHealth={checkHealth}
          onOpenModelManager={() => {
            setIsMobileDrawerOpen(false);
            setIsModelManagerOpen(true);
          }}
          onUnloadModel={handleUnloadModel}
          onClearChat={handleClearChat}
          isMobileDrawerOpen={isMobileDrawerOpen}
          setIsMobileDrawerOpen={setIsMobileDrawerOpen}
        />

        <ChatPlayground 
          messages={messages}
          isStreaming={isStreaming}
          onSendMessage={handleSendMessage}
          onStopStreaming={handleStopStreaming}
          loadedModel={healthData?.loaded_model}
        />
      </div>

      {/* Modals */}
      <ModelManagerModal 
        isOpen={isModelManagerOpen}
        onClose={() => setIsModelManagerOpen(false)}
        currentModel={healthData?.loaded_model}
        onModelChanged={checkHealth}
      />

      <SettingsModal 
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        onConnectionChanged={checkHealth}
      />

    </div>
  );
}
