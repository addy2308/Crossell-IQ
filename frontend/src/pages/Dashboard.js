import React from 'react';
import { useQuery } from 'react-query';
import {
  Grid, Paper, Typography, Box, Card, CardContent,
  Skeleton
} from '@mui/material';
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell
} from 'recharts';
import { dashboardAPI } from '../services/api';

const COLORS = ['#00e5ff', '#ff4081', '#ffd700', '#00ff7f'];

const Dashboard = () => {
  const { data: kpis, isLoading: kpisLoading } = useQuery('kpis', dashboardAPI.getKPIs);
  const { data: revenueTrend, isLoading: trendLoading } = useQuery(
    'revenueTrend', 
    () => dashboardAPI.getRevenueTrend('weekly', 12)
  );
  const { data: segments, isLoading: segLoading } = useQuery(
    'segments', 
    dashboardAPI.getSegmentDistribution
  );

  if (kpisLoading) {
    return (
      <Box>
        <Skeleton variant="text" width={400} height={60} />
        <Grid container spacing={3}>
          {[1,2,3,4].map(i => (
            <Grid item xs={12} sm={6} md={3} key={i}>
              <Skeleton variant="rectangular" height={120} />
            </Grid>
          ))}
        </Grid>
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom sx={{ color: '#00e5ff' }}>
        📊 Management KPI Dashboard
      </Typography>

      {/* KPI Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {[
          { label: 'Total Customers', value: kpis?.total_customers || 0, color: '#00e5ff' },
          { label: 'Prediction Coverage', value: `${kpis?.coverage_rate || 0}%`, color: '#ff4081' },
          { label: 'Avg Propensity', value: `${kpis?.average_propensity_score || 0}%`, color: '#ffd700' },
          { label: 'Conversion Rate', value: `${kpis?.conversion_rate || 0}%`, color: '#00ff7f' },
        ].map((kpi, idx) => (
          <Grid item xs={12} sm={6} md={3} key={idx}>
            <Card sx={{ bgcolor: '#1a1f2e', border: `1px solid ${kpi.color}22` }}>
              <CardContent>
                <Typography variant="h3" sx={{ color: kpi.color, fontWeight: 700 }}>
                  {kpi.value}
                </Typography>
                <Typography variant="body2" sx={{ color: '#888' }}>
                  {kpi.label}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Charts Row */}
      <Grid container spacing={3}>
        {/* Revenue Trend */}
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 3, bgcolor: '#1a1f2e' }}>
            <Typography variant="h6" gutterBottom sx={{ color: '#00e5ff' }}>
              Weekly Revenue Trend
            </Typography>
            {trendLoading ? (
              <Skeleton variant="rectangular" height={300} />
            ) : (
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={revenueTrend}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#ffffff11" />
                  <XAxis dataKey="date" stroke="#ffffff66" fontSize={12} />
                  <YAxis stroke="#ffffff66" fontSize={12} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#1a1f2e', border: '1px solid #00e5ff44' }}
                  />
                  <Legend />
                  <Line 
                    type="monotone" 
                    dataKey="baseline" 
                    stroke="#ff4081" 
                    strokeWidth={2}
                    name="Baseline Revenue" 
                    dot={false}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="nba" 
                    stroke="#00e5ff" 
                    strokeWidth={3}
                    name="NBA Engine Revenue" 
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            )}
          </Paper>
        </Grid>

        {/* Segment Distribution */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 3, bgcolor: '#1a1f2e' }}>
            <Typography variant="h6" gutterBottom sx={{ color: '#00e5ff' }}>
              Customer Segments
            </Typography>
            {segLoading ? (
              <Skeleton variant="circular" width={200} height={200} sx={{ mx: 'auto' }} />
            ) : (
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={segments}
                    cx="50%"
                    cy="50%"
                    innerRadius={50}
                    outerRadius={90}
                    paddingAngle={5}
                    dataKey="value"
                    nameKey="name"
                  >
                    {segments?.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#1a1f2e', border: '1px solid #00e5ff44' }}
                  />
                </PieChart>
              </ResponsiveContainer>
            )}
            {/* Legend */}
            <Box sx={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'center', gap: 1, mt: 1 }}>
              {segments?.map((seg, idx) => (
                <Box key={idx} sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                  <Box sx={{ width: 12, height: 12, borderRadius: '50%', bgcolor: COLORS[idx] }} />
                  <Typography variant="caption">{seg.name}</Typography>
                </Box>
              ))}
            </Box>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;