import React from "react";
import { Box, TextField, IconButton, Paper } from "@mui/material";
import SendIcon from "@mui/icons-material/Send";

const ChatInput = () => {
  return (
    <Paper elevation={2} sx={{ p: 1, display: 'flex', alignItems: 'center', borderRadius: 3 }}>
      <TextField
        fullWidth
        placeholder="Type your message..."
        variant="standard"
        InputProps={{ disableUnderline: true }}
        sx={{ mx: 1 }}
      />
      <IconButton color="primary">
        <SendIcon />
      </IconButton>
    </Paper>
  );
};

export default ChatInput; 