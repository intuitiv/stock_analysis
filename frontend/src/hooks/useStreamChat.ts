import { useState, useEffect, useCallback, useRef } from 'react';
import { ChatMessageResponseData, MessageRole, StreamEvent, ProcessingEventType } from '../utils/api';

export interface ProcessingUpdate {
  type: ProcessingEventType;  // Use ProcessingEventType enum for all event types
  message: string;
  timestamp?: string;
  data?: any;
  metadata?: any;
}

interface ErrorData {
  error?: string;
  message?: string;
}

let messageBuffer = '';
let updateBuffer: ProcessingUpdate[] = [];

// WebSocket state mapping for better error handling
type WebSocketStateMap = {
  [key: number]: string;
};

const WS_STATE_MAP: WebSocketStateMap = {
  [WebSocket.CONNECTING]: 'CONNECTING',
  [WebSocket.OPEN]: 'OPEN',
  [WebSocket.CLOSING]: 'CLOSING',
  [WebSocket.CLOSED]: 'CLOSED'
};

const getWebSocketStateString = (ws: WebSocket | null): string => {
  if (!ws) return 'NONE';
  const stateNum = ws.readyState;
  const stateName = WS_STATE_MAP[stateNum] || 'UNKNOWN';
  return `${stateName} (${stateNum})`;
};

// Helper function for consistent close handling
const determinisicClose = (ws: WebSocket | null): boolean => {
  if (!ws) return true;
  if (ws.readyState === WebSocket.CLOSED) return true;
  if (ws.readyState === WebSocket.CLOSING) return true;
  return false;
};

const createWebSocketWithAuth = (baseUrl: string, token: string, sessionId?: number): WebSocket => {
  const wsUrl = new URL(baseUrl.replace(/^http/, 'ws'));
  wsUrl.pathname = `/api/v1/chat/ws/${sessionId || '0'}`;

  // Create WebSocket with protocol that includes the token
  // This will be sent in the Sec-WebSocket-Protocol header
  return new WebSocket(wsUrl.toString(), `bearer.${token}`);
};

type CleanupStatus = 'idle' | 'in_progress' | 'completed' | 'failed';

interface StreamChatHookResult {
  currentStreamedMessage: string;
  processingUpdates: ProcessingUpdate[];
  finalAssistantMessage: ChatMessageResponseData | null;
  isProcessing: boolean;
  error: string | null;
  cleanupStatus: CleanupStatus;
  sendMessage: (messageContent: string, sessionId?: number) => Promise<void>;
  closeStream: () => Promise<void>;
}

export const useStreamChat = (apiBaseUrl: string, getToken: () => string | null): StreamChatHookResult => {
  const [currentStreamedMessage, setCurrentStreamedMessage] = useState<string>('');
  const [processingUpdates, setProcessingUpdates] = useState<ProcessingUpdate[]>([]);
  const [finalAssistantMessage, setFinalAssistantMessage] = useState<ChatMessageResponseData | null>(null);
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [hasError, setHasError] = useState<boolean>(false);
  const [cleanupStatus, setCleanupStatus] = useState<CleanupStatus>('idle');
  const [cleanupQueue, setCleanupQueue] = useState<Array<() => Promise<void>>>([]);
  
  // Track cleanup attempts for retry logic
  const cleanupAttemptRef = useRef<number>(0);

  // Process cleanup queue sequentially
  useEffect(() => {
    const processQueue = async () => {
      if (cleanupQueue.length > 0) {
        console.debug(`Processing cleanup queue (${cleanupQueue.length} items)...`);
        for (const cleanup of cleanupQueue) {
          await cleanup();
        }
        setCleanupQueue([]);
        console.debug('Cleanup queue processing complete');
      }
    };
    processQueue();
  }, [cleanupQueue]);

  const closeStream = useCallback(async () => {
    const currentWs = ws;
    if (!currentWs) return;

    console.debug('Starting WebSocket cleanup sequence...');
    
    const MAX_RETRIES = 3;
    const RETRY_DELAY = 100; // ms

    const attemptClose = async (retries = cleanupAttemptRef.current): Promise<void> => {
      setCleanupStatus('in_progress');
      cleanupAttemptRef.current = retries;

      try {
        if (currentWs.readyState === WebSocket.OPEN) {
          console.debug('Sending CLOSE event...');
          await currentWs.send(JSON.stringify({ 
            event: ProcessingEventType.CLOSE, 
            timestamp: new Date().toISOString() 
          }));
        }

        console.debug('Executing cleanup tasks...');
        currentWs.close();
        currentWs.onclose = null;
        currentWs.onerror = null;
        currentWs.onmessage = null;

        setCleanupStatus('completed');

      } catch (err) {
        console.error(`Attempt ${retries + 1} failed:`, err);
        if (retries < MAX_RETRIES) {
          console.debug(`Retrying cleanup in ${RETRY_DELAY}ms...`);
          await new Promise(resolve => setTimeout(resolve, RETRY_DELAY));
          return attemptClose(retries + 1);
        }
        throw err;
      }
    };

    try {
      await attemptClose();
      
      // Ensure state updates are properly synchronized
      await new Promise<void>(resolve => {
        requestAnimationFrame(() => {
          setWs(null);
          // Wait for setWs to complete
          requestAnimationFrame(() => {
            setIsProcessing(false);
            // Wait for setIsProcessing to complete
            requestAnimationFrame(() => {
              console.debug('WebSocket cleanup completed:', {
                wsState: getWebSocketStateString(currentWs),
                isProcessing: false,
                hasWs: false,
                cleanupStatus: 'completed',
                timestamp: new Date().toISOString()
              });
              resolve();
            });
          });
        });
      });
    } catch (err) {
      console.error('Failed to close WebSocket cleanly:', err);
      setCleanupStatus('failed');

      // Ensure cleanup completes even on error
      await new Promise<void>(resolve => {
        requestAnimationFrame(() => {
          console.debug('Executing emergency cleanup after error');
          if (currentWs) {
            try {
              currentWs.close();
            } catch (closeErr) {
              console.warn('Error during emergency close:', closeErr);
            }
            currentWs.onclose = null;
            currentWs.onerror = null;
            currentWs.onmessage = null;
          }
          
          // Force state reset
          setWs(null);
          requestAnimationFrame(() => {
            setIsProcessing(false);
            setCleanupStatus('completed'); // Set completed even after failure
            cleanupAttemptRef.current = 0; // Reset attempt counter
            console.debug('Emergency cleanup completed');
            resolve();
          });
        });
      });
    }
  }, [ws]);

  useEffect(() => {
    let pongTimeout: ReturnType<typeof setTimeout>;

    const resetPongTimeout = () => {
      if (pongTimeout) clearTimeout(pongTimeout);
      pongTimeout = setTimeout(() => {
        if (ws?.readyState === WebSocket.OPEN) {
          console.warn('No pong received, closing connection:', {
            wsState: getWebSocketStateString(ws),
            timestamp: new Date().toISOString()
          });
          closeStream();
        }
      }, 40000); // Give generous timeout for pong (40s)
    };

    if (ws) {
      // Error handling function
      const handleError = (errorData: any) => {
        const now = new Date().toISOString();
        const errorMsg = typeof errorData === 'object' && errorData !== null
          ? (errorData as ErrorData).error || (errorData as ErrorData).message || 'An unknown error occurred'
          : typeof errorData === 'string'
            ? errorData
            : 'An unknown error occurred';
        
        const errorUpdate: ProcessingUpdate = {
          type: ProcessingEventType.ERROR,
          message: errorMsg,
          timestamp: now
        };
        updateBuffer.push(errorUpdate);
        setProcessingUpdates([...updateBuffer]);
        setError(errorMsg);
        setHasError(true);
        setIsProcessing(false);
        closeStream();
      };

      // Handle all messages including pings
      const messageHandler = (event: MessageEvent) => {
        try {
          const streamEvent = JSON.parse(event.data);

          if (streamEvent.event === ProcessingEventType.PING) {
            resetPongTimeout();
            ws.send(JSON.stringify({ event: ProcessingEventType.PONG, timestamp: new Date().toISOString() }));
            return;
          }

          // Process other events
          const now = new Date().toISOString();

          // Helper function to add updates
          const addUpdate = (type: ProcessingEventType, message: string, metadata?: any) => {
            const update: ProcessingUpdate = {
              type,
              message,
              timestamp: streamEvent.timestamp || now,
              data: metadata || streamEvent.metadata
            };
            updateBuffer.push(update);
            requestAnimationFrame(() => {
              setProcessingUpdates([...updateBuffer]);
            });
          };

          switch (streamEvent.event) {
            case ProcessingEventType.PROCESSING:
            case ProcessingEventType.INTENT:
            case ProcessingEventType.ANALYSIS:
            case ProcessingEventType.DATA_FETCH:
            case ProcessingEventType.THOUGHT:
            case ProcessingEventType.LEARNING:
            case ProcessingEventType.INFO:
              addUpdate(
                streamEvent.event,
                typeof streamEvent.data === 'string' ? streamEvent.data : JSON.stringify(streamEvent.data)
              );
              
              if (streamEvent.metadata?.sequence === 998) {
                try {
                  const finalData = JSON.parse(streamEvent.data as string) as ChatMessageResponseData;
                  setCurrentStreamedMessage(finalData.content);
                  setFinalAssistantMessage(finalData);
                  
                  // Add final message content as a new update
                  addUpdate(
                    ProcessingEventType.INFO,
                    finalData.content
                  );
                } catch (err) {
                  console.error('Failed to parse final response:', {
                  error: err instanceof Error ? err.message : 'Unknown error',
                  data: streamEvent.data,
                  timestamp: now,
                  wsState: getWebSocketStateString(ws)
                });
                }
              } else if (streamEvent.metadata?.sequence === 999) {
                setIsProcessing(false);
                closeStream(); // Close immediately for completion
              }
              break;

            case ProcessingEventType.FINAL:
              console.debug('Final response received:', streamEvent.data);
              try {
                // Parse the final response
                const finalData = JSON.parse(streamEvent.data as string) as ChatMessageResponseData;
                setCurrentStreamedMessage(finalData.content);
                setFinalAssistantMessage(finalData);
                
                // Add final message content
                addUpdate(
                  ProcessingEventType.INFO,
                  finalData.content
                );
                
                // Add completion message
                addUpdate(
                  ProcessingEventType.INFO,
                  'Processing complete'
                );
                
                setIsProcessing(false);
                closeStream();
              } catch (err) {
                console.error('Failed to parse final message:', {
                error: err instanceof Error ? err.message : 'Unknown error',
                data: streamEvent.data,
                wsState: getWebSocketStateString(ws),
                timestamp: now
              });
                handleError('Failed to process response');
              }
              break;

            case ProcessingEventType.ERROR:
              handleError(streamEvent.data);
              break;

            default:
              console.warn('Unhandled event type:', streamEvent.event);
          }
        } catch (err) {
          console.error('Failed to process message:', {
            error: err instanceof Error ? err.message : 'Unknown error',
            wsState: getWebSocketStateString(ws),
            eventData: event.data,
            timestamp: new Date().toISOString()
          });
          handleError('Failed to process message');
        }
      };

      // Single message handler for all events
      ws.onmessage = messageHandler;
    }

    return () => {
      if (pongTimeout) clearTimeout(pongTimeout);
      closeStream(); // Cleanup on unmount
    };
  }, [ws, closeStream]);

  // Debug state changes
  useEffect(() => {
      console.debug('Chat state updated:', {
        isProcessing,
        hasError,
        errorMessage: error,
        hasFinalMessage: !!finalAssistantMessage,
        updatesCount: processingUpdates.length,
        currentMessageLength: currentStreamedMessage.length,
        wsState: getWebSocketStateString(ws),
        cleanupStatus,
        cleanupAttempt: cleanupAttemptRef.current,
        timestamp: new Date().toISOString()
      });
    }, [isProcessing, error, hasError, finalAssistantMessage, processingUpdates, currentStreamedMessage, ws, cleanupStatus]);

  const sendMessage = useCallback(async (messageContent: string, sessionId?: number) => {
      console.debug('Starting new message sequence, cleaning up previous state...');
      closeStream(); // Close any existing WebSocket

      console.debug('Waiting for cleanup to complete...');
      await new Promise(resolve => setTimeout(resolve, 100));
      console.debug('Previous connection cleanup complete');

    // Reset state and buffers
    messageBuffer = '';
    updateBuffer = [];
    setIsProcessing(true);
    setCurrentStreamedMessage('');
    setProcessingUpdates([]);
    setFinalAssistantMessage(null);
    setError(null);
    setHasError(false); // Reset error state for new message
    setCleanupStatus('idle'); // Reset cleanup status
    cleanupAttemptRef.current = 0; // Reset cleanup attempt counter

    const token = getToken();
    if (!token) {
      setError('Authentication token not found.');
      setIsProcessing(false);
      return;
    }

    try {
      console.debug('Creating new WebSocket connection with params:', {
        baseUrl: apiBaseUrl,
        hasToken: !!token,
        sessionId,
      });
      
      const newWs = createWebSocketWithAuth(apiBaseUrl, token, sessionId);
      console.debug('WebSocket instance created:', {
        wsState: getWebSocketStateString(newWs),
        protocol: newWs.protocol,
        url: newWs.url
      });
      
      setWs(newWs);
      console.debug('WebSocket instance stored in state');
      
      newWs.onopen = (event) => {
        console.debug('WebSocket connection established:', event);
        console.debug('Sending initial message:', { content: messageContent, sessionId });
        newWs.send(JSON.stringify({
          content: messageContent,
          sessionId,
        }));
      };

      // Define helper functions
      const addMessage = (type: ProcessingEventType, message: string, metadata?: any) => {
        const update: ProcessingUpdate = {
          type,
          message,
          timestamp: new Date().toISOString(),
          data: metadata
        };
        updateBuffer.push(update);
        requestAnimationFrame(() => {
          setProcessingUpdates([...updateBuffer]);
        });
      };
      
      newWs.onmessage = async (event) => {
        const streamEvent: StreamEvent = JSON.parse(event.data);
        const now = new Date().toISOString();
        
        const addMessage = (type: ProcessingEventType, message: string, metadata?: any) => {
          const update: ProcessingUpdate = {
            type,
            message,
            timestamp: streamEvent.timestamp || now,
            data: metadata || streamEvent.metadata
          };
          updateBuffer.push(update);
          requestAnimationFrame(() => {
            setProcessingUpdates([...updateBuffer]);
          });
        };

        switch (streamEvent.event) {
          case ProcessingEventType.PROCESSING:
          case ProcessingEventType.INTENT:
          case ProcessingEventType.ANALYSIS:
          case ProcessingEventType.DATA_FETCH:
          case ProcessingEventType.THOUGHT:
          case ProcessingEventType.LEARNING:
          case ProcessingEventType.INFO:
              addMessage(
                streamEvent.event,
                typeof streamEvent.data === 'string' ? streamEvent.data : JSON.stringify(streamEvent.data),
                streamEvent.metadata
            );
            
            // Handle special info messages with sequences
            if (streamEvent.metadata?.sequence === 998) {
              console.debug('Received sequence 998 - Final response data:', streamEvent);
              try {
                const finalData = JSON.parse(streamEvent.data as string) as ChatMessageResponseData;
                console.debug('Parsed final response:', finalData);
                setCurrentStreamedMessage(finalData.content);
                setFinalAssistantMessage(finalData);
                
              // Add final message content as a new update
              console.debug('Adding final message to updates:', {
                contentLength: finalData.content.length,
                messageUpdates: updateBuffer.length,
                timestamp: now,
                isProcessing,
                wsState: getWebSocketStateString(ws)
              });

              addMessage(
                ProcessingEventType.INFO,
                finalData.content
              );
              
              console.debug('Final message content added to updates');
              console.debug('Current update buffer:', updateBuffer);
              }
              catch (err) {
                console.error('Failed to parse sequence 998 response:', {
                  error: err instanceof Error ? err.message : 'Unknown error',
                  data: streamEvent.data,
                  wsState: getWebSocketStateString(ws),
                  timestamp: now,
                  metadata: streamEvent.metadata
                });
              }
            } else if (streamEvent.metadata?.sequence === 999) {
              console.debug('Received sequence 999 - Starting completion sequence');
              
              // Ensure all state updates are complete before closing
              await new Promise<void>((resolve) => {
                requestAnimationFrame(async () => {
                  console.debug('Finalizing chat session...', {
                    messageCount: updateBuffer.length,
                    hasFinalMessage: !!finalAssistantMessage,
                    currentState: {
                      isProcessing,
                      wsState: getWebSocketStateString(ws),
                      hasError
                    }
                  });
                  
                  setIsProcessing(false);
                  // Wait for state update to complete
                  await new Promise(resolve => setTimeout(resolve, 50));
                  closeStream();
                  resolve();
                });
              });
              
              console.debug('Chat session completion sequence finished');
            }
            break;

          case ProcessingEventType.FINAL:
            console.debug('Final response received:', streamEvent.data);
            try {
              // Parse the final response
              const finalData = JSON.parse(streamEvent.data as string) as ChatMessageResponseData;
              
              // Ensure state updates are synchronized
              await new Promise<void>((resolve) => {
                requestAnimationFrame(async () => {
                  console.debug('Processing final response...', {
                    contentLength: finalData.content.length,
                    hasAssistantDetails: !!finalData.assistant_response_details,
                  });
                  
                  setCurrentStreamedMessage(finalData.content);
                  setFinalAssistantMessage(finalData);
                  
                  // Add final message content
                  addMessage(
                    ProcessingEventType.INFO,
                    finalData.content
                  );
                  
                  // Add completion message
                  addMessage(
                    ProcessingEventType.INFO,
                    'Processing complete'
                  );
                  
                  setIsProcessing(false);
                  // Wait for state updates to complete
                  await new Promise(resolve => setTimeout(resolve, 50));
                  closeStream();
                  resolve();
                });
              });
              
              console.debug('Final response processing complete');
            } catch (err) {
              console.error('Failed to parse final message:', {
                error: err instanceof Error ? err.message : 'Unknown error',
                data: streamEvent.data,
                wsState: getWebSocketStateString(ws),
                timestamp: now,
                metadata: streamEvent.metadata
              });
              const errorUpdate: ProcessingUpdate = {
                type: ProcessingEventType.ERROR,
                message: 'Error processing final response',
                timestamp: now
              };
              updateBuffer.push(errorUpdate);
              setProcessingUpdates([...updateBuffer]);
              setError('Failed to process response');
              setIsProcessing(false);
              closeStream();
            }
            break;

          case ProcessingEventType.ERROR:
            console.error('Stream event error:', {
              error: typeof streamEvent.data === 'object' ? JSON.stringify(streamEvent.data) : streamEvent.data,
              wsState: getWebSocketStateString(ws),
              timestamp: now,
              metadata: streamEvent.metadata
            });
            if (!hasError && streamEvent.data) {
              const errorData = streamEvent.data as ErrorData;
              // Extract error message
              const errorMsg = typeof errorData === 'object' && errorData !== null
                ? (errorData as ErrorData).error || (errorData as ErrorData).message || 'An unknown error occurred'
                : typeof errorData === 'string'
                  ? errorData
                  : 'An unknown error occurred';
              
              // Create final message with preserved updates
              const finalMessage: ChatMessageResponseData = {
                role: MessageRole.ASSISTANT,
                content: '',
                timestamp: now,
                assistant_response_details: {
                  naetra_thought_process: [
                    ...updateBuffer.map(u => u.message),
                    `Error: ${errorMsg}`
                  ]
                }
              };
              
              setFinalAssistantMessage(finalMessage);
              setProcessingUpdates(prev => [
                ...prev,
                { type: ProcessingEventType.ERROR, message: errorMsg, timestamp: now } as ProcessingUpdate
              ]);
              setError(errorMsg);
              setHasError(true);
              setIsProcessing(false);
              closeStream();
            }
            break;

          default:
            console.warn('Unhandled event type:', streamEvent.event);
        }
      };

      newWs.onerror = (err) => {
        const now = new Date().toISOString();
        console.error('WebSocket error:', {
          wsState: getWebSocketStateString(newWs),
          errorType: err.type,
          timestamp: now
        });
        
        // Only handle WebSocket connection errors, not message errors
        if (!hasError && err instanceof Event && err.type === 'error') {
          const errorUpdate: ProcessingUpdate = {
            type: ProcessingEventType.ERROR,
            message: 'Failed to connect to the streaming service.',
            timestamp: now
          };
          updateBuffer.push(errorUpdate);
          setProcessingUpdates([...updateBuffer]);
          setError(errorUpdate.message);
          setHasError(true);
        }
        setIsProcessing(false);
        closeStream();
      };

      newWs.onclose = (event) => {
        console.debug('WebSocket connection closed:', {
          wsState: getWebSocketStateString(ws),
          code: event.code,
          reason: event.reason || 'no reason provided',
          wasClean: event.wasClean,
          finalMessage: !!finalAssistantMessage,
          hasError: hasError
        });
        
        if (!finalAssistantMessage && !error) {
          const errorUpdate: ProcessingUpdate = {
            type: ProcessingEventType.ERROR,
            message: `Connection closed unexpectedly. Code: ${event.code}, Reason: ${event.reason || 'none provided'}`,
            timestamp: new Date().toISOString()
          };
          updateBuffer.push(errorUpdate);
          setProcessingUpdates([...updateBuffer]);
          setError(errorUpdate.message);
        }
        setIsProcessing(false);
        console.debug('WebSocket cleanup complete:', {
          wsState: getWebSocketStateString(ws),
          isProcessing: false,
          cleanupStatus,
          hasError,
          timestamp: new Date().toISOString()
        });
      };
    } catch (err) {
      const now = new Date().toISOString();
      console.error('Failed to initialize chat connection:', {
        error: err instanceof Error ? err.message : 'Unknown error',
        timestamp: now,
        apiBaseUrl,
        hasToken: !!token,
        sessionId
      });
      const errorUpdate: ProcessingUpdate = {
        type: ProcessingEventType.ERROR,
        message: 'Failed to initialize chat stream.',
        timestamp: new Date().toISOString()
      };
      updateBuffer.push(errorUpdate);
      setProcessingUpdates([...updateBuffer]);
      setError(errorUpdate.message);
      setIsProcessing(false);
    }
  }, [apiBaseUrl, getToken, closeStream]);

  // Debug state changes
  useEffect(() => {
    console.debug('Chat state updated:', {
      isProcessing,
      hasError,
      errorMessage: error,
      hasFinalMessage: !!finalAssistantMessage,
      updatesCount: processingUpdates.length,
      currentMessageLength: currentStreamedMessage.length,
      wsState: getWebSocketStateString(ws),
      cleanupStatus,
      cleanupAttempt: cleanupAttemptRef.current
    });
  }, [isProcessing, error, hasError, finalAssistantMessage, processingUpdates, currentStreamedMessage, ws, cleanupStatus]);

  return {
    currentStreamedMessage,
    processingUpdates,
    finalAssistantMessage,
    isProcessing,
    error,
    cleanupStatus,
    sendMessage,
    closeStream,
  };
};
