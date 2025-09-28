import React, { useEffect, useRef } from "react";
import { Box, Typography, Paper, Avatar, Stack } from "@mui/material";
import useWebSocket from "../hooks/useWebSocket";
import PersonIcon from "@mui/icons-material/Person";
import SupportAgentIcon from "@mui/icons-material/SupportAgent";
import ShoppingCartIcon from "@mui/icons-material/ShoppingCart";
import DirectionsCarIcon from "@mui/icons-material/DirectionsCar";
import RestaurantIcon from "@mui/icons-material/Restaurant";
import HelpOutlineIcon from "@mui/icons-material/HelpOutline";

const WS_URL = "ws://localhost:8003/ws/chat";

function getMessageType(msg) {
  if (!msg._topic) return "system";
  if (msg._topic === "transcript") return "user";
  if (msg._topic === "agent.cmd" && msg.tool === "clarify") return "clarify";
  if (msg._topic === "agent.out.ride") return "ride";
  if (msg._topic === "agent.out.food") return "food";
  if (msg._topic === "agent.out.mart") return "mart";
  if (msg._topic === "agent.out.clarify") return "clarify";
  return "system";
}

function getIcon(type) {
  switch (type) {
    case "user": return <PersonIcon color="primary" />;
    case "ride": return <DirectionsCarIcon color="success" />;
    case "food": return <RestaurantIcon color="warning" />;
    case "mart": return <ShoppingCartIcon color="info" />;
    case "clarify": return <HelpOutlineIcon color="secondary" />;
    default: return <SupportAgentIcon color="action" />;
  }
}

const ChatWindow = () => {
  const { messages, connectionStatus } = useWebSocket(WS_URL);
  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  return (
    <Box ref={scrollRef} sx={{ flex: 1, p: 2, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 2 }}>
      {messages.length === 0 && (
        <Typography variant="body2" color="text.secondary" align="center" sx={{ mt: 4 }}>
          Start chatting to see your conversation here.
        </Typography>
      )}
      {messages.map((msg, idx) => {
        const type = getMessageType(msg);
        const isUser = type === "user";
        console.log(msg);
        return (
          <Stack key={idx} direction={isUser ? "row-reverse" : "row"} alignItems="flex-end" spacing={1}>
            <Avatar sx={{ bgcolor: isUser ? 'primary.main' : 'grey.200', color: isUser ? 'white' : 'text.primary', width: 32, height: 32 }}>
              {getIcon(type)}
            </Avatar>
            <Paper
              elevation={2}
              sx={{
                p: 1.5,
                bgcolor: isUser ? 'primary.main' : (type === 'clarify' ? 'secondary.light' : 'background.paper'),
                color: isUser ? 'white' : 'text.primary',
                borderRadius: 3,
                maxWidth: '70%',
                minWidth: 60,
                wordBreak: 'break-word',
              }}
            >
              <Typography variant="body1">
                {msg.text || msg.question || msg.suggestion || msg.service || msg._topic}
              </Typography>
              {msg._topic && (
                <Typography variant="caption" color="text.secondary">
                  {msg._topic.replace("agent.out.", "").replace("transcript", "user").replace("agent.cmd", "clarify")}
                </Typography>
              )}
            </Paper>
          </Stack>
        );
      })}
      <Box sx={{ height: 16 }} />
      <Typography variant="caption" color="text.secondary" align="center">
        Connection: {connectionStatus}
      </Typography>
    </Box>
  );
};

export default ChatWindow; 