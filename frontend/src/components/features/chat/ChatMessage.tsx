import React from 'react';
import { Box, Paper, Typography, Avatar, useTheme } from '@mui/material';
import { alpha } from '@mui/material/styles';
import PersonIcon from '@mui/icons-material/Person';
import AssistantIcon from '@mui/icons-material/Assistant';
import MarkdownContent from '../../common/MarkdownContent';
import { MessageRole, ChatMessageResponseData } from '../../../utils/api';
import { ProcessingUpdate } from '../../../hooks/useStreamChat';

interface ChatMessageProps {
  role: MessageRole;
  content: string;
  timestamp?: string;
  isProcessing?: boolean;
  processingUpdates?: ProcessingUpdate[];
  messageDetails?: ChatMessageResponseData;
}

const ChatMessage: React.FC<ChatMessageProps> = ({
  role,
  content,
  timestamp,
  isProcessing,
  processingUpdates,
  messageDetails,
}) => {
  const theme = useTheme();
  const isUser = role === MessageRole.USER;

  return (
    <Box sx={{ display: 'flex', justifyContent: isUser ? 'flex-end' : 'flex-start', mb: 2 }}>
      <Paper
        elevation={1}
        sx={{
          p: 2,
          backgroundColor: isUser ? theme.palette.primary.light : theme.palette.background.paper,
          color: isUser ? theme.palette.primary.contrastText : theme.palette.text.primary,
          width: '100%',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        {/* Header */}
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <Avatar
            sx={{ 
              width: 30, 
              height: 30, 
              mr: 1, 
              bgcolor: isUser ? theme.palette.primary.main : theme.palette.secondary.main 
            }}
          >
            {isUser ? <PersonIcon fontSize="small" /> : <AssistantIcon fontSize="small" />}
          </Avatar>
          <Typography variant="caption" sx={{ fontWeight: 'bold' }}>
            {isUser ? 'You' : 'CHAETRA'}
          </Typography>
        </Box>

        {/* Assistant messages show thought process first */}
        {!isUser && (
          <>
            {/* Thought Process */}
            {(isProcessing || (messageDetails?.assistant_response_details?.naetra_thought_process || []).length > 0) && (
              <Box
                sx={{
                  mb: 3,
                  p: 1.5,
                  borderRadius: 1,
                  backgroundColor: alpha(theme.palette.background.default, 0.5),
                  fontFamily: 'monospace',
                  fontSize: '0.875rem',
                  lineHeight: 1.5,
                  color: theme.palette.text.secondary
                }}
              >
                <Typography variant="caption" sx={{ display: 'block', mb: 1, color: theme.palette.text.disabled }}>
                  Thought Process:
                </Typography>

                {(isProcessing ? processingUpdates : messageDetails?.assistant_response_details?.naetra_thought_process)?.map((item, index) => {
                  // Handle both ProcessingUpdate objects and thought process strings
                  const update = typeof item === 'string'
                    ? { type: 'info', message: item }
                    : item;
                  return (
                    <Box
                      key={index}
                      sx={{
                        display: 'flex',
                        alignItems: 'flex-start',
                        mb: 0.5,
                      }}
                    >
                      <Box sx={{ mr: 1, color: theme.palette.text.disabled }}>•</Box>
                      <Box>{update.message}</Box>
                    </Box>
                  );
                })}

                {/* Show processing indicator only during active processing */}
                {isProcessing && !processingUpdates?.some(update => update.message.startsWith('Error:')) && (
                  <Box
                    component="span"
                    sx={{
                      display: 'inline-block',
                      width: '0.5em',
                      height: '1.2em',
                      backgroundColor: theme.palette.primary.main,
                      animation: 'blink 1s step-end infinite',
                      ml: 2,
                      '@keyframes blink': {
                        '50%': { opacity: 0 }
                      }
                    }}
                  />
                )}
              </Box>
            )}

            {/* Main content when available */}
            {content && (
              <Box
                sx={{
                  p: 1.5,
                  borderRadius: 1,
                  backgroundColor: theme.palette.background.paper,
                  boxShadow: theme.shadows[1]
                }}
              >
                <MarkdownContent content={content} />
              </Box>
            )}
          </>
        )}

        {/* User messages only show content */}
        {isUser && (
          <Box sx={{ mb: 1 }}>
            <MarkdownContent content={content} />
          </Box>
        )}

        {/* Timestamp */}
        {timestamp && (
          <Typography
            variant="caption"
            sx={{
              alignSelf: 'flex-end',
              mt: 1,
              color: isUser ? theme.palette.primary.contrastText : theme.palette.text.disabled,
              opacity: 0.7,
            }}
          >
            {new Date(timestamp).toLocaleTimeString()}
          </Typography>
        )}
      </Paper>
    </Box>
  );
};

export default ChatMessage;
