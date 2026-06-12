import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import {
  Box, Typography, Paper, Table, TableBody, TableCell,
  TableContainer, TableHead, TableRow, Chip, Button,
  Dialog, DialogTitle, DialogContent, DialogActions,
  TextField, Select, MenuItem, FormControl, InputLabel,
  Skeleton, Alert
} from '@mui/material';
import toast from 'react-hot-toast';
import { predictionAPI, agentAPI } from '../services/api';
import { useAuth } from '../context/AuthContext';

const urgencyColors = {
  high: '#ff4081',
  medium: '#ffd700',
  low: '#00e5ff',
};

const AgentView = () => {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [selectedCustomer, setSelectedCustomer] = useState(null);
  const [feedbackOpen, setFeedbackOpen] = useState(false);
  const [feedbackData, setFeedbackData] = useState({
    action_taken: '',
    outcome: '',
    notes: '',
  });

  const { data: queue, isLoading } = useQuery(
    ['agentQueue', user?.agent_id],
    () => predictionAPI.getAgentQueue(user?.agent_id, 20),
    { enabled: !!user?.agent_id }
  );

  const { data: performance } = useQuery(
    ['agentPerformance', user?.agent_id],
    () => agentAPI.getPerformance(user?.agent_id, 30),
    { enabled: !!user?.agent_id }
  );

  const feedbackMutation = useMutation(
    (data) => predictionAPI.submitFeedback(data),
    {
      onSuccess: () => {
        toast.success('Feedback submitted!');
        queryClient.invalidateQueries(['agentQueue']);
        setFeedbackOpen(false);
        setFeedbackData({ action_taken: '', outcome: '', notes: '' });
      },
      onError: () => toast.error('Failed to submit feedback'),
    }
  );

  const handleOpenFeedback = (customer) => {
    setSelectedCustomer(customer);
    setFeedbackOpen(true);
  };

  const handleSubmitFeedback = () => {
    if (!feedbackData.action_taken) {
      toast.error('Please select an action');
      return;
    }
    feedbackMutation.mutate({
      customer_id: selectedCustomer.customer_id,
      agent_id: user.agent_id,
      prediction_id: 1, // In production, get from prediction
      ...feedbackData,
    });
  };

  if (isLoading) {
    return (
      <Box>
        <Skeleton variant="text" width={300} height={60} />
        <Skeleton variant="rectangular" height={400} />
      </Box>
    );
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" sx={{ color: '#00e5ff' }}>
          🧑‍💼 Agent Workspace
        </Typography>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Chip 
            label={`Activation: ${performance?.activation_rate || 0}%`}
            sx={{ bgcolor: '#00e5ff22', color: '#00e5ff', borderColor: '#00e5ff44' }}
            variant="outlined"
          />
          <Chip 
            label={`Conversions: ${performance?.conversions || 0}`}
            sx={{ bgcolor: '#ff408122', color: '#ff4081', borderColor: '#ff408144' }}
            variant="outlined"
          />
        </Box>
      </Box>

      {/* Priority Queue Table */}
      <TableContainer component={Paper} sx={{ bgcolor: '#1a1f2e', mb: 3 }}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell sx={{ color: '#00e5ff', fontWeight: 600 }}>Priority</TableCell>
              <TableCell sx={{ color: '#00e5ff', fontWeight: 600 }}>Customer ID</TableCell>
              <TableCell sx={{ color: '#00e5ff', fontWeight: 600 }}>Propensity</TableCell>
              <TableCell sx={{ color: '#00e5ff', fontWeight: 600 }}>Product</TableCell>
              <TableCell sx={{ color: '#00e5ff', fontWeight: 600 }}>Channel</TableCell>
              <TableCell sx={{ color: '#00e5ff', fontWeight: 600 }}>Reasoning</TableCell>
              <TableCell sx={{ color: '#00e5ff', fontWeight: 600 }}>Action</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {queue?.map((item, idx) => (
              <TableRow 
                key={idx}
                sx={{ 
                  '&:hover': { bgcolor: '#00e5ff08' },
                  bgcolor: idx === 0 ? '#00e5ff11' : 'transparent'
                }}
              >
                <TableCell>
                  <Chip 
                    label={item.urgency.toUpperCase()}
                    size="small"
                    sx={{ 
                      bgcolor: `${urgencyColors[item.urgency]}22`,
                      color: urgencyColors[item.urgency],
                      fontWeight: 600,
                    }}
                  />
                </TableCell>
                <TableCell sx={{ color: '#fff' }}>#{item.customer_id}</TableCell>
                <TableCell>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Box sx={{ 
                      width: 60, 
                      height: 6, 
                      bgcolor: '#ffffff11', 
                      borderRadius: 3,
                      overflow: 'hidden'
                    }}>
                      <Box sx={{ 
                        width: `${item.propensity_score * 100}%`, 
                        height: '100%', 
                        bgcolor: item.propensity_score > 0.7 ? '#00ff7f' : '#00e5ff',
                        borderRadius: 3
                      }} />
                    </Box>
                    <Typography variant="body2" sx={{ color: '#fff' }}>
                      {(item.propensity_score * 100).toFixed(1)}%
                    </Typography>
                  </Box>
                </TableCell>
                <TableCell sx={{ color: '#fff' }}>{item.recommended_product}</TableCell>
                <TableCell>
                  <Chip 
                    label={item.suggested_channel}
                    size="small"
                    variant="outlined"
                    sx={{ borderColor: '#00e5ff44', color: '#00e5ff' }}
                  />
                </TableCell>
                <TableCell>
                  <Typography variant="body2" sx={{ color: '#888', maxWidth: 200 }}>
                    {item.reasoning}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Button
                    variant="contained"
                    size="small"
                    onClick={() => handleOpenFeedback(item)}
                    sx={{ 
                      background: 'linear-gradient(90deg, #00e5ff, #00b8d4)',
                      '&:hover': { background: 'linear-gradient(90deg, #00b8d4, #0095a8)' }
                    }}
                  >
                    Take Action
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Feedback Dialog */}
      <Dialog 
        open={feedbackOpen} 
        onClose={() => setFeedbackOpen(false)}
        PaperProps={{ sx: { bgcolor: '#1a1f2e', border: '1px solid #00e5ff33' } }}
      >
        <DialogTitle sx={{ color: '#00e5ff' }}>
          Submit Feedback - Customer #{selectedCustomer?.customer_id}
        </DialogTitle>
        <DialogContent>
          <FormControl fullWidth sx={{ mt: 2, mb: 2 }}>
            <InputLabel sx={{ color: '#888' }}>Action Taken</InputLabel>
            <Select
              value={feedbackData.action_taken}
              onChange={(e) => setFeedbackData({ ...feedbackData, action_taken: e.target.value })}
              sx={{ 
                color: '#fff',
                '& .MuiOutlinedInput-notchedOutline': { borderColor: '#00e5ff44' }
              }}
            >
              <MenuItem value="called_interested">Called - Interested</MenuItem>
              <MenuItem value="called_not_interested">Called - Not Interested</MenuItem>
              <MenuItem value="email_sent">Email Sent</MenuItem>
              <MenuItem value="ignored">Ignored</MenuItem>
            </Select>
          </FormControl>
          <FormControl fullWidth sx={{ mb: 2 }}>
            <InputLabel sx={{ color: '#888' }}>Outcome</InputLabel>
            <Select
              value={feedbackData.outcome}
              onChange={(e) => setFeedbackData({ ...feedbackData, outcome: e.target.value })}
              sx={{ 
                color: '#fff',
                '& .MuiOutlinedInput-notchedOutline': { borderColor: '#00e5ff44' }
              }}
            >
              <MenuItem value="converted">Converted</MenuItem>
              <MenuItem value="not_converted">Not Converted</MenuItem>
              <MenuItem value="pending">Pending</MenuItem>
            </Select>
          </FormControl>
          <TextField
            fullWidth
            label="Notes"
            multiline
            rows={3}
            value={feedbackData.notes}
            onChange={(e) => setFeedbackData({ ...feedbackData, notes: e.target.value })}
            sx={{ 
              '& .MuiOutlinedInput-root': { 
                color: '#fff',
                '& fieldset': { borderColor: '#00e5ff44' } 
              },
              '& .MuiInputLabel-root': { color: '#888' }
            }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setFeedbackOpen(false)} sx={{ color: '#888' }}>
            Cancel
          </Button>
          <Button 
            onClick={handleSubmitFeedback}
            disabled={feedbackMutation.isLoading}
            sx={{ color: '#00e5ff' }}
          >
            {feedbackMutation.isLoading ? 'Submitting...' : 'Submit'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default AgentView;