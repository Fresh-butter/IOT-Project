import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Card, 
  CardActionArea,
  CardContent, 
  Typography, 
  Chip, 
  CircularProgress, 
  Alert,
  Grid,
  Paper,
  Divider
} from '@mui/material';
import { fetchRoutes, Route } from '../services/api';
import RouteMap from './RouteMap';

const RoutesList: React.FC = () => {
  const [routes, setRoutes] = useState<Route[]>([]);
  const [selectedRoute, setSelectedRoute] = useState<Route | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadRoutes = async () => {
      try {
        setLoading(true);
        const data = await fetchRoutes();
        setRoutes(data);
        setError(null);
      } catch (err: any) {
        setError(err.message || 'Failed to fetch routes');
      } finally {
        setLoading(false);
      }
    };

    loadRoutes();
  }, []);

  const handleRouteClick = (route: Route) => {
    setSelectedRoute(route);
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ my: 2 }}>
        {error}
      </Alert>
    );
  }

  return (
    <Box sx={{ py: 2 }}>
      <Grid container spacing={3}>
        {/* Left column: Routes list */}
        <Grid item xs={12} md={5}>
          <Typography variant="h5" component="h2" gutterBottom>
            Available Routes
          </Typography>
          
          <Box sx={{ maxHeight: 'calc(100vh - 220px)', overflowY: 'auto', pr: 1 }}>
            {routes.length === 0 ? (
              <Alert severity="info">No routes available</Alert>
            ) : (
              routes.map((route) => (
                <Card 
                  key={route._id}
                  sx={{ 
                    mb: 2, 
                    border: selectedRoute?._id === route._id ? '2px solid #1976d2' : '1px solid #e0e0e0',
                    transition: 'all 0.2s',
                    '&:hover': {
                      boxShadow: 3
                    }
                  }}
                >
                  <CardActionArea onClick={() => handleRouteClick(route)}>
                    <CardContent>
                      <Typography variant="h6">{route.route_name}</Typography>
                      <Typography color="text.secondary" gutterBottom>ID: {route.route_id}</Typography>
                      
                      <Box sx={{ mt: 1, display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                        <Chip 
                          label={`${route.checkpoints.length} checkpoints`}
                          size="small"
                          sx={{ mr: 1 }}
                        />
                        
                        {route.assigned_train_id && (
                          <Chip 
                            label={`Train: ${route.assigned_train_id}`}
                            color="primary"
                            size="small"
                          />
                        )}
                      </Box>
                      
                      {route.start_time && (
                        <Typography variant="body2" sx={{ mt: 1 }}>
                          Starts: {new Date(route.start_time).toLocaleString()}
                        </Typography>
                      )}
                    </CardContent>
                  </CardActionArea>
                </Card>
              ))
            )}
          </Box>
        </Grid>
        
        {/* Right column: Map and details */}
        <Grid item xs={12} md={7}>
          <Typography variant="h5" component="h2" gutterBottom>
            Route Map
          </Typography>
          
          <RouteMap selectedRoute={selectedRoute} />
          
          {selectedRoute && (
            <Paper elevation={2} sx={{ mt: 2, p: 2 }}>
              <Typography variant="h6" gutterBottom>Route Details</Typography>
              
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <Typography variant="body2">
                    <strong>Name:</strong> {selectedRoute.route_name}
                  </Typography>
                  <Typography variant="body2">
                    <strong>ID:</strong> {selectedRoute.route_id}
                  </Typography>
                  {selectedRoute.assigned_train_id && (
                    <Typography variant="body2">
                      <strong>Assigned Train:</strong> {selectedRoute.assigned_train_id}
                    </Typography>
                  )}
                </Grid>
                
                <Grid item xs={12} sm={6}>
                  {selectedRoute.start_time && (
                    <Typography variant="body2">
                      <strong>Start Time:</strong> {new Date(selectedRoute.start_time).toLocaleString()}
                    </Typography>
                  )}
                  <Typography variant="body2">
                    <strong>Checkpoints:</strong> {selectedRoute.checkpoints.length}
                  </Typography>
                </Grid>
                
                <Grid item xs={12}>
                  <Divider sx={{ my: 1 }} />
                  <Typography variant="subtitle2">Checkpoint Names:</Typography>
                  <Box sx={{ mt: 1 }}>
                    {selectedRoute.checkpoints.map((checkpoint, index) => (
                      <Chip 
                        key={index}
                        label={checkpoint.name || `Checkpoint ${index + 1}`}
                        size="small"
                        sx={{ mr: 1, mb: 1 }}
                      />
                    ))}
                  </Box>
                </Grid>
              </Grid>
            </Paper>
          )}
        </Grid>
      </Grid>
    </Box>
  );
};

export default RoutesList;