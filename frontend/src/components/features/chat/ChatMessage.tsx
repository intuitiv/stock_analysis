import React from 'react';
import { Box, Paper, Typography, useTheme } from '@mui/material';
import { alpha } from '@mui/material/styles';
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
    <Box
      sx={{
        display: 'flex',
        justifyContent: isUser ? 'flex-end' : 'flex-start',
        mt: 3,
      }}
    >
      {isUser ? (
        // USER MESSAGE
        <Paper
          elevation={1}
          sx={{
            p: 2,
            maxWidth: '80%',
            borderRadius: 3,
            backgroundColor: theme.palette.grey[800],
            color: theme.palette.common.white,
          }}
        >
          <Box sx={{ textAlign: 'right' }}>
            <Typography
              variant="body1"
              sx={{
                whiteSpace: 'pre-wrap',
                wordBreak: 'break-word',
              }}
            >
              {content}
            </Typography>
          </Box>
          {timestamp && (
            <Typography
              variant="caption"
              sx={{
                display: 'block',
                textAlign: 'right',
                mt: 1,
                opacity: 0.7,
                fontSize: '0.65rem',
                color: theme.palette.grey[300],
              }}
            >
              {/* {new Date(timestamp).toLocaleTimeString()} */}
            </Typography>
          )}
        </Paper>
      ) : (
        // ASSISTANT / SYSTEM MESSAGE (no Paper)
        <Box sx={{ flex: 1 }}>
          {/* Thought Process */}
          {(isProcessing || (messageDetails?.assistant_response_details?.naetra_thought_process || []).length > 0) && (
            <Box
              sx={{
                mb: 2,
                p: 1.5,
                borderRadius: 1,
                backgroundColor: alpha(theme.palette.background.default, 0.5),
                fontFamily: 'monospace',
                fontSize: '0.875rem',
                lineHeight: 1.5,
                color: theme.palette.text.secondary,
              }}
            >
              <Typography variant="caption" sx={{ display: 'block', mb: 1, color: theme.palette.text.disabled }}>
                Thought Process:
              </Typography>

              {(isProcessing ? processingUpdates : messageDetails?.assistant_response_details?.naetra_thought_process)?.map((item, index) => {
                const update = typeof item === 'string' ? { type: 'info', message: item } : item;
                return (
                  <Box key={index} sx={{ display: 'flex', alignItems: 'flex-start', mb: 0.5 }}>
                    <Box sx={{ mr: 1, color: theme.palette.text.disabled }}>•</Box>
                    <Box>{update.message}</Box>
                  </Box>
                );
              })}

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
                      '50%': { opacity: 0 },
                    },
                  }}
                />
              )}
            </Box>
          )}

          {/* Main Content */}
          {content && (
            <Box sx={{ p: 0.75 }}>
              <MarkdownContent content={content} />
            </Box>
          )}

          {/* Timestamp */}
          {timestamp && !isNaN(new Date(timestamp).getTime()) && (
            <Typography
              variant="caption"
              sx={{
                display: 'block',
                textAlign: 'left',
                mt: 1,
                color: theme.palette.text.disabled,
                opacity: 0.7,
              }}
            >
              {/*{new Date(timestamp).toLocaleTimeString()}*/}
            </Typography>
          )}
        </Box>
      )}
    </Box>
  );
};

export default ChatMessage;
