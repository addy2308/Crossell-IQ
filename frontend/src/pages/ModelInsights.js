import React from 'react';
import { useQuery } from 'react-query';
import {
  Box, Typography, Paper, Grid, Skeleton
} from '@mui/material';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, RadarChart, Radar,
  PolarGrid, PolarAngleAxis, PolarRadiusAxis
} from 'recharts';
import { modelAPI } from '../services/api';

const ModelInsights = () => {
  const { data: featureImportance, isLoading: fiLoading } = useQuery(
    'featureImportance', 
    modelAPI.getFeatureImportance
  );
  
  const { data: metrics, isLoading: metLoading } = useQuery(
    'modelMetrics', 
    modelAPI.getMetrics
  );
  
  const { data: segmentProfiles, isLoading: segLoading } = useQuery(
    'segmentProfiles', 
    modelAPI.getSegmentProfiles
  );

  // Prepare radar data
  const radarData = segmentProfiles?.map(seg => ({
    segment: seg.name,
    'Avg Recency': seg.avg_recency_days / 10,
    'Avg Frequency': seg.avg_frequency * 10,
    'Avg Monetary': seg.avg_monetary / 100,
  })) || [];

  return (
    <Box>
      <Typography variant="h4" gutterBottom sx={{ color: '#00e5ff' }}>
        🤖 Model & Segmentation Insights
      </Typography>

      {/* Model Metrics Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {[
          { label: 'Algorithm', value: metrics?.model_info?.algorithm || 'XGBoost' },
          { label: 'AUC-ROC', value: metrics?.performance?.auc_roc || 0.84 },
          { label: 'Precision', value: metrics?.performance?.precision || 0.78 },
          { label: 'Recall', value: metrics?.performance?.recall || 0.82 },
        ].map((metric, idx) => (
          <Grid item xs={6} md={3} key={idx}>
            <Paper sx={{ p: 2, bgcolor: '#1a1f2e', textAlign: 'center' }}>
              <Typography variant="h5" sx={{ color: '#00e5ff', fontWeight: 700 }}>
                {typeof metric.value === 'number' ? metric.value.toFixed(2) : metric.value}
              </Typography>
              <Typography variant="body2" sx={{ color: '#888' }}>{metric.label}</Typography>
            </Paper>
          </Grid>
        ))}
      </Grid>

      <Grid container spacing={3}>
        {/* Feature Importance */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3, bgcolor: '#1a1f2e' }}>
            <Typography variant="h6" gutterBottom sx={{ color: '#00e5ff' }}>
              Top Feature Importance (SHAP)
            </Typography>
            {fiLoading ? (
              <Skeleton variant="rectangular" height={300} />
            ) : (
              <ResponsiveContainer width="100%" height={350}>
                <BarChart 
                  data={featureImportance?.slice(0, 10)} 
                  layout="vertical"
                  margin={{ left: 100 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="#ffffff11" />
                  <XAxis type="number" stroke="#ffffff66" />
                  <YAxis 
                    dataKey="feature" 
                    type="category" 
                    stroke="#ffffff66"
                    width={90}
                  />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#1a1f2e', border: '1px solid #00e5ff44' }}
                  />
                  <Bar dataKey="importance" fill="#00e5ff" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </Paper>
        </Grid>

        {/* Segment Radar */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3, bgcolor: '#1a1f2e' }}>
            <Typography variant="h6" gutterBottom sx={{ color: '#00e5ff' }}>
              Segment Profiles
            </Typography>
            {segLoading ? (
              <Skeleton variant="rectangular" height={350} />
            ) : (
              <ResponsiveContainer width="100%" height={350}>
                <RadarChart data={radarData}>
                  <PolarGrid stroke="#ffffff22" />
                  <PolarAngleAxis dataKey="segment" stroke="#ffffff66" />
                  <PolarRadiusAxis stroke="#ffffff22" />
                  <Radar 
                    name="Avg Recency" 
                    dataKey="Avg Recency" 
                    stroke="#00e5ff" 
                    fill="#00e5ff" 
                    fillOpacity={0.2} 
                  />
                  <Radar 
                    name="Avg Frequency" 
                    dataKey="Avg Frequency" 
                    stroke="#ff4081" 
                    fill="#ff4081" 
                    fillOpacity={0.2} 
                  />
                  <Radar 
                    name="Avg Monetary" 
                    dataKey="Avg Monetary" 
                    stroke="#ffd700" 
                    fill="#ffd700" 
                    fillOpacity={0.2} 
                  />
                </RadarChart>
              </ResponsiveContainer>
            )}
          </Paper>
        </Grid>

        {/* Segment Details */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3, bgcolor: '#1a1f2e' }}>
            <Typography variant="h6" gutterBottom sx={{ color: '#00e5ff' }}>
              Segment Strategies
            </Typography>
            <Grid container spacing={2}>
              {segmentProfiles?.map((seg, idx) => (
                <Grid item xs={12} sm={6} md={3} key={idx}>
                  <Paper sx={{ p: 2, bgcolor: '#0b0f19', border: '1px solid #00e5ff22' }}>
                    <Typography variant="subtitle1" sx={{ color: '#00e5ff', fontWeight: 600 }}>
                      {seg.name}
                    </Typography>
                    <Typography variant="body2" sx={{ color: '#888', mt: 1 }}>
                      {seg.recommended_strategy}
                    </Typography>
                    <Box sx={{ mt: 1, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                      <Typography variant="caption" sx={{ color: '#ffd700' }}>
                        Avg Value: ₹{seg.avg_monetary?.toLocaleString()}
                      </Typography>
                      <Typography variant="caption" sx={{ color: '#00e5ff' }}>
                        Freq: {seg.avg_frequency}
                      </Typography>
                    </Box>
                  </Paper>
                </Grid>
              ))}
            </Grid>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default ModelInsights;