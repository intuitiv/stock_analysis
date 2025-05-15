import { useState, useEffect, useCallback } from 'react';
import { ChatMessageResponseData, MessageRole, StreamEvent } from '../utils/api';

export interface ProcessingUpdate {
  type: 'thought' | 'learning' | 'actionable_insight' | 'chart_data' | 'error' | 'info' | 'processing' | 'intent' | 'analysis' | 'data_fetch';
  message: string;
  timestamp?: string;
  data?: any;
}

let messageBuffer = '';
let updateBuffer: ProcessingUpdate[] = [];

const createWebSocketWithAuth = (baseUrl: string, token: string, sessionId?: number): WebSocket => {
  const wsUrl = new URL(baseUrl.replace(/^http/, 'ws'));
  wsUrl.pathname = `/api/v1/chat/ws/${sessionId || '0'}`;

  // Create WebSocket with protocol that includes the token
  // This will be sent in the Sec-WebSocket-Protocol header
  return new WebSocket(wsUrl.toString(), `bearer.${token}`);
};

export const useStreamChat = (apiBaseUrl: string, getToken: () => string | null) => {
  const [currentStreamedMessage, setCurrentStreamedMessage] = useState<string>('');
  const [processingUpdates, setProcessingUpdates] = useState<ProcessingUpdate[]>([]);
  const [finalAssistantMessage, setFinalAssistantMessage] = useState<ChatMessageResponseData | null>(null);
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [hasError, setHasError] = useState<boolean>(false);

  const closeStream = useCallback(() => {
    if (ws) {
      ws.close();
      ws.onclose = null;
      ws.onerror = null;
      ws.onmessage = null;
      setWs(null);
      setIsProcessing(false);
    }
  }, [ws]);

  useEffect(() => {
    return () => {
      closeStream(); // Cleanup on unmount
    };
  }, [closeStream]);

  const sendMessage = useCallback(async (messageContent: string, sessionId?: number) => {
    closeStream(); // Close any existing WebSocket

    // Small delay to ensure previous connection is fully closed
    await new Promise(resolve => setTimeout(resolve, 100));

    // Reset state and buffers
    messageBuffer = '';
    updateBuffer = [];
    setIsProcessing(true);
    setCurrentStreamedMessage('');
    setProcessingUpdates([]);
    setFinalAssistantMessage(null);
    setError(null);
    setHasError(false); // Reset error state for new message

    const token = getToken();
    if (!token) {
      setError('Authentication token not found.');
      setIsProcessing(false);
      return;
    }

    try {
      const newWs = createWebSocketWithAuth(apiBaseUrl, token, sessionId);
      setWs(newWs);

      newWs.onopen = () => {
        newWs.send(JSON.stringify({
          content: messageContent,
          sessionId,
        }));
      };

      newWs.onmessage = async (event) => {
        const streamEvent: StreamEvent = JSON.parse(event.data);
        const now = new Date().toISOString();

        switch (streamEvent.event) {
          case 'processing':
          case 'intent':
          case 'analysis':
          case 'data_fetch':
            // Add to thought process immediately
            const update: ProcessingUpdate = {
              type: streamEvent.event,
              message: streamEvent.data,
              timestamp: streamEvent.timestamp || now
            };
            updateBuffer.push(update);
            setProcessingUpdates([...updateBuffer]);
            break;

          case 'final':
            try {
              // Parse the final response
              const finalData = JSON.parse(streamEvent.data as string) as ChatMessageResponseData;
              
              // Add completion message
              const completionUpdate: ProcessingUpdate = {
                type: 'info',
                message: 'Processing complete',
                timestamp: streamEvent.timestamp || now
              };
              updateBuffer.push(completionUpdate);
              
              // Update state
              requestAnimationFrame(() => {
                setProcessingUpdates([...updateBuffer]);
                setCurrentStreamedMessage(finalData.content);
                setFinalAssistantMessage(finalData);
                setIsProcessing(false);
                closeStream();
              });
            } catch (err) {
              console.error('Error parsing final message:', err);
              const errorUpdate: ProcessingUpdate = {
                type: 'error',
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

          case 'error':
            console.error('Stream error:', streamEvent.data);
            if (!hasError && streamEvent.data) {
              const errorData = streamEvent.data;
              // Extract error message
              const errorMsg = typeof errorData === 'object'
                ? errorData.error || errorData.message || 'An unknown error occurred.'
                : typeof errorData === 'string'
                  ? errorData
                  : 'An unknown error occurred.';
              
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
                { type: 'error', message: errorMsg, timestamp: now }
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
        console.error('WebSocket failed:', err);
        // Only handle WebSocket connection errors, not message errors
        if (!hasError && err instanceof Event && err.type === 'error') {
          const errorUpdate: ProcessingUpdate = {
            type: 'error',
            message: 'Failed to connect to the streaming service.',
            timestamp: new Date().toISOString()
          };
          updateBuffer.push(errorUpdate);
          setProcessingUpdates([...updateBuffer]);
          setError(errorUpdate.message);
          setHasError(true);
        }
        setIsProcessing(false);
        closeStream();
      };

      newWs.onclose = () => {
        if (!finalAssistantMessage && !error) {
          const errorUpdate: ProcessingUpdate = {
            type: 'error',
            message: 'Connection closed unexpectedly.',
            timestamp: new Date().toISOString()
          };
          updateBuffer.push(errorUpdate);
          setProcessingUpdates([...updateBuffer]);
          setError(errorUpdate.message);
        }
        setIsProcessing(false);
      };
    } catch (err) {
      console.error("Error setting up EventSource:", err);
      const errorUpdate: ProcessingUpdate = {
        type: 'error',
        message: 'Failed to initialize chat stream.',
        timestamp: new Date().toISOString()
      };
      updateBuffer.push(errorUpdate);
      setProcessingUpdates([...updateBuffer]);
      setError(errorUpdate.message);
      setIsProcessing(false);
    }
  }, [apiBaseUrl, getToken, closeStream]);

  return {
    currentStreamedMessage,
    processingUpdates,
    finalAssistantMessage,
    isProcessing,
    error,
    sendMessage,
    closeStream,
  };
};
