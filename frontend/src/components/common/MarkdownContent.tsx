import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';
import rehypeSanitize from 'rehype-sanitize';
import { Box, useTheme } from '@mui/material';

interface MarkdownContentProps {
  content: string;
  className?: string;
}

const MarkdownContent: React.FC<MarkdownContentProps> = ({ content, className }) => {
  const theme = useTheme();

  return (
    <Box
      className={className}
      sx={{
        '& pre': {
          backgroundColor: theme.palette.mode === 'dark' ? theme.palette.grey[900] : theme.palette.grey[100],
          padding: theme.spacing(2),
          borderRadius: theme.shape.borderRadius,
          overflowX: 'auto',
          fontFamily: 'monospace',
        },
        '& code:not(pre > code)': { // Inline code
          backgroundColor: theme.palette.mode === 'dark' ? theme.palette.grey[800] : theme.palette.grey[200],
          padding: theme.spacing(0.25, 0.5),
          borderRadius: theme.shape.borderRadius,
          fontSize: '0.875em',
          fontFamily: 'monospace',
        },
        '& pre > code': { // Code within pre blocks
          padding: 0,
          backgroundColor: 'transparent',
          fontSize: 'inherit', // Inherit from pre
        },
        '& blockquote': {
          borderLeft: `4px solid ${theme.palette.divider}`,
          margin: theme.spacing(1.5, 0),
          padding: theme.spacing(0, 2),
          color: theme.palette.text.secondary,
        },
        '& table': {
          borderCollapse: 'collapse',
          width: '100%',
          marginBottom: theme.spacing(2),
          border: `1px solid ${theme.palette.divider}`,
        },
        '& th, & td': {
          border: `1px solid ${theme.palette.divider}`,
          padding: theme.spacing(1),
          textAlign: 'left',
        },
        '& th': {
          backgroundColor: theme.palette.mode === 'dark' ? theme.palette.grey[800] : theme.palette.grey[100],
        },
        '& ul, & ol': {
          paddingLeft: theme.spacing(3),
          marginBottom: theme.spacing(1),
        },
        '& li': {
          marginBottom: theme.spacing(0.5),
        },
        '& p': {
          marginBottom: theme.spacing(1.5),
          lineHeight: 1.6,
        },
        '& h1, & h2, & h3, & h4, & h5, & h6': {
          marginTop: theme.spacing(3),
          marginBottom: theme.spacing(1.5),
          fontWeight: theme.typography.fontWeightMedium,
        },
        '& a': {
          color: theme.palette.primary.main,
          textDecoration: 'none',
          '&:hover': {
            textDecoration: 'underline',
          },
        },
        '& img': {
          maxWidth: '100%',
          height: 'auto',
          borderRadius: theme.shape.borderRadius,
        },
        '& hr': {
          borderColor: theme.palette.divider,
          margin: theme.spacing(3, 0),
        }
      }}
    >
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeRaw, rehypeSanitize]}
      >
        {content}
      </ReactMarkdown>
    </Box>
  );
};

export default MarkdownContent;
