import React from "react";
import { Box, AppBar, Toolbar, Typography, Paper, Container, CssBaseline, ThemeProvider, createTheme } from "@mui/material";
import ChatWindow from "./components/ChatWindow";
import ChatInput from "./components/ChatInput";

const darkTheme = createTheme({
  palette: {
    mode: 'dark',
    primary: { main: '#1976d2' },
    background: { default: '#181a20', paper: '#23272f' },
  },
  typography: {
    fontFamily: 'Inter, Roboto, Arial, sans-serif',
    fontSize: 15,
  },
});

function App() {
  return (
    <ThemeProvider theme={darkTheme}>
      <CssBaseline />
      <Box sx={{ bgcolor: 'background.default', minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
        <Container maxWidth="sm" sx={{ py: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '90vh' }}>
          <AppBar
            position="static"
            elevation={1}
            sx={{
              borderRadius: 3,
              mb: 2,
              width: '100%',
              bgcolor: '#b2f2bb', // light pastel green
              color: '#23472b',   // dark green for text for contrast
            }}
          >
            <Toolbar>
              <Typography
                variant="h6"
                sx={{
                  fontWeight: 700,
                  letterSpacing: 1,
                  fontFamily: '"Roboto Slab", "Roboto", "Arial", "sans-serif"',
                  color: 'inherit'
                }}
              >
                Agent communications interface.
              </Typography>
            </Toolbar>
          </AppBar>
          <AppBar position="static" color="primary" elevation={1} sx={{ borderRadius: 3, mb: 2, width: '100%' }}>
            <Toolbar>
              <Typography variant="h8" sx={{ fontWeight: 500, letterSpacing: 1, fontFamily: '"Roboto Slab", "Roboto", "Arial", "sans-serif"' }}>
                This chatbox can be used to communicate with the agentic system to perform your desired actions.
              </Typography>
            </Toolbar>
          </AppBar>
          <Paper elevation={3} sx={{ flex: 1, display: 'flex', flexDirection: 'column', borderRadius: 3, overflow: 'hidden', width: '100%', minHeight: 500, maxHeight: 700, mb: 2, bgcolor: 'background.paper' }}>
            <ChatWindow />
          </Paper>
          <Box sx={{ width: '100%' }}>
            <ChatInput />
          </Box>
        </Container>
      </Box>
    </ThemeProvider>
  );
}

export default App;
