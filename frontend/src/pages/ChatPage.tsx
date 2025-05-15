import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  Container,
  IconButton,
  useTheme,
  Paper,
} from '@mui/material';
import { alpha } from '@mui/material/styles';
import SendIcon from '@mui/icons-material/Send';
import StopIcon from '@mui/icons-material/Stop';
import { useAuth } from '../contexts/AuthContext';
import { useStreamChat } from '../hooks/useStreamChat';
import ChatMessage from '../components/features/chat/ChatMessage';
import { MessageRole } from '../utils/api';
import { config } from '../config';
import TextareaAutosize from 'react-textarea-autosize';

const ChatPage: React.FC = () => {
  const theme = useTheme();
  const { getToken } = useAuth();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [inputValue, setInputValue] = useState('');

  interface ChatMessage {
    id: string;
    role: MessageRole;
    content: string;
    timestamp: string;
    messageDetails?: any;
    isStreaming?: boolean;
  }

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<number | undefined>();

  const {
    processingUpdates,
    currentStreamedMessage,
    finalAssistantMessage,
    error,
    isProcessing,
    sendMessage,
    closeStream
  } = useStreamChat(config.apiBaseUrl, getToken);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, currentStreamedMessage]);

  const handleStopMessage = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    closeStream();
    
    // Update the current streaming message to indicate it was stopped
    setMessages(prev => prev.map(msg =>
      msg.isStreaming
        ? {
            ...msg,
            content: msg.content + "\n\n[Response stopped by user]",
            isStreaming: false,
            messageDetails: {
              ...msg.messageDetails,
              assistant_response_details: {
                ...msg.messageDetails?.assistant_response_details,
                naetra_thought_process: [
                  ...(msg.messageDetails?.assistant_response_details?.naetra_thought_process || []),
                  "Response stopped by user"
                ]
              }
            }
          }
        : msg
    ));
  };

  const handleSendMessage = async () => {
    if (!inputValue.trim()) return;

    const messageId = Date.now().toString();
    const timestamp = new Date().toISOString();

    const newUserMessage: ChatMessage = {
      id: `user-${messageId}`,
      role: MessageRole.USER,
      content: inputValue,
      timestamp
    };

    const streamingMessage: ChatMessage = {
      id: `assistant-${messageId}`,
      role: MessageRole.ASSISTANT,
      content: '',
      timestamp,
      isStreaming: true
    };

    setMessages(prev => [...prev, newUserMessage, streamingMessage]);
    setInputValue('');

    try {
      await sendMessage(inputValue, currentSessionId);
    } catch (err) {
      console.error('Send error:', err);
      setMessages(prev => prev.map(msg =>
        msg.id === `assistant-${messageId}`
          ? { ...msg, content: 'Failed to send message.', isStreaming: false }
          : msg
      ));
    }
  };

  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSendMessage();
    }
  };

  useEffect(() => {
    if (isProcessing && currentStreamedMessage) {
      setMessages(prev => prev.map(msg =>
        msg.isStreaming
          ? {
              ...msg,
              content: currentStreamedMessage,
              messageDetails: {
                role: MessageRole.ASSISTANT,
                content: currentStreamedMessage,
                timestamp: new Date().toISOString(),
                session_id: currentSessionId,
                assistant_response_details: {
                  naetra_thought_process: processingUpdates.map(u =>
                    u.type === 'error' ? `Error: ${u.message}` : u.message
                  )
                }
              }
            }
          : msg
      ));
    }
  }, [currentStreamedMessage, isProcessing, currentSessionId, processingUpdates]);

  useEffect(() => {
    if (finalAssistantMessage) {
      setMessages(prev => prev.map(msg =>
        msg.isStreaming
          ? {
              ...msg,
              content: finalAssistantMessage.content,
              isStreaming: false,
              messageDetails: {
                ...finalAssistantMessage,
                assistant_response_details: {
                  ...finalAssistantMessage.assistant_response_details,
                  naetra_thought_process: [
                    ...(msg.messageDetails?.assistant_response_details?.naetra_thought_process || []),
                    ...processingUpdates.map(u => u.message)
                  ]
                }
              }
            }
          : msg
      ));
      if (finalAssistantMessage.session_id) {
        setCurrentSessionId(finalAssistantMessage.session_id);
      }
    }
  }, [finalAssistantMessage]);

  useEffect(() => {
    if (error && processingUpdates) {
      const updatedProcessing = [...processingUpdates, { type: 'error', message: error }];
      setMessages(prev => prev.map(msg =>
        msg.isStreaming
          ? {
              ...msg,
              isStreaming: false,
              messageDetails: {
                ...msg.messageDetails,
                assistant_response_details: {
                  ...msg.messageDetails?.assistant_response_details,
                  naetra_thought_process: updatedProcessing.map(u =>
                    u.type === 'error' ? `Error: ${u.message}` : u.message
                  )
                }
              }
            }
          : msg
      ));
    }
  }, [error]);

  return (
    <Box sx={{
      display: 'flex',
      flexDirection: 'column',
      height: '100%',
      alignItems: 'center',
      width: '100%'
    }}>
      {/* Chat content */}
      <Box sx={{
        width: '65%',
        flex: 1,
        overflowY: 'auto',
        p: 2,
        pb: '100px', // Extra padding for fixed input box
        '&::-webkit-scrollbar': {
          width: '8px',
        },
        '&::-webkit-scrollbar-thumb': {
          backgroundColor: 'rgba(0,0,0,0.2)',
          borderRadius: '4px',
        }
      }}>
        {messages.map((message) => (
          <ChatMessage
            key={message.id}
            role={message.role}
            content={message.content}
            isProcessing={message.isStreaming}
            processingUpdates={message.isStreaming ? processingUpdates : undefined}
            messageDetails={message.messageDetails}
            timestamp={message.timestamp}
          />
        ))}
        <div ref={messagesEndRef} />
      </Box>

      {/* Input box floating bottom like ChatGPT */}
      <Box
        sx={{
          position: 'fixed',
          bottom: 0,
          left: 0,
          right: 0,
          zIndex: theme.zIndex.appBar,
          backgroundColor: alpha(theme.palette.background.default, 0.8),
          backdropFilter: 'blur(8px)',
          borderTop: `1px solid ${theme.palette.divider}`,
          py: 2
        }}
      >
        <Container maxWidth="md" sx={{ px: { xs: 2, md: 3 }, width: '65%' }}>
        <Paper
          elevation={3}
          sx={{
            maxWidth: '768px',
            mx: 'auto',
            display: 'flex',
            alignItems: 'flex-end',
            px: 2,
            py: 1,
            borderRadius: '24px',
            backgroundColor: theme.palette.background.paper
          }}
        >
          <TextareaAutosize
            minRows={1}
            maxRows={8}
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyPress}
            placeholder="Send a message..."
            style={{
              resize: 'none',
              width: '100%',
              border: 'none',
              outline: 'none',
              fontSize: '16px',
              padding: '8px 0',
              backgroundColor: 'transparent',
              color: theme.palette.text.primary,
              fontFamily: 'inherit'
            }}
            disabled={isProcessing}
          />
          {isProcessing ? (
            <IconButton
              onClick={handleStopMessage}
              color="primary"
              sx={{ ml: 1 }}
            >
              <StopIcon />
            </IconButton>
          ) : (
            <IconButton
              onClick={handleSendMessage}
              disabled={!inputValue.trim()}
              color="primary"
              sx={{ ml: 1 }}
            >
              <SendIcon />
            </IconButton>
          )}
        </Paper>
        </Container>
      </Box>
    </Box>
  );
};

export default ChatPage;
