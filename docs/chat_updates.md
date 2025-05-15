# Chat Processing Updates Implementation

## Overview
To improve visibility of processing updates in the chat interface, we will implement a combined approach showing both current status and history.

## Implementation Details

### 1. ChatMessage Component Updates
```typescript
// Display current processing update with loading indicator
{isProcessing && (
  <Box sx={{ mt: 1, display: 'flex', alignItems: 'center', gap: 1 }}>
    <CircularProgress size={16} color="primary" />
    <Typography variant="caption" sx={{ fontStyle: 'italic' }}>
      {processingUpdates && processingUpdates.length > 0 
        ? processingUpdates[processingUpdates.length - 1].message 
        : 'Processing...'}
    </Typography>
  </Box>
)}

// Display previous updates as chips
{isProcessing && processingUpdates && processingUpdates.length > 1 && (
  <Box sx={{ mt: 1, borderTop: `1px dashed`, pt: 1 }}>
    <Typography variant="caption" sx={{ fontWeight: 'bold', mb: 0.5 }}>
      Updates:
    </Typography>
    {processingUpdates.slice(0, -1).map((update, index) => (
      <Chip 
        key={index}
        label={`${update.type}: ${update.message}`}
        size="small"
        variant="outlined"
        color={update.type === 'error' ? 'error' : 'default'}
      />
    ))}
  </Box>
)}
```

### 2. ChatPage Updates
```typescript
// In the streaming message section
<ChatMessage
  role={MessageRole.ASSISTANT}
  content={currentStreamedMessage || ''}
  isProcessing={true}
  processingUpdates={processingUpdates}
  messageDetails={{
    role: MessageRole.ASSISTANT,
    content: currentStreamedMessage,
    timestamp: new Date().toISOString(),
    session_id: currentSessionId,
    assistant_response_details: {
      naetra_thought_process: processingUpdates.map(u => `${u.type}: ${u.message}`)
    }
  }}
/>
```

## Expected Behavior
1. Current processing update shown with loading spinner
2. Previous updates displayed as chips below
3. Error messages highlighted in red
4. All updates preserved in thought process section after completion

## Implementation Steps
1. Switch to Code mode
2. Update ChatMessage.tsx with new display logic
3. Verify changes in ChatPage.tsx
4. Test with different types of updates (processing, intent, error)