# Chat Component Scrolling Fix

## Current Issues
1. Double scrollbars appearing due to nested full-height containers
2. Improper integration between Layout and ChatPage components
3. Fixed input box potentially causing content overlap

## Component Analysis

### Layout.tsx
```tsx
// Current implementation
<Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
  <Navbar />
  <Box component="main" sx={{ flexGrow: 1, ... }}>
    {children}
  </Box>
</Box>
```
- Correctly sets up full viewport height container
- Properly handles main content area with flexGrow

### ChatPage.tsx
```tsx
// Current implementation with issues
<Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
  <Box sx={{ flex: 1, overflowY: 'auto', p: 2, pb: 10 }}>
    {/* Messages */}
  </Box>
  <Box sx={{ position: 'fixed', bottom: 0, width: '100%', ... }}>
    {/* Input */}
  </Box>
</Box>
```
- Incorrectly sets full viewport height
- Creates competing scroll container

## Proposed Changes

### ChatPage.tsx Updates
```tsx
<Box sx={{ 
  display: 'flex', 
  flexDirection: 'column',
  height: '100%',  // Use available height from Layout
  position: 'relative' // For proper fixed positioning context
}}>
  <Box sx={{ 
    flex: 1,
    overflowY: 'auto',
    p: 2,
    pb: '80px' // Match input box height
  }}>
    {/* Messages */}
  </Box>
  <Box sx={{
    position: 'absolute', // Change to absolute positioning
    bottom: 0,
    left: 0,
    right: 0,
    backgroundColor: 'background.default',
    borderTop: '1px solid',
    borderColor: 'divider',
    py: 2,
    px: { xs: 2, md: 4 }
  }}>
    {/* Input */}
  </Box>
</Box>
```

## Benefits
1. Single scrollable container
2. Proper space management for fixed input
3. Maintains responsive behavior
4. Better integration with Layout component

## Implementation Steps
1. Update ChatPage.tsx styling
2. Test scrolling behavior in different viewport sizes
3. Verify input box positioning
4. Check for any content overlap issues

## Future Considerations
- Monitor performance with large message lists
- Consider virtualization if needed
- Evaluate accessibility implications