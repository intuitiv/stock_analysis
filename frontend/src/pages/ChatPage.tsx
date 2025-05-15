import React, { useState, useRef, useEffect } from 'react';
import { 
  Box, 
  Container, 
  TextField, 
  IconButton, 
  Paper, 
  Typography, 
  CircularProgress,
  useTheme
} from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import { useAuth } from '../contexts/AuthContext';
import { useStreamChat } from '../hooks/useStreamChat';
import ChatMessage from '../components/features/chat/ChatMessage';
import { MessageRole } from '../utils/api';
import { config } from '../config';

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
  
  // Initialize streaming chat hook
  const {
    processingUpdates,
    currentStreamedMessage,
    finalAssistantMessage,
    error,
    isProcessing,
    sendMessage,
    closeStream
  } = useStreamChat(config.apiBaseUrl, getToken);

  // Scroll to bottom whenever messages change
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, currentStreamedMessage]);

  // Handle sending a new message
  const handleSendMessage = async () => {
    if (!inputValue.trim()) return;

    const messageId = Date.now().toString();
    const timestamp = new Date().toISOString();

    // Add user message
    const newUserMessage: ChatMessage = {
      id: `user-${messageId}`,
      role: MessageRole.USER,
      content: inputValue,
      timestamp
    };

    // Add assistant message placeholder for streaming
    const streamingMessage: ChatMessage = {
      id: `assistant-${messageId}`,
      role: MessageRole.ASSISTANT,
      content: '',
      timestamp,
      isStreaming: true
    };

    setMessages(prev => [...prev, newUserMessage, streamingMessage]);
    setInputValue(''); // Clear input

    try {
      await sendMessage(inputValue, currentSessionId);
    } catch (err) {
      console.error('Failed to send message:', err);
      // Update streaming message to show error
      setMessages(prev => prev.map(msg =>
        msg.id === `assistant-${messageId}`
          ? { ...msg, content: 'Failed to send message. Please try again.', isStreaming: false }
          : msg
      ));
    }
  };

  // Handle key press (Enter to send)
  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSendMessage();
    }
  };

  // Effect to update streaming message content and preserve processing updates
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

  // Effect to finalize assistant message
  useEffect(() => {
    if (finalAssistantMessage) {
      setMessages(prev => prev.map(msg =>
        msg.isStreaming
          ? {
              ...msg,
              content: finalAssistantMessage.content,
              messageDetails: {
                ...finalAssistantMessage,
                assistant_response_details: {
                  ...finalAssistantMessage.assistant_response_details,
                  naetra_thought_process: [
                    ...(msg.messageDetails?.assistant_response_details?.naetra_thought_process || []),
                    ...processingUpdates.map(u => u.message)
                  ]
                }
              },
              isStreaming: false
            }
          : msg
      ));
      
      if (finalAssistantMessage.session_id) {
        setCurrentSessionId(finalAssistantMessage.session_id);
      }
    }
  }, [finalAssistantMessage]);

  // Effect to handle errors
  useEffect(() => {
    if (error && processingUpdates) {
      console.error('Stream error:', error);
      // Create a new processing updates array that preserves existing updates
      const updatedProcessing = [
        ...processingUpdates,
        { type: 'error', message: error }
      ];
      
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
    <Container maxWidth="md" sx={{ height: '100vh', py: 2 }}>
      <Paper 
        elevation={3}
        sx={{
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
          backgroundColor: theme.palette.background.paper
        }}
      >
        {/* Chat header */}
        <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
          <Typography variant="h6">Chat with CHAETRA</Typography>
        </Box>

        {/* Messages area */}
        <Box
          sx={{
            flex: 1,
            overflow: 'auto',
            p: 2,
            display: 'flex',
            flexDirection: 'column',
            gap: 2
          }}
        >
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

        {/* Input area */}
        <Box sx={{ p: 2, borderTop: 1, borderColor: 'divider', bgcolor: 'background.default' }}>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <TextField
              fullWidth
              multiline
              maxRows={4}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Type your message..."
              disabled={isProcessing}
              sx={{
                '& .MuiOutlinedInput-root': {
                  borderRadius: theme.shape.borderRadius,
                  bgcolor: 'background.paper'
                }
              }}
            />
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              <IconButton
                onClick={handleSendMessage}
                disabled={!inputValue.trim() || isProcessing}
                color="primary"
                sx={{ alignSelf: 'flex-end' }}
              >
                {isProcessing ? <CircularProgress size={24} /> : <SendIcon />}
              </IconButton>
              
              {/* Stop generation button */}
              {isProcessing && (
                <IconButton
                  onClick={() => {
                    const updatedProcessing = [
                      ...processingUpdates,
                      { type: 'info', message: '[Generation stopped by user]' }
                    ];
                    
                    closeStream();
                    setMessages(prev => prev.map(msg =>
                      msg.isStreaming
                        ? {
                            ...msg,
                            content: msg.content + ' [stopped]',
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
                  }}
                  color="error"
                  size="small"
                  sx={{
                    alignSelf: 'flex-end',
                    minWidth: 40,
                    height: 40
                  }}
                >
                  <Box
                    sx={{
                      width: 12,
                      height: 12,
                      bgcolor: 'error.main',
                      borderRadius: 0.5
                    }}
                  />
                </IconButton>
              )}
            </Box>
          </Box>
        </Box>
      </Paper>
    </Container>
  );
};

export default ChatPage;
